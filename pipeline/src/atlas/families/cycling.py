"""Transport: cycling, as the kilometres of cycle track within 1 km (`cycle-tracks`, from
OpenStreetMap) and the cycle hire docking stations within a 10-minute walk (`cycle-hire`, from TfL).
See the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
from pyproj import Transformer

from atlas.datasets.cities.london import tfl_bikepoints
from atlas.datasets.world import openstreetmap
from atlas.families import Context, Family
from atlas.indicators import cycling

TRACK_RADIUS = 1000.0  # metres, in a straight line: a few minutes' ride
HIRE_MINUTES = 10  # 800 m: TfL spaces docks 300 to 500 m apart, and 5 minutes missed the City
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    tracks = openstreetmap.cycle_tracks(ctx.data_dir, ctx.region_id)
    x0, y0 = _TO_BNG.transform(tracks["lng0"].to_numpy(), tracks["lat0"].to_numpy())
    x1, y1 = _TO_BNG.transform(tracks["lng1"].to_numpy(), tracks["lat1"].to_numpy())
    km = cycling.track_km(np.column_stack([x0, y0, x1, y1]), ctx.cells, TRACK_RADIUS)
    docks = tfl_bikepoints.read_docks(tfl_bikepoints.fetch(ctx.data_dir))
    return {
        "cycle-tracks": [float(v) for v in km],
        "cycle-hire": ctx.count_within(docks, HIRE_MINUTES),
    }


# The docking stations are TfL's, so the family is for London.
FAMILY = Family("cycling", columns, regions=("london",))
