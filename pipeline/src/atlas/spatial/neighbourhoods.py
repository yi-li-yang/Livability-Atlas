"""Which neighbourhood each hex cell is in.

A neighbourhood is an MSOA, a statistical area of 7,000 to 10,000 residents that the House of
Commons Library has named. A cell belongs to the MSOA that holds its centre, or, for a centre on the
water or just beyond a boundary, the nearest MSOA within reach.
"""

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from atlas.spatial.grid import cell_centres_bng

REACH = 750.0  # metres: how far from its centre a cell looks for an MSOA when none holds it


def neighbourhood_of(
    areas: gpd.GeoDataFrame, cells: list[str], reach: float = REACH
) -> list[str | None]:
    """The code of the MSOA each cell is in, or None where none is within `reach` metres of the
    cell's centre. `areas` has `MSOA21CD` and polygons in British National Grid."""
    centres = cell_centres_bng(cells)
    boundaries = gpd.GeoDataFrame(areas[["MSOA21CD", "geometry"]], crs=areas.crs)
    points = gpd.GeoDataFrame(
        {"position": np.arange(len(cells))},
        geometry=[Point(x, y) for x, y in centres],
        crs=areas.crs,
    )
    inside = gpd.sjoin(points, boundaries, how="left", predicate="within")
    inside = inside.drop_duplicates("position")
    found: list[str | None] = [None] * len(cells)
    for position, code in zip(inside["position"], inside["MSOA21CD"], strict=True):
        if isinstance(code, str):
            found[int(position)] = code
    missing = [i for i, code in enumerate(found) if code is None]
    if missing:
        outside = points.iloc[missing]
        near = gpd.sjoin_nearest(
            outside, boundaries, how="left", max_distance=reach
        ).drop_duplicates("position")
        for position, code in zip(near["position"], near["MSOA21CD"], strict=True):
            if isinstance(code, str):
                found[int(position)] = code
    return found


def listed(
    codes: list[str | None], names: pd.DataFrame
) -> tuple[list[tuple[str, str]], list[int | None]]:
    """The neighbourhoods that cells are in, as (name, local authority) in the order of their codes,
    and for each cell the position of its neighbourhood in that list (None where it has none).
    A code with no name is called by the code."""
    used = sorted({code for code in codes if code is not None})
    position = {code: i for i, code in enumerate(used)}
    listing = [
        (str(names.loc[code, "name"]), str(names.loc[code, "area"]))
        if code in names.index
        else (code, "")
        for code in used
    ]
    return listing, [None if code is None else position[code] for code in codes]
