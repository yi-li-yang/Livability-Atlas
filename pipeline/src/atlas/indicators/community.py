"""The community indicators.

Diversity is Simpson's index over the census's detailed ethnic groups: the chance that two
residents picked at random belong to different groups. Each cell's residents in each group are
its output areas' counts shared by area (`crime.counts_shared_by_cell`), and the index is taken
on those, not averaged from the areas' indexes.
"""

import re

import geopandas as gpd
import numpy as np
import pandas as pd

from atlas.indicators.crime import counts_shared_by_cell


def simpson(counts: np.ndarray) -> np.ndarray:
    """One minus the sum of the squared shares, for each row of group counts. A row with no
    residents has no value."""
    totals = counts.sum(axis=1)
    shares = np.divide(
        counts, totals[:, None], out=np.full(counts.shape, np.nan), where=totals[:, None] > 0
    )
    return 1.0 - (shares**2).sum(axis=1)


def diversity(areas: gpd.GeoDataFrame, groups: pd.DataFrame, cells: list[str]) -> pd.Series:
    """The diversity index of each cell, from 0 (one group) towards 1 (many, evenly).

    `areas` holds output area boundaries in British National Grid in a column `OA21CD`, and
    `groups` is indexed by the same codes, with a column of residents for each group. A cell with
    no residents has no value.
    """
    shared = counts_shared_by_cell(areas, groups, cells).reindex(cells).fillna(0.0)
    return pd.Series(simpson(shared.to_numpy(dtype=float)), index=cells, dtype=float)


def shares(areas: gpd.GeoDataFrame, groups: pd.DataFrame, cells: list[str]) -> pd.DataFrame:
    """The percentage of each cell's residents in each group, with a column for each of `groups`.

    `groups` is indexed by output area code and must list every group of its table, so that the
    columns add up to the area's residents. A cell with no residents has no shares.
    """
    shared = counts_shared_by_cell(areas, groups, cells).reindex(cells).fillna(0.0)
    counts = shared.to_numpy(dtype=float)
    totals = counts.sum(axis=1)
    percent = np.divide(
        100.0 * counts,
        totals[:, None],
        out=np.full(counts.shape, np.nan),
        where=totals[:, None] > 0,
    )
    return pd.DataFrame(percent, index=cells, columns=shared.columns)


# The census's categories that are not a group of people to be near.
NOT_OFFERED = {"Not answered", "Other religion"}


def slug(text: str) -> str:
    """The text as an id of lowercase words joined by hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def community_options(
    ethnic: pd.DataFrame, religion: pd.DataFrame
) -> list[tuple[str, str, str, pd.Series]]:
    """The options of Your community, as (id, name, group, share of residents in each cell).

    `ethnic` and `religion` are the cells' shares from `shares`, a column for each group of the
    census's tables. An ethnic group is named by the part of its census name after the last colon.
    """
    options = []
    for column in ethnic.columns:
        name = str(column).rsplit(": ", 1)[-1]
        options.append((f"ethnic-{slug(name)}", name, "Ethnic group", ethnic[column]))
    for column in religion.columns:
        if column not in NOT_OFFERED:
            options.append(
                (f"religion-{slug(str(column))}", str(column), "Religion", religion[column])
            )
    return options
