"""Community and people: the turnout at the local election of the ward a cell lies in
(`election-turnout`), from the GLA's results for the London borough elections of May 2022
(`gla_elections`) and the ONS's ward boundaries (`ons_wards`). See the indicator's method in the
catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np

from atlas.datasets.cities.london import gla_elections
from atlas.datasets.countries.gb import ons_wards
from atlas.families import Context, Family
from atlas.indicators import turnout
from atlas.spatial.grid import bounds_bng


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    wards = ons_wards.read_boundaries(
        ons_wards.fetch(ctx.data_dir, bounds_bng(ctx.cells, margin=2000))
    )
    results = gla_elections.read_turnout(
        gla_elections.fetch(ctx.data_dir), wards["LAD22NM"].unique().tolist()
    )
    share = turnout.by_ward(results, wards).dropna()
    values = turnout.by_cell(wards, share.to_dict(), ctx.cells)
    return {"election-turnout": [None if np.isnan(v) else float(v) for v in values]}


# The GLA's results cover London's boroughs only.
FAMILY = Family("civic", columns, regions=("london",))
