"""The daily amenities that are walks: the minutes on foot to the nearest of a kind of place."""

import numpy as np
import pandas as pd

from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

# The catalogue's indicator for the kind of place whose nearest one it measures.
NEAREST = {
    "groceries": "grocery",
    "pharmacies": "pharmacy",
    "gyms": "gym",
    "libraries": "library",
}


def nearest_minutes(
    network: Network, places: dict[str, pd.DataFrame], cells: list[str]
) -> dict[str, pd.Series]:
    """The walking minutes from each cell's centre to the nearest place of each kind, along
    streets and paths. `places` maps a kind to a table with `Easting` and `Northing`; a kind with
    no place gives no value."""
    origins = cell_centres_bng(cells)
    result: dict[str, pd.Series] = {}
    for indicator, kind in NEAREST.items():
        table = places.get(kind)
        if table is None or table.empty:
            result[indicator] = pd.Series(np.nan, index=cells)
            continue
        found = np.column_stack([table["Easting"].to_numpy(), table["Northing"].to_numpy()])
        result[indicator] = pd.Series(
            network.minutes_to_nearest(places=found, origins=origins), index=cells
        )
    return result
