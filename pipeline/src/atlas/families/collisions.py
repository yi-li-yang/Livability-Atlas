"""Safety: fatal and serious road collisions (`road-collisions`).

The collisions of the latest three years in each cell, per year, against the people present there
(residents and workers), pooled over a cell's neighbours with a floor as the crime rates are. See
the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import h3
import pandas as pd

from atlas.datasets.countries.gb import dft_stats19
from atlas.families import Context, Family
from atlas.indicators import crime


def collisions_per_year(collisions: pd.DataFrame, cells: list[str], resolution: int) -> pd.Series:
    """The collisions of one year, on average, in each cell. `collisions` has a `Longitude` and a
    `Latitude` for each; one outside `cells` is left out."""
    wanted = set(cells)
    tally = dict.fromkeys(cells, 0)
    for lat, lng in zip(collisions["Latitude"], collisions["Longitude"], strict=True):
        cell = h3.latlng_to_cell(lat, lng, resolution)
        if cell in wanted:
            tally[cell] += 1
    return pd.Series(tally, dtype=float) / len(dft_stats19.YEARS)


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    collisions = dft_stats19.read_collisions(dft_stats19.fetch(ctx.data_dir))
    counts = collisions_per_year(collisions, ctx.cells, ctx.resolution)
    rate = crime.rates(counts, ctx.people, ctx.cells)
    return {"road-collisions": [None if pd.isna(v) else float(v) for v in rate]}


FAMILY = Family("collisions", columns)
