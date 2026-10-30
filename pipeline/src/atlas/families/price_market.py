"""Housing and cost: how the market moves (`price-trend`) and how busy it is (`sales-volume`).

Both read the sales of HM Land Registry's Price Paid Data. The trend sets the price per square
metre of the latest 24 months against that of the 24 months five years before, each found as
`buying-cost` is (see `atlas.indicators.prices`). The volume is the sales of a year against the
residents. See the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any, cast

import numpy as np
import pandas as pd

from atlas.datasets.countries.gb import code_point, epc, hm_land_registry
from atlas.families import Context, Family
from atlas.indicators import crime, prices
from atlas.spatial.grid import cells_at_bng

MONTHS = 24
YEARS_BACK = 5


def change(now: pd.Series, then: pd.Series) -> pd.Series:
    """The percent change from `then` to `now`, missing where either is."""
    return (now / then - 1) * 100


def _with_cells(ctx: Context, sales: pd.DataFrame, inside: pd.DataFrame) -> pd.DataFrame:
    """The sales whose postcode is inside the region's reach, with the cell of its centre."""
    keys = pd.Index([code_point.normalise(p) for p in sales["postcode"]])
    where = inside.reindex(keys)
    easting = where["Easting"].to_numpy(dtype=float)
    northing = where["Northing"].to_numpy(dtype=float)
    known = ~np.isnan(easting)
    located = sales.loc[known].reset_index(drop=True)
    located["cell"] = cells_at_bng(easting[known], northing[known], ctx.resolution)
    return located


def _per_metre(located: pd.DataFrame, certificates: pd.DataFrame, ctx: Context) -> pd.Series:
    """The pooled median price per square metre of the sales in each cell (`buying-cost`'s)."""
    area = prices.floor_areas(located, certificates)
    sold = pd.DataFrame(
        {
            "cell": located["cell"],
            "per_metre": prices.per_metre(cast(pd.Series, located["price"]), area),
        }
    ).dropna()
    return prices.pooled_median(sold, ctx.cells)


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    inside = ctx.postcodes_inside()
    now_paths = hm_land_registry.fetch(ctx.data_dir, hm_land_registry.YEARS)
    ending = hm_land_registry.latest_date(now_paths)
    earlier_end = ending - pd.DateOffset(years=YEARS_BACK)
    then_years = hm_land_registry.years_of(earlier_end, MONTHS)
    then_paths = hm_land_registry.fetch(ctx.data_dir, then_years)
    now = _with_cells(ctx, hm_land_registry.read_window(now_paths, ending, MONTHS), inside)
    then = _with_cells(ctx, hm_land_registry.read_window(then_paths, earlier_end, MONTHS), inside)

    certificates = epc.certificates(ctx.data_dir, ctx.region_id, set(inside.index))
    trend = change(_per_metre(now, certificates, ctx), _per_metre(then, certificates, ctx))

    tally = cast(pd.Series, now.groupby("cell").size())
    per_year = tally.reindex(ctx.cells).fillna(0) / (MONTHS / 12)
    volume = crime.rates(per_year, ctx.residents, ctx.cells)
    return {
        "price-trend": [None if pd.isna(v) else float(v) for v in trend],
        "sales-volume": [None if pd.isna(v) else float(v) for v in volume],
    }


FAMILY = Family(
    "price_market",
    columns,
    built_from={
        "price-trend": ("hm-land-registry-price-paid", "epc-domestic"),
        "sales-volume": ("hm-land-registry-price-paid",),
    },
)
