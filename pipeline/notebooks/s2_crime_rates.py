"""Spike S2: what crime rates per hex cell do 12 months of Police.uk data give, with smoothing?

Throwaway code, never imported by `atlas`. Needs, in `data/raw/`:
- `police/2026-08.zip`, the data.police.uk archive of the latest 36 months
- `census/census2021-ts001-oa.csv`, Census 2021 residents by output area (Nomis)
- `ptal/*Contours*.TAB`, from spike S1, only for the outline of Greater London
It fetches the output areas' population-weighted centroids from the ONS once, and caches them.
Run from `pipeline/` with `uv run python notebooks/s2_crime_rates.py`.
"""

import json
import zipfile

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import pyogrio
import requests
from pyproj import Transformer
from scipy.stats import spearmanr
from shapely.geometry import Polygon
from shapely.ops import unary_union

from atlas.paths import data_dir

RESOLUTION = 9
RAW = data_dir() / "raw"
MONTHS = [
    f"{y}-{m:02d}" for y, m in [(2025, m) for m in range(9, 13)] + [(2026, m) for m in range(1, 9)]
]
FORCES = ["metropolitan", "city-of-london"]
CATEGORIES = {
    "burglary": ["Burglary"],
    "violence and sexual offences": ["Violence and sexual offences"],
    "robbery and theft from the person": ["Robbery", "Theft from the person"],
    "vehicle crime": ["Vehicle crime"],
    "anti-social behaviour": ["Anti-social behaviour"],
}
PWC = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "OA_December_2021_EW_PWC_V4/FeatureServer/0/query"
)


def london_cells() -> list[str]:
    contours = pyogrio.read_dataframe(next((RAW / "ptal").glob("*Contours*.TAB")))
    outline = unary_union(
        contours.set_crs("EPSG:27700", allow_override=True).to_crs("EPSG:4326").geometry.tolist()
    )
    polygons = [outline] if outline.geom_type == "Polygon" else list(outline.geoms)
    cells: set[str] = set()
    for polygon in polygons:
        ring = [(y, x) for x, y in polygon.exterior.coords]
        cells |= set(h3.h3shape_to_cells(h3.LatLngPoly(ring), RESOLUTION))
    return sorted(cells)


def centroids() -> pd.DataFrame:
    cache = RAW / "census" / "oa_pwc_london.csv"
    if cache.exists():
        return pd.read_csv(cache)
    rows, offset = [], 0
    while True:
        reply = requests.get(
            PWC,
            params={
                "where": "1=1",
                "geometry": "503000,155000,562000,201000",
                "geometryType": "esriGeometryEnvelope",
                "inSR": 27700,
                "outSR": 27700,
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OA21CD",
                "returnGeometry": "true",
                "resultOffset": offset,
                "resultRecordCount": 2000,
                "f": "json",
            },
            timeout=60,
        ).json()
        batch = reply["features"]
        rows += [
            {"oa": f["attributes"]["OA21CD"], "x": f["geometry"]["x"], "y": f["geometry"]["y"]}
            for f in batch
        ]
        if not batch or not reply.get("exceededTransferLimit"):
            break
        offset += len(batch)
    frame = pd.DataFrame(rows)
    frame.to_csv(cache, index=False)
    return frame


def residents_per_cell() -> pd.Series:
    pwc = centroids()
    people = pd.read_csv(RAW / "census" / "census2021-ts001-oa.csv", usecols=[2, 3])
    people.columns = ["oa", "residents"]
    merged = pwc.merge(people, on="oa", how="left")
    lng, lat = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True).transform(
        merged["x"].to_numpy(), merged["y"].to_numpy()
    )
    merged["cell"] = [h3.latlng_to_cell(a, o, RESOLUTION) for a, o in zip(lat, lng, strict=True)]
    return merged.groupby("cell")["residents"].sum()


BOUNDARIES = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Output_Areas_2021_EW_BGC_V2/FeatureServer/0/query"
)


