"""Health care: the walk to a dentist (`dentists`).

The minutes on foot along streets from each cell to the nearest active dental practice of NHS
England's register, placed by postcode. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import nhs_ods
from atlas.families import Context, Family
from atlas.indicators import health


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    sites = nhs_ods.read_dental_sites(nhs_ods.fetch_dental(ctx.data_dir))
    places = health.site_places(sites, ctx.postcodes)
    minutes = health.gp_minutes(ctx.network, places, ctx.cells)
    return {"dentists": [None if pd.isna(m) else float(m) for m in minutes]}


FAMILY = Family("dentists", columns)
