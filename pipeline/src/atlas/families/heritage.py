"""Culture and leisure: the listed buildings within a 10-minute walk (`local-character`) and the
share of a cell inside a conservation area (`conservation-areas`), from planning.data.gov.uk. See
the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import h3
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from atlas.datasets.countries.gb import planning_data
from atlas.families import Context, Family
from atlas.indicators import places
from atlas.spatial.grid import lonlat_box

WALK_MINUTES = 10
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def share_inside(polygons: Sequence[BaseGeometry], cells: list[str]) -> pd.Series:
    """The percent of each cell's area inside `polygons` (in metres of British National Grid)."""
    out = np.zeros(len(cells))
    if len(polygons):
        covered = shapely.union_all(list(polygons))
        shapely.prepare(covered)
        for i, cell in enumerate(cells):
            boundary = h3.cell_to_boundary(cell)
            xs, ys = _TO_BNG.transform([lng for _, lng in boundary], [lat for lat, _ in boundary])
            outline = Polygon(zip(xs, ys, strict=True))
            if covered.intersects(outline):
                out[i] = 100.0 * covered.intersection(outline).area / outline.area
    return pd.Series(out, index=cells)


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    box = lonlat_box(ctx.cells, margin=0.05)
    listed = planning_data.read_listed_buildings(
        planning_data.fetch(ctx.data_dir, "listed-building"), box
    )
    xy = places.to_metres(listed["lng"].to_numpy(dtype=float), listed["lat"].to_numpy(dtype=float))
    buildings = pd.DataFrame({"Easting": xy[:, 0], "Northing": xy[:, 1]})
    areas = planning_data.read_conservation_areas(
        planning_data.fetch(ctx.data_dir, "conservation-area"), box
    )
    in_metres = list(areas.to_crs("EPSG:27700").geometry) if len(areas) else []
    return {
        "local-character": ctx.count_within(buildings, WALK_MINUTES),
        "conservation-areas": [float(v) for v in share_inside(in_metres, ctx.cells)],
    }


FAMILY = Family("heritage", columns)