def oa_boundaries() -> gpd.GeoDataFrame:
    """London's output area boundaries in British National Grid, fetched once from the ONS."""
    cache = RAW / "census" / "oa_boundaries_london.geojson"
    if not cache.exists():
        features, offset = [], 0
        while True:
            reply = requests.get(
                BOUNDARIES,
                params={
                    "where": "1=1",
                    "geometry": "503000,155000,562000,201000",
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": 27700,
                    "outSR": 27700,
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "OA21CD",
                    "returnGeometry": "true",
                    "resultOffset": offset,
                    "resultRecordCount": 1000,
                    "f": "geojson",
                },
                timeout=120,
            ).json()
            batch = reply["features"]
            features += batch
            if not batch or not reply.get("properties", {}).get("exceededTransferLimit"):
                break
            offset += len(batch)
        cache.write_text(
            json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
        )
    return gpd.read_file(cache).set_crs("EPSG:27700", allow_override=True)


def residents_by_area(cells: list[str]) -> pd.Series:
    """Each output area's residents, shared between the cells it overlaps by the area of overlap."""
    people = pd.read_csv(RAW / "census" / "census2021-ts001-oa.csv", usecols=[2, 3])
    people.columns = ["OA21CD", "residents"]
    areas = oa_boundaries().merge(people, on="OA21CD", how="left")
    areas["area"] = areas.geometry.area
    hexes = gpd.GeoDataFrame(
        {"cell": cells},
        geometry=[Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in cells],
        crs="EPSG:4326",
    ).to_crs("EPSG:27700")
    pieces = gpd.overlay(
        areas[["OA21CD", "residents", "area", "geometry"]], hexes, how="intersection"
    )
    pieces["share"] = pieces["residents"] * pieces.geometry.area / pieces["area"]
    return pieces.groupby("cell")["share"].sum()


def read_crimes() -> pd.DataFrame:
    frames = []
    with zipfile.ZipFile(RAW / "police" / "2026-08.zip") as archive:
        for month in MONTHS:
            for force in FORCES:
                name = f"{month}/{month}-{force}-street.csv"
                if name in archive.namelist():
                    with archive.open(name) as file:
                        frames.append(
                            pd.read_csv(
                                file, usecols=["Month", "Longitude", "Latitude", "Crime type"]
                            )
                        )
    crimes = pd.concat(frames, ignore_index=True)
    crimes["located"] = crimes["Longitude"].notna()
    return crimes


def to_cells(crimes: pd.DataFrame) -> pd.DataFrame:
    points = crimes.loc[crimes["located"], ["Longitude", "Latitude"]].drop_duplicates()
    points["cell"] = [
        h3.latlng_to_cell(a, o, RESOLUTION)
        for a, o in zip(points["Latitude"], points["Longitude"], strict=True)
    ]
    return crimes.merge(points, on=["Longitude", "Latitude"], how="left")


def smoothed_total(values: pd.Series, cells: list[str], k: int) -> pd.Series:
    """The sum of a value over each cell and its neighbours within k steps."""
    index = {c: i for i, c in enumerate(cells)}
    v = values.reindex(cells).fillna(0).to_numpy()
    return pd.Series(
        [v[[index[c] for c in h3.grid_disk(cell, k) if c in index]].sum() for cell in cells],
        index=cells,
    )


def smoothed(
    counts: pd.Series, residents: pd.Series, cells: list[str], k: int, floor: float = 0.0
) -> pd.Series:
    """Crimes per 1,000 residents, pooled over each cell and its neighbours within k steps.

    A floor adds that many residents at the overall rate, which pulls thin denominators towards
    the average.
    """
    index = {c: i for i, c in enumerate(cells)}
    n, p = counts.reindex(cells).fillna(0).to_numpy(), residents.reindex(cells).fillna(0).to_numpy()
    out = np.full(len(cells), np.nan)
    overall = n.sum() / p.sum()
    for cell, i in index.items():
        near = [index[c] for c in h3.grid_disk(cell, k) if c in index]
        if p[near].sum() + floor > 0:
            out[i] = 1000 * (n[near].sum() + floor * overall) / (p[near].sum() + floor)
    return pd.Series(out, index=cells)


