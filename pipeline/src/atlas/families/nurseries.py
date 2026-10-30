"""Education: the walk to a nursery (`nurseries`).

The minutes on foot along streets from each cell to the nearest nursery or pre-school on Ofsted's
register, placed by postcode. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import ofsted_childcare
from atlas.families import Context, Family
from atlas.indicators import health


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    sites = ofsted_childcare.read_nurseries(ofsted_childcare.fetch(ctx.data_dir))
    places = health.site_places(sites, ctx.postcodes)
    minutes = health.gp_minutes(ctx.network, places, ctx.cells)
    return {"nurseries": [None if pd.isna(m) else float(m) for m in minutes]}


FAMILY = Family("nurseries", columns)
