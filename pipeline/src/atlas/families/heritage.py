"""Culture and leisure: the listed buildings within a 10-minute walk (`local-character`) and the
share of a cell inside a conservation area (`conservation-areas`), from planning.data.gov.uk. See
the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import planning_data
from atlas.families import Context, Family
from atlas.indicators import places
from atlas.indicators.coverage import share_inside
from atlas.spatial.grid import lonlat_box

WALK_MINUTES = 10


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    box = lonlat_box(ctx.cells, margin=0.05)
    listed = planning_data.read_listed_buildings(
        planning_data.fetch(ctx.data_dir, "listed-building"), box
    )
    xy = places.to_metres(listed["lng"].to_numpy(dtype=float), listed["lat"].to_numpy(dtype=float))
    buildings = pd.DataFrame({"Easting": xy[:, 0], "Northing": xy[:, 1]})
    areas = planning_data.read_areas(planning_data.fetch(ctx.data_dir, "conservation-area"), box)
    in_metres = list(areas.to_crs("EPSG:27700").geometry) if len(areas) else []
    return {
        "local-character": ctx.count_within(buildings, WALK_MINUTES),
        "conservation-areas": [float(v) for v in share_inside(in_metres, ctx.cells)],
    }


FAMILY = Family("heritage", columns)
