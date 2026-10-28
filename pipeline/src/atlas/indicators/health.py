"""The health care indicators that are walks: the minutes on foot to the nearest GP practice."""

import numpy as np
import pandas as pd

from atlas.datasets.countries.gb.code_point import normalise
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network


def gp_places(sites: pd.DataFrame, postcodes: pd.DataFrame) -> np.ndarray:
    """The easting and northing of each GP site, found from its postcode. A site whose postcode
    is not in Code-Point Open is left out."""
    keys = pd.Index([normalise(p) for p in sites["Postcode"]])
    found = postcodes.reindex(keys).dropna()
    return found[["Easting", "Northing"]].to_numpy(dtype=float)


def gp_minutes(network: Network, places: np.ndarray, cells: list[str]) -> pd.Series:
    """The walking minutes from each cell's centre to the nearest GP site, along streets and
    paths."""
    minutes = network.minutes_to_nearest(places=places, origins=cell_centres_bng(cells))
    return pd.Series(minutes, index=cells)
