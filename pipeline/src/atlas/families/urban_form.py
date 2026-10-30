"""Urban form and change: how crowded an area is (`density`) and how old its homes are
(`building-age`). The residents are the census's, shared between cells by area
(`Context.residents`); the age is the median year in which the homes with an energy certificate
were built. See the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.families import Context, Family
from atlas.families.energy import homes_by_cell
from atlas.indicators.pooling import per_km2, pooled_median

STEPS = 2
AGE_STEPS = 1
MINIMUM_HOMES = 30


def columns_with(ctx: Context, homes: pd.DataFrame) -> dict[str, Sequence[Any]]:
    """The columns for `homes`, a table of the region's homes with a `cell` and the year `built`."""
    density = per_km2(ctx.residents, ctx.cells, STEPS)
    age = pooled_median(homes, "built", ctx.cells, AGE_STEPS, MINIMUM_HOMES)
    return {
        "density": [None if pd.isna(v) else float(v) for v in density],
        "building-age": [None if pd.isna(v) else float(v) for v in age],
    }


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    return columns_with(ctx, homes_by_cell(ctx))


FAMILY = Family("urban_form", columns, built_from={"building-age": ("epc-domestic",)})
