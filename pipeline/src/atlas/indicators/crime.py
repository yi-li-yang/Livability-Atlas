"""The crime indicators of Safety: recorded crimes per 1,000 residents, for each hex cell.

Spike S2 (docs/spikes/S2-crime.md) chose the method. Each output area's residents are shared
between the hex cells it overlaps by the area of overlap, since placing them at centroids left 38%
of the cells empty. Each cell pools itself with its neighbours within two steps, about an 8-minute
walk, and a floor of 3,000 residents at the London-wide rate pulls thin denominators towards the
average, so that a cell with a few residents and a few crimes does not top the ranking.
"""

from typing import cast

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

# The police.uk crime types that make up each of the catalogue's measured indicators.
CATEGORIES: dict[str, list[str]] = {
    "burglary": ["Burglary"],
    "violence-and-sexual-offences": ["Violence and sexual offences"],
    "robbery-and-theft-from-the-person": ["Robbery", "Theft from the person"],
    "vehicle-crime": ["Vehicle crime"],
    "anti-social-behaviour": ["Anti-social behaviour"],
}
STEPS = 2  # each cell pools the cells within this many steps of it
FLOOR = 3000  # residents added at the overall rate


def residents_by_cell(areas: gpd.GeoDataFrame, residents: pd.Series, cells: list[str]) -> pd.Series:
    """Each cell's residents: every output area's count shared by the area of overlap.

    `areas` holds output area boundaries in British National Grid in a column `OA21CD`, and
    `residents` is indexed by the same codes. An area's residents are shared by the part of the
    area that lies in each of `cells`, so those outside the cells are dropped, not given to others.
    """
    areas = cast(gpd.GeoDataFrame, areas[["OA21CD", "geometry"]].copy())
    known = residents.to_dict()
    areas["residents"] = [float(known.get(code, 0.0)) for code in areas["OA21CD"]]
    areas["area"] = areas.geometry.area
    hexes = gpd.GeoDataFrame(
        {"cell": cells},
        geometry=[Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in cells],
        crs="EPSG:4326",
    ).to_crs("EPSG:27700")
    pieces = gpd.overlay(areas, hexes, how="intersection")
    pieces["share"] = pieces["residents"] * pieces.geometry.area / pieces["area"]
    return cast(pd.Series, pieces.groupby("cell")["share"].sum())


def counts_by_cell(crimes: pd.DataFrame, cells: list[str], resolution: int) -> dict[str, pd.Series]:
    """The crimes of each indicator in each cell, from police.uk's street records.

    `crimes` has the columns `Longitude`, `Latitude` and `Crime type`. A record with no location,
    or outside `cells`, is left out.
    """
    located = crimes.dropna(subset=["Longitude", "Latitude"])
    points = located[["Longitude", "Latitude"]].drop_duplicates()
    points["cell"] = [
        h3.latlng_to_cell(lat, lng, resolution)
        for lat, lng in zip(points["Latitude"], points["Longitude"], strict=True)
    ]
    placed = located.merge(points, on=["Longitude", "Latitude"], how="left")
    placed = placed[placed["cell"].isin(list(cells))]
    return {
        indicator: cast(
            pd.Series,
            placed[placed["Crime type"].isin(kinds)]
            .groupby("cell")
            .size()
            .reindex(cells)
            .fillna(0),
        )
        for indicator, kinds in CATEGORIES.items()
    }


def rates(
    counts: pd.Series,
    residents: pd.Series,
    cells: list[str],
    steps: int = STEPS,
    floor: float = FLOOR,
) -> pd.Series:
    """Crimes per 1,000 residents, pooled over each cell and its neighbours within `steps`.

    The floor adds that many residents at the region's overall rate. Where the pooled residents
    and the floor are both 0 there is no rate.
    """
    index = {cell: i for i, cell in enumerate(cells)}
    n = counts.reindex(cells).fillna(0).to_numpy(dtype=float)
    p = residents.reindex(cells).fillna(0).to_numpy(dtype=float)
    overall = n.sum() / p.sum() if p.sum() > 0 else 0.0
    out = np.full(len(cells), np.nan)
    for cell, i in index.items():
        near = [index[c] for c in h3.grid_disk(cell, steps) if c in index]
        people = p[near].sum() + floor
        if people > 0:
            out[i] = 1000 * (n[near].sum() + floor * overall) / people
    return pd.Series(out, index=cells)
