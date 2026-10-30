"""Resident wellbeing: the years of good health a baby born in the area can expect
(`life-expectancy`). Each cell takes the estimate of the neighbourhood (MSOA) that holds its
centre. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import ons_hsle
from atlas.families import Context, Family
from atlas.spatial import neighbourhoods


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    years = ons_hsle.read_msoa(ons_hsle.fetch(ctx.data_dir)).to_dict()
    owner = neighbourhoods.neighbourhood_of(ctx.msoas, ctx.cells)
    found: list[float | None] = []
    for code in owner:
        value = years.get(code) if code is not None else None
        found.append(None if value is None or pd.isna(value) else float(value))
    return {"life-expectancy": found}


FAMILY = Family("wellbeing", columns)
