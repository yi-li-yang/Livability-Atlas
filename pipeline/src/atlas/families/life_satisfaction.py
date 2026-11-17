"""Resident wellbeing: how satisfied residents are with their lives (`life-satisfaction`).

Measured for a whole borough, so each cell takes the value of the borough that holds its centre.
See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import ons_local_authorities, ons_wellbeing
from atlas.families import Context, Family
from atlas.indicators import housing


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    values = ons_wellbeing.read_life_satisfaction(ons_wellbeing.fetch(ctx.data_dir))
    owner = ons_local_authorities.borough_of(
        ons_local_authorities.fetch(ctx.data_dir, ctx.region_id), ctx.cells
    )
    found = housing.by_borough(values, owner, ctx.cells)
    return {"life-satisfaction": [None if pd.isna(v) else float(v) for v in found]}


FAMILY = Family("life_satisfaction", columns)
