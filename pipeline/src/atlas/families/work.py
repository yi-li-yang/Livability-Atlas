"""Work and economy: the jobs around a cell (`job-density`) and the coworking spaces within a
15-minute walk (`coworking`). The jobs are the Business Register and Employment Survey's, shared
between cells by area (`Context.workers`); the spaces are Overture's. See the indicators' methods
in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import h3
import numpy as np
import pandas as pd

from atlas.families import Context, Family

STEPS = 2
COWORKING_MINUTES = 15
COWORKING = {"coworking_space", "shared_office_space"}


def jobs_per_km2(workers: pd.Series, cells: list[str], steps: int = STEPS) -> pd.Series:
    """The jobs a square kilometre over each cell and the cells within `steps` of it that the
    region has."""
    present = set(workers.index)
    out = np.full(len(cells), np.nan)
    for i, cell in enumerate(cells):
        near = [c for c in h3.grid_disk(cell, steps) if c in present]
        if near:
            area = sum(h3.cell_area(c, "km^2") for c in near)
            out[i] = float(workers.reindex(near).sum()) / area
    return pd.Series(out, index=cells)


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    density = jobs_per_km2(ctx.workers, ctx.cells)
    return {
        "job-density": [None if pd.isna(v) else float(v) for v in density],
        "coworking": ctx.count_within(ctx.places_of(COWORKING), COWORKING_MINUTES),
    }


FAMILY = Family("work", columns)
