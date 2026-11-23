"""Housing and cost: how well the homes nearby keep heat in (`energy-efficiency`).

The energy performance certificates' points for each home (a home counts once, by its latest
certificate), pooled over a cell and its neighbours. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.families import Context, Family
from atlas.indicators.pooling import pooled_median

STEPS = 1
MINIMUM_HOMES = 30


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    median = pooled_median(ctx.homes, "efficiency", ctx.cells, STEPS, MINIMUM_HOMES)
    return {"energy-efficiency": [None if pd.isna(v) else float(v) for v in median]}


FAMILY = Family("energy", columns, built_from={"energy-efficiency": ("epc-domestic",)})
