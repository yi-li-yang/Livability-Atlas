"""Spike S5: how should a noise grid be averaged over a hex cell?

Throwaway code, never imported by `atlas`. It fetches Defra's modelled daytime road noise
(LAeq,16h, Round 4) for Greater London from its WCS service, in 10 km tiles cached in
`data/raw/noise/`, puts each 10 m pixel in the hex cell that holds it, and compares ways of
turning a cell's pixels into one number. Needs spike S1's contours, for London's cells.
Run from `pipeline/` with `uv run python notebooks/s5_noise_aggregation.py`.
"""

import json
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.features import rasterize
from rasterio.merge import merge
from s2_crime_rates import london_cells
from s3_sales_and_rents import postcodes
from scipy.stats import spearmanr
from shapely.geometry import Polygon

from atlas.paths import data_dir

WCS = "https://environment.data.gov.uk/spatialdata/road-noise-all-metrics-england-round-4/wcs"
COVERAGE = "562c9d56-7c2d-4d42-83bb-578d6e97a517__Road_Noise_LAeq16hr_England_Round_4_All"
EXTENT = (503000, 155000, 563000, 201000)  # Greater London, in British National Grid metres
TILE = 10000
FLOOR = 40.0  # the maps' cut-off: anything below counts as this
NODATA = -96.0
RAW = data_dir() / "raw" / "noise"


def fetch_tile(x: int, y: int) -> Path:
    path = RAW / f"road-laeq16-{x}-{y}.tif"
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        reply = requests.get(
            WCS,
            params={
                "service": "WCS",
                "version": "2.0.1",
                "request": "GetCoverage",
                "coverageId": COVERAGE,
                "format": "image/tiff",
                "subset": [f"E({x},{x + TILE})", f"N({y},{y + TILE})"],
            },
            timeout=300,
        )
        reply.raise_for_status()
        path.write_bytes(reply.content)
    return path


def mosaic() -> tuple[np.ndarray, rasterio.Affine]:
    paths = [
        fetch_tile(x, y)
        for x in range(EXTENT[0], EXTENT[2], TILE)
        for y in range(EXTENT[1], EXTENT[3], TILE)
    ]
    sources = [rasterio.open(p) for p in paths]
    data, transform = merge(sources, nodata=NODATA)
    for source in sources:
        source.close()
    return data[0], transform


def cell_ids(cells: list[str], shape: tuple[int, int], transform: rasterio.Affine) -> np.ndarray:
    hexes = gpd.GeoDataFrame(
        {"cell": cells},
        geometry=[Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in cells],
        crs="EPSG:4326",
    ).to_crs("EPSG:27700")
    shapes = ((geometry, i + 1) for i, geometry in enumerate(hexes.geometry))
    return rasterize(shapes, out_shape=shape, transform=transform, fill=0, dtype="int32")


