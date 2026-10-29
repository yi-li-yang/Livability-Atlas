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


# The census's categories that are not a group of people to be near, or too few to rank (British
# Overseas births: a share of 0.0% in the middle of London's cells).
NOT_OFFERED = {"Not answered", "Other religion", "British Overseas"}


def slug(text: str) -> str:
    """The text as an id of lowercase words joined by hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def community_options(
    ethnic: pd.DataFrame,
    religion: pd.DataFrame,
    birth: pd.DataFrame | None = None,
    age: pd.DataFrame | None = None,
) -> list[tuple[str, str, str, pd.Series]]:
    """The options of Your community, as (id, name, group, share of residents in each cell).

    Each argument is the cells' shares from `shares`, a column for each group of a census table.
    An ethnic group is named by the part of its census name after the last colon, a place of
    birth by `BIRTH_NAMES`, and an age by its life stage (`life_stages`).
    """
    options = []
    for column in ethnic.columns:
        name = str(column).rsplit(": ", 1)[-1]
        options.append((f"ethnic-{slug(name)}", name, "Ethnic group", ethnic[column]))
    for column in religion.columns:
        if column not in NOT_OFFERED:
            title = str(column)
            options.append((f"religion-{slug(title)}", title, "Religion", religion[column]))
    if birth is not None:
        for column in birth.columns:
            if column in NOT_OFFERED:
                continue
            name = BIRTH_NAMES.get(str(column), str(column))
            options.append((f"born-{slug(str(column))}", name, "Country of birth", birth[column]))
    if age is not None:
        for column in age.columns:
            options.append((f"age-{slug(str(column))}", str(column), "Age", age[column]))
    return options


# The picker's words for the places of birth that Census 2021 gives at the smallest areas.
BIRTH_NAMES = {
    "United Kingdom": "Born in the United Kingdom",
    "European Union EU14": "Born in the older EU countries (such as France or Spain)",
    "European Union EU8": "Born in the eastern EU (such as Poland)",
    "European Union EU2": "Born in Romania or Bulgaria",
    "All other EU countries": "Born in another EU country",
    "All other non-EU countries": "Born in another European country",
    "Africa": "Born in Africa",
    "Middle East and Asia": "Born in the Middle East or Asia",
    "The Americas and the Caribbean": "Born in the Americas or the Caribbean",
    "Antarctica and Oceania (including Australasia) and Other": "Born in Oceania or elsewhere",
}
# The five-year age bands added into life stages, by the first and last band of each.
LIFE_STAGES = {
    "Children under 15": ("Aged 4 years and under", "Aged 10 to 14 years"),
    "Aged 15 to 24": ("Aged 15 to 19 years", "Aged 20 to 24 years"),
    "Aged 25 to 34": ("Aged 25 to 29 years", "Aged 30 to 34 years"),
    "Aged 35 to 49": ("Aged 35 to 39 years", "Aged 45 to 49 years"),
    "Aged 50 to 64": ("Aged 50 to 54 years", "Aged 60 to 64 years"),
    "Aged 65 and over": ("Aged 65 to 69 years", "Aged 85 years and over"),
}


def life_stages(bands: pd.DataFrame) -> pd.DataFrame:
    """The residents of each area in each life stage: the five-year bands (youngest first) added
    up, so that the stages cover everyone."""
    columns = list(bands.columns)
    return pd.DataFrame(
        {
            stage: bands[columns[columns.index(first) : columns.index(last) + 1]].sum(axis=1)
            for stage, (first, last) in LIFE_STAGES.items()
        }
    )
