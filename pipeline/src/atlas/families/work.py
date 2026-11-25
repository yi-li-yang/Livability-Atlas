"""Work and economy: the jobs around a cell (`job-density`), the jobs it reaches by public
transport within 45 minutes (`jobs-within-reach`) and the coworking spaces within a 15-minute walk
(`coworking`). The jobs are the Business Register and Employment Survey's, shared between cells by
area (`Context.workers`); the journeys are the travel estimate's (`Context.reached_by_transport`);
the spaces are Overture's. See the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.families import Context, Family
from atlas.indicators.pooling import per_km2

STEPS = 2
REACH_MINUTES = 45
COWORKING_MINUTES = 15
COWORKING = {"coworking_space", "shared_office_space"}


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    density = per_km2(ctx.workers, ctx.cells, STEPS)
    return {
        "job-density": [None if pd.isna(v) else float(v) for v in density],
        "jobs-within-reach": ctx.reached_by_transport(
            ctx.workers.reindex(ctx.cells).to_numpy(dtype=float), REACH_MINUTES
        ),
        "coworking": ctx.count_within(ctx.places_of(COWORKING), COWORKING_MINUTES),
    }


FAMILY = Family("work", columns)
