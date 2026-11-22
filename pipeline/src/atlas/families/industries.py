"""Work and economy: the industries a user can choose (`your-industry`).

For each industry section, the jobs a square kilometre over a cell and the cells within two steps,
from the Business Register and Employment Survey's open table of jobs by 2011 LSOA, shared between
cells by area. A cell scores the best of the industries the user picks. See the indicator's method
in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import bres, ons_lsoa
from atlas.families import Context, Family
from atlas.indicators import crime
from atlas.indicators.pooling import per_km2
from atlas.publish.bundle import Choice
from atlas.spatial.grid import bounds_bng

STEPS = 2
# The sections of the Standard Industrial Classification that a person picks as their line of work.
# Farming, mining, utilities, households as employers and extraterritorial bodies are left out:
# there are too few jobs in London to rank, or no one means them by an industry.
INDUSTRIES = {
    "C": "Manufacturing",
    "F": "Construction",
    "G": "Retail and wholesale trade",
    "H": "Transport and storage",
    "I": "Hotels, restaurants and cafés",
    "J": "Information and communication",
    "K": "Finance and insurance",
    "L": "Real estate",
    "M": "Professional, scientific and technical work",
    "N": "Administrative and support services",
    "O": "Public administration and defence",
    "P": "Education",
    "Q": "Health and social work",
    "R": "Arts, entertainment and recreation",
}


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    return {}


def choices(ctx: Context) -> dict[str, list[Choice]]:
    lsoas = ons_lsoa.read_boundaries(
        ons_lsoa.fetch(ctx.data_dir, bounds_bng(ctx.cells, margin=2000))
    )
    jobs = pd.DataFrame(
        {letter: bres.read_jobs(bres.fetch_industry(ctx.data_dir, letter)) for letter in INDUSTRIES}
    )
    shared = crime.counts_shared_by_cell(lsoas, jobs, ctx.cells, code="LSOA11CD").reindex(ctx.cells)
    options = []
    for letter, name in INDUSTRIES.items():
        density = per_km2(pd.Series(shared[letter]).dropna(), ctx.cells, STEPS)
        values = [None if pd.isna(v) else round(float(v)) for v in density]
        options.append(Choice(id=letter.lower(), name=name, group="Industry", values=values))
    return {"your-industry": options}


FAMILY = Family("industries", columns, choices=choices)
