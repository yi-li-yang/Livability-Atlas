"""GP access: how patients rate the GP practices within a 15-minute walk (`gp-experience`), from
the GP Patient Survey (`gpps`), weighted by each practice's registered patients (`nhs_gp`). See the
indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import gpps, nhs_gp
from atlas.families import Context, Family
from atlas.indicators import health

MINUTES = 15


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    practices = health.located_practices(
        nhs_gp.read_practices(*nhs_gp.fetch(ctx.data_dir)), ctx.postcodes
    )
    ratings = gpps.read_ratings(gpps.fetch(ctx.data_dir))
    rating = health.patient_rating(
        ctx.network,
        practices[["Easting", "Northing"]].to_numpy(dtype=float),
        ratings["good"].reindex(practices.index).to_numpy(dtype=float),
        practices["patients"].to_numpy(dtype=float),
        ctx.cells,
        MINUTES,
    )
    return {"gp-experience": [None if pd.isna(v) else float(v) for v in rating]}


# The survey's data has no licence statement of its own (see the dataset's licence note), so a
# commercial build leaves the indicator out (D07).
FAMILY = Family("gp_experience", columns, built_from={"gp-experience": ("nhs-gp-patient-survey",)})
