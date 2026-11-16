"""Health care: how long people wait at the nearest A&E (`ae-waiting`).

Each cell takes the four-hour performance of the trust that runs its nearest emergency department
(a straight line, as the distance to A&E is), among the departments whose trust has figures. See
the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from atlas.datasets.countries.gb import nhs_ae, nhs_ae_waits
from atlas.datasets.countries.gb.code_point import normalise
from atlas.families import Context, Family
from atlas.indicators import health
from atlas.spatial.grid import cell_centres_bng

# Departments whose code does not start with their trust's three characters.
TRUST_OF = {"AXA02": "R1H"}  # the Royal London Hospital, run by Barts Health


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    seeds = health.ae_seed_postcodes(ctx.cells, ctx.postcodes)
    sites = nhs_ae.read_sites(nhs_ae.fetch(ctx.data_dir, ctx.region_id, seeds))
    performance = nhs_ae_waits.read_performance(nhs_ae_waits.fetch(ctx.data_dir)).to_dict()
    where = ctx.postcodes[["Easting", "Northing"]].reindex(
        pd.Index([normalise(p) for p in sites["Postcode"]])
    )
    trusts = [TRUST_OF.get(code, code[:3]) for code in sites["code"]]
    usable = [
        i
        for i, trust in enumerate(trusts)
        if trust in performance and not where.iloc[i].isna().any()
    ]
    if not usable:
        return {"ae-waiting": [None] * len(ctx.cells)}
    points = where.iloc[usable].to_numpy(dtype=float)
    values = np.array([performance[trusts[i]] for i in usable])
    _, nearest = KDTree(points).query(cell_centres_bng(ctx.cells))
    return {"ae-waiting": [float(values[i]) for i in np.atleast_1d(nearest)]}


FAMILY = Family("ae_waits", columns)
