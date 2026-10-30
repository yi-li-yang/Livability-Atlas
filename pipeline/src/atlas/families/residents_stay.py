"""Community and people: how long residents stay (`residents-stay`).

The share of a cell's residents who lived at the same address a year before the 2021 census, from
the output areas' counts shared between cells by area. See the indicator's method in the
catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from atlas.datasets.countries.gb import census_migrant
from atlas.families import Context, Family
from atlas.indicators import crime


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    counts = census_migrant.read_counts(census_migrant.fetch(ctx.data_dir))
    shared = crime.counts_shared_by_cell(ctx.areas, counts, ctx.cells).reindex(ctx.cells)
    residents = shared["residents"].to_numpy(dtype=float)
    same = shared["same_address"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(residents > 0, 100.0 * same / residents, np.nan)
    share = np.clip(share, 0.0, 100.0)
    return {"residents-stay": [None if pd.isna(v) else float(v) for v in share]}


FAMILY = Family("residents_stay", columns)
