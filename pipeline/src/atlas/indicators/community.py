"""The community indicators.

Diversity is Simpson's index over the census's detailed ethnic groups: the chance that two
residents picked at random belong to different groups. Each cell's residents in each group are
its output areas' counts shared by area (`crime.counts_shared_by_cell`), and the index is taken
on those, not averaged from the areas' indexes.
"""

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
