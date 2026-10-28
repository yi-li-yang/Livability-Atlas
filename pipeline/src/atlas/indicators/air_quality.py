"""The air quality indicators of Environment: the mean modelled concentration of a pollutant over
each hex cell.

The mean is over the cell's area, read at points spread evenly over it: the centres of the 49 cells
of two resolutions finer (about 15 m apart), each taking the value of the nearest point of the
model's 20 m grid. A cell with no point on the grid has no value.
"""

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer

from atlas.datasets.cities.london.laei import Grid

FINER = 2  # resolutions finer than the hex cells: 49 points a cell
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def mean_concentration(grid: Grid, cells: list[str], resolution: int) -> pd.Series:
    """The mean concentration (µg/m³) over each cell, from the points of `grid` inside it."""
    points: list[tuple[float, float]] = []
    owner: list[int] = []
    for index, cell in enumerate(cells):
        for child in h3.cell_to_children(cell, resolution + FINER):
            points.append(h3.cell_to_latlng(child))
            owner.append(index)
    lat = np.array([p[0] for p in points])
    lng = np.array([p[1] for p in points])
    x, y = _TO_BNG.transform(lng, lat)
    found = grid.at(np.asarray(x), np.asarray(y))
    owner_index = np.asarray(owner, dtype=np.int64)

    known = ~np.isnan(found)
    seen = np.bincount(owner_index[known], minlength=len(cells))
    total = np.bincount(owner_index[known], weights=found[known], minlength=len(cells))
    mean = np.full(len(cells), np.nan)
    has_points = seen > 0
    mean[has_points] = total[has_points] / seen[has_points]
    return pd.Series(mean, index=cells)
