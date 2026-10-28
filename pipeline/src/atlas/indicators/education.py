"""The education indicators that are walks: the minutes on foot to the nearest primary school and
the nearest secondary school."""

import numpy as np
import pandas as pd

from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network


def school_minutes(
    network: Network, schools: pd.DataFrame, cells: list[str]
) -> dict[str, pd.Series]:
    """The walking minutes from each cell's centre to the nearest school of each phase, along
    streets and paths. `schools` has `Easting`, `Northing`, `primary` and `secondary` columns."""
    origins = cell_centres_bng(cells)
    result: dict[str, pd.Series] = {}
    for indicator, phase in (("primary-schools", "primary"), ("secondary-schools", "secondary")):
        chosen = schools.loc[schools[phase]]
        places = np.column_stack([chosen["Easting"].to_numpy(), chosen["Northing"].to_numpy()])
        minutes = network.minutes_to_nearest(places=places, origins=origins)
        result[indicator] = pd.Series(minutes, index=cells)
    return result
