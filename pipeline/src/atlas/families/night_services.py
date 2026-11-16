"""Transport: the services that run at night (`night-services`), for London.

The night bus routes (TfL's N routes, which run only at night) within an 8-minute walk and the
night Tube and Overground lines within a 12-minute walk, counted together. See the indicator's
method in the catalogue.
"""

import re
from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.cities.london import tfl_lines
from atlas.families import Context, Family
from atlas.indicators import transport

BUS_MINUTES = 8
RAIL_MINUTES = 12
NIGHT_BUS = re.compile(r"^n\d+$")  # TfL's id of a night route: n1, n29, n109
NIGHT_RAIL = {"central", "jubilee", "northern", "piccadilly", "victoria", "windrush"}


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    stops = transport.place_stops(tfl_lines.read_stops(tfl_lines.fetch(ctx.data_dir)))
    bus = pd.DataFrame(
        stops[(stops["kind"] == "bus") & stops["line"].map(lambda x: bool(NIGHT_BUS.match(x)))]
    )
    rail = pd.DataFrame(stops[(stops["kind"] == "rail") & stops["line"].isin(sorted(NIGHT_RAIL))])
    buses = transport.lines_within_a_walk(ctx.network, bus, ctx.cells, BUS_MINUTES)
    trains = transport.lines_within_a_walk(ctx.network, rail, ctx.cells, RAIL_MINUTES)
    return {"night-services": [int(n) for n in buses + trains]}


FAMILY = Family("night_services", columns, regions=("london",))