def main() -> None:
    cells = london_cells()
    level, transform = mosaic()
    ids = cell_ids(cells, level.shape, transform)
    inside = ids > 0
    result: dict[str, object] = {
        "raster pixels": int(level.size),
        "pixels inside London's cells": int(inside.sum()),
    }
    values = np.where(level[inside] <= NODATA + 1, FLOOR, np.maximum(level[inside], FLOOR))
    owner = ids[inside] - 1
    result["pixels below the 40 dB cut-off, or empty"] = float((level[inside] <= FLOOR).mean())
    n = len(cells)
    count = np.bincount(owner, minlength=n)
    ok = count > 0
    arithmetic = np.bincount(owner, weights=values, minlength=n) / np.maximum(count, 1)
    energy = 10 * np.log10(
        np.bincount(owner, weights=10 ** (values / 10), minlength=n) / np.maximum(count, 1)
    )
    peak = np.full(n, FLOOR)
    np.maximum.at(peak, owner, values)
    over = {
        t: np.bincount(owner, weights=(values >= t).astype(float), minlength=n)
        / np.maximum(count, 1)
        for t in (55, 60, 65)
    }
    result["cells with pixels"] = int(ok.sum())
    result["pixels per cell, median"] = int(np.median(count[ok]))

    table = pd.DataFrame(
        {
            "arithmetic mean": arithmetic,
            "energy mean": energy,
            "highest pixel": peak,
            "share at 55 dB or more": over[55],
            "share at 65 dB or more": over[65],
        }
    )[ok]
    result["dB, quantiles"] = {
        c: table[c].quantile([0.05, 0.5, 0.95]).round(1).tolist() for c in table.columns[:3]
    }
    gap = table["energy mean"] - table["arithmetic mean"]
    result["energy mean minus arithmetic mean, dB, quantiles 5/50/95/99"] = (
        gap.quantile([0.05, 0.5, 0.95, 0.99]).round(2).tolist()
    )
    result["rank correlation of the energy mean with the arithmetic mean"] = round(
        float(spearmanr(table["energy mean"], table["arithmetic mean"])[0]), 4
    )
    result["rank correlation of the highest pixel with the arithmetic mean"] = round(
        float(spearmanr(table["highest pixel"], table["arithmetic mean"])[0]), 3
    )
    result["rank correlation of the share at 55 dB or more with the arithmetic mean"] = round(
        float(spearmanr(table["share at 55 dB or more"], table["arithmetic mean"])[0]), 3
    )

    # At addresses: the level at each postcode's point, which stands in for where homes and
    # businesses are, averaged in each cell that has any.
    codes = postcodes()
    cols, rows = ~transform * (codes["e"].to_numpy(), codes["n"].to_numpy())
    rows, cols = rows.astype(int), cols.astype(int)
    within = (rows >= 0) & (rows < level.shape[0]) & (cols >= 0) & (cols < level.shape[1])
    at = level[rows[within], cols[within]]
    at = np.where(at <= NODATA + 1, FLOOR, np.maximum(at, FLOOR))
    index = {c: i for i, c in enumerate(cells)}
    place = codes.loc[within, "cell"].map(index)
    keep = place.notna().to_numpy()
    where = place[keep].astype(int).to_numpy()
    n_codes = np.bincount(where, minlength=n)
    has = n_codes > 0
    at_mean = np.bincount(where, weights=at[keep], minlength=n) / np.maximum(n_codes, 1)
    with np.errstate(divide="ignore"):
        at_energy = 10 * np.log10(
            np.bincount(where, weights=10 ** (at[keep] / 10), minlength=n) / np.maximum(n_codes, 1)
        )
    both = has & ok
    result["cells with postcodes"] = int(has.sum())
    result["postcodes per cell with any, median"] = int(np.median(n_codes[has]))
    result["dB at postcodes: arithmetic mean quantiles 5/50/95"] = (
        np.quantile(at_mean[both], [0.05, 0.5, 0.95]).round(1).tolist()
    )
    result["dB at postcodes: energy mean quantiles 5/50/95"] = (
        np.quantile(at_energy[both], [0.05, 0.5, 0.95]).round(1).tolist()
    )
    result["area arithmetic mean minus postcode arithmetic mean, dB, median"] = round(
        float(np.median(arithmetic[both] - at_mean[both])), 2
    )
    result["area energy mean minus postcode energy mean, dB, median"] = round(
        float(np.median(energy[both] - at_energy[both])), 2
    )
    result["rank correlation, postcode arithmetic mean with area arithmetic mean"] = round(
        float(spearmanr(at_mean[both], arithmetic[both])[0]), 3
    )
    result["rank correlation, postcode arithmetic mean with area energy mean"] = round(
        float(spearmanr(at_mean[both], energy[both])[0]), 3
    )
    result["rank correlation, postcode energy mean with area energy mean"] = round(
        float(spearmanr(at_energy[both], energy[both])[0]), 3
    )
    s_at = ((70 - at_mean[both]) / 20).clip(0, 1)
    result["mean score: postcode arithmetic mean"] = round(float(s_at.mean()), 3)
    result["mean score: postcode energy mean"] = round(
        float(((70 - at_energy[both]) / 20).clip(0, 1).mean()), 3
    )

    # The benchmark: each address scored on its own, then averaged in the cell.
    each = ((70 - at[keep]) / 20).clip(0, 1)
    benchmark = np.bincount(where, weights=each, minlength=n) / np.maximum(n_codes, 1)
    for name, db in (
        ("area arithmetic mean", arithmetic),
        ("area energy mean", energy),
        ("highest pixel", peak),
        ("arithmetic mean of the levels at addresses", at_mean),
        ("energy mean of the levels at addresses", at_energy),
    ):
        guess = ((70 - db) / 20).clip(0, 1)
        result[f"against the mean of address scores: {name}"] = {
            "mean score minus benchmark": round(float((guess[both] - benchmark[both]).mean()), 3),
            "mean absolute difference": round(
                float(np.abs(guess[both] - benchmark[both]).mean()), 3
            ),
            "rank correlation": round(float(spearmanr(guess[both], benchmark[both])[0]), 3),
        }
    result["mean of address scores"] = round(float(benchmark[both].mean()), 3)

    # What each choice does to the score of the road noise curve: 1 at 50 dB and 0 at 70 dB.
    def score(db: pd.Series) -> pd.Series:
        return ((70 - db) / 20).clip(0, 1)

    s_arith, s_energy, s_peak = (
        score(table[c]) for c in ("arithmetic mean", "energy mean", "highest pixel")
    )
    result["cells scoring differently by more than 0.1: energy against arithmetic"] = round(
        float(((s_energy - s_arith).abs() > 0.1).mean()), 3
    )
    result["mean score: arithmetic, energy, highest pixel"] = [
        round(float(s.mean()), 3) for s in (s_arith, s_energy, s_peak)
    ]
    result["cells at the maximum score (50 dB or less): arithmetic, energy, highest pixel"] = [
        round(float((s >= 1).mean()), 3) for s in (s_arith, s_energy, s_peak)
    ]
    result["cells at the minimum score (70 dB or more): arithmetic, energy, highest pixel"] = [
        round(float((s <= 0).mean()), 3) for s in (s_arith, s_energy, s_peak)
    ]
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
