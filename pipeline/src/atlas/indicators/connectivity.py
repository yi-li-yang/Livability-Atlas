"""The digital connectivity indicators.

The share of homes with gigabit-capable broadband comes by census output area, which is shared
between the hex cells that it overlaps by area, as the residents of Safety's crime rates are (spike
S2): the cell's gigabit homes over its homes. The 5G coverage comes by local authority, so a cell
takes its borough's value (`housing.by_borough`).
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from atlas.indicators.crime import residents_by_cell


def gigabit_share(areas: gpd.GeoDataFrame, homes: pd.DataFrame, cells: list[str]) -> pd.Series:
    """The percentage of each cell's homes that can get a gigabit-capable connection.

    `areas` holds output area boundaries in British National Grid in a column `OA21CD`, and
    `homes` is indexed by the same codes, with `homes` and `gigabit_homes`. A cell with no homes
    has no value.
    """
    total = residents_by_cell(areas, pd.Series(homes["homes"]), cells).reindex(cells)
    gigabit = residents_by_cell(areas, pd.Series(homes["gigabit_homes"]), cells).reindex(cells)
    homes_in = total.to_numpy(dtype=float)
    share = np.where(homes_in > 0, 100.0 * gigabit.to_numpy(dtype=float) / homes_in, np.nan)
    return pd.Series(share, index=cells, dtype=float)
