"""The noise indicators of Environment: the average modelled daytime level from roads, railways and
aircraft at each hex cell (spike S5).

A cell takes the arithmetic mean, in decibels, of the levels at its addresses, because that is
what the people who live there hear: it matches the average of the addresses' own scores almost
exactly, where an average over the area does not. A cell with no address, such as a park, takes the
mean over its area. A cell the map does not reach has no value.
"""

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer

from atlas.indicators.air_quality import Surface, mean_concentration

_FROM_BNG = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


def mean_level(
    levels: Surface, addresses: np.ndarray, cells: list[str], resolution: int
) -> pd.Series:
    """The mean level (dB) in each cell. `addresses` holds an easting and a northing for each."""
    mean = mean_concentration(levels, cells, resolution)  # the area's mean, for cells without
    if len(addresses) == 0:
        return mean
    lng, lat = _FROM_BNG.transform(addresses[:, 0], addresses[:, 1])
    owner = {cell: i for i, cell in enumerate(cells)}
    index = np.array(
        [owner.get(h3.latlng_to_cell(a, b, resolution), -1) for a, b in zip(lat, lng, strict=True)]
    )
    level = levels.at(addresses[:, 0], addresses[:, 1])
    counted = (index >= 0) & ~np.isnan(level)
    seen = np.bincount(index[counted], minlength=len(cells))
    total = np.bincount(index[counted], weights=level[counted], minlength=len(cells))
    result = mean.to_numpy(dtype=float, copy=True)
    has_addresses = seen > 0
    result[has_addresses] = total[has_addresses] / seen[has_addresses]
    return pd.Series(result, index=cells)
