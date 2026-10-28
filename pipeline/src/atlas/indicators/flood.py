"""The flood indicators of Natural hazards: the share of each hex cell with a medium or high chance
of flooding, which is 1 in 100 or more in any year.

The share is of the cell's area, read at points spread evenly over it: the centres of the 49 cells
of two resolutions finer (about 15 m apart). A point whose pixel has no class, such as an outline,
is left out; a cell with no point left has no value.
"""

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer

from atlas.datasets.countries.gb.ea_flood_risk import HIGH, MEDIUM, UNKNOWN, Mosaic

FINER = 2  # resolutions finer than the hex cells: 7 steps along a side, 49 points a cell
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def share_at_risk(mosaic: Mosaic, cells: list[str], resolution: int) -> pd.Series:
    """The percentage (0 to 100) of each cell's area in the medium or high band."""
    points: list[tuple[float, float]] = []
    owner: list[int] = []
    for index, cell in enumerate(cells):
        for child in h3.cell_to_children(cell, resolution + FINER):
            points.append(h3.cell_to_latlng(child))
            owner.append(index)
    lat = np.array([p[0] for p in points])
    lng = np.array([p[1] for p in points])
    x, y = _TO_BNG.transform(lng, lat)
    classes = mosaic.at(np.asarray(x), np.asarray(y))
    owner_index = np.asarray(owner, dtype=np.int64)

    known = classes != UNKNOWN
    risky = known & ((classes == MEDIUM) | (classes == HIGH))
    seen = np.bincount(owner_index[known], minlength=len(cells))
    at_risk = np.bincount(owner_index[risky], minlength=len(cells))
    share = np.full(len(cells), np.nan)
    has_points = seen > 0
    share[has_points] = 100 * at_risk[has_points] / seen[has_points]
    return pd.Series(share, index=cells)