def main() -> None:
    cells = london_cells()
    by_centroid = residents_per_cell()
    residents = residents_by_area(cells)
    crimes = to_cells(read_crimes())
    result: dict[str, object] = {"london cells": len(cells), "crime records": len(crimes)}
    result["share of records with no location"] = float((~crimes["located"]).mean())
    in_london = crimes["cell"].isin(set(cells))
    result["share of located records outside Greater London's cells"] = float(
        1 - in_london[crimes["located"]].mean()
    )
    result["cells with no residents when each output area sits at its centroid"] = float(
        (by_centroid.reindex(cells).fillna(0) == 0).mean()
    )
    result["residents in London's cells"] = int(residents.reindex(cells).fillna(0).sum())
    pop = residents.reindex(cells).fillna(0)
    result["cells with no residents"] = float((pop == 0).mean())
    result["cells under 50 residents"] = float((pop < 50).mean())
    result["residents per cell, quantiles"] = pop.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).to_dict()

    pooled2 = smoothed_total(residents, cells, 2)
    result["pooled residents within 2 steps, quantiles"] = (
        pooled2.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(0).to_dict()
    )
    result["cells whose pooled residents within 2 steps are under 3,000"] = float(
        (pooled2 < 3000).mean()
    )

    first = crimes["Month"].map({m: i for i, m in enumerate(MONTHS)}) % 2  # alternate months
    per_category: dict[str, object] = {}
    for name, kinds in CATEGORIES.items():
        sel = crimes[crimes["Crime type"].isin(kinds) & in_london]
        total = sel.groupby("cell").size()
        half = [sel[first.loc[sel.index] == h].groupby("cell").size() for h in (0, 1)]
        row: dict[str, object] = {"records in London's cells": int(len(sel))}
        for k in (0, 1, 2, 3):
            a, b = (smoothed(h, residents, cells, k) for h in half)
            ok = a.notna() & b.notna() & (pop > 0)
            row[f"split-half rank correlation, k={k}"] = round(float(spearmanr(a[ok], b[ok])[0]), 3)
        full = {k: smoothed(total, residents, cells, k) for k in (0, 1, 2)}
        for k in (1, 2):
            ok = full[0].notna() & full[k].notna()
            row[f"rank correlation of k={k} with the raw rate"] = round(
                float(spearmanr(full[0][ok], full[k][ok])[0]), 3
            )
        for floor in (1000, 3000, 10000):
            a, b = (smoothed(h, residents, cells, 2, floor) for h in half)
            ok = a.notna() & b.notna() & (pop > 0)
            row[f"split-half rank correlation, k=2 with a floor of {floor}"] = round(
                float(spearmanr(a[ok], b[ok])[0]), 3
            )
            held = smoothed(total, residents, cells, 2, floor)
            top = held.rank(pct=True) > 0.95
            row[f"top 5% of k=2 rates, floor {floor}: share with under 3,000 pooled residents"] = (
                round(float((pooled2[top] < 3000).mean()), 3)
            )
        chosen = smoothed(total, residents, cells, 2, 3000)
        bank = h3.latlng_to_cell(51.5133, -0.0890, RESOLUTION)  # the Bank junction, in the City
        row["the City's Bank cell: share of London's cells with a lower rate (k=2, floor 3000)"] = (
            round(float((chosen < chosen[bank]).mean()), 3)
        )
        row["the City's Bank cell: pooled residents within 2 steps"] = int(pooled2[bank])
        count = total.reindex(cells).fillna(0)
        ok = full[1].notna()
        row["rank correlation of the k=1 rate per resident with the count per cell"] = round(
            float(spearmanr(full[1][ok], count[ok])[0]), 3
        )
        smooth2 = full[2]
        hottest = smooth2.rank(pct=True) > 0.95
        row["top 5% of k=2 rates: share whose pooled residents are under 3,000"] = round(
            float((pooled2[hottest] < 3000).mean()), 3
        )
        top = full[1][ok].rank(pct=True) > 0.9
        low_count = count[ok].rank(pct=True) < 0.5
        row["top-decile cells per resident that are in the lower half by count"] = round(
            float((top & low_count).sum() / top.sum()), 3
        )
        per_category[name] = row
    result["by category"] = per_category
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
