"""The share of the land around a cell that polygons cover (conservation areas, nature sites)."""

from collections.abc import Sequence

import h3
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def share_inside(
    polygons: Sequence[BaseGeometry], cells: list[str], buffer: float = 0.0
) -> pd.Series:
    """The percent of each cell's area inside `polygons` (in metres of British National Grid).
    With a `buffer` in metres, the area is the cell's widened by that distance on every side."""
    out = np.zeros(len(cells))
    if len(polygons):
        covered = shapely.union_all(list(polygons))
        shapely.prepare(covered)
        for i, cell in enumerate(cells):
            boundary = h3.cell_to_boundary(cell)
            xs, ys = _TO_BNG.transform([lng for _, lng in boundary], [lat for lat, _ in boundary])
            outline = Polygon(zip(xs, ys, strict=True))
            if buffer:
                outline = outline.buffer(buffer)
            if covered.intersects(outline):
                out[i] = 100.0 * covered.intersection(outline).area / outline.area
    return pd.Series(out, index=cells)
