"""Housing and cost: how well the homes nearby keep heat in (`energy-efficiency`).

The energy performance certificates' points for each home (a home counts once, by its latest
certificate), pooled over a cell and its neighbours. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import pandas as pd

from atlas.datasets.countries.gb import epc
from atlas.families import Context, Family
from atlas.indicators.pooling import pooled_median
from atlas.spatial.grid import cells_at_bng

STEPS = 1
MINIMUM_HOMES = 30


def homes_by_cell(ctx: Context) -> pd.DataFrame:
    """The region's homes with the cell that holds their postcode's centre."""
    inside = ctx.postcodes_inside()
    homes = epc.stock(ctx.data_dir, ctx.region_id, set(inside.index))
    where = inside.reindex(pd.Index(homes["postcode"]))
    known = where["Easting"].notna().to_numpy()
    homes = homes.loc[known].reset_index(drop=True)
    homes["cell"] = cells_at_bng(
        where["Easting"].to_numpy(dtype=float)[known],
        where["Northing"].to_numpy(dtype=float)[known],
        ctx.resolution,
    )
    return homes


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    median = pooled_median(homes_by_cell(ctx), "efficiency", ctx.cells, STEPS, MINIMUM_HOMES)
    return {"energy-efficiency": [None if pd.isna(v) else float(v) for v in median]}


FAMILY = Family("energy", columns, built_from={"energy-efficiency": ("epc-domestic",)})
