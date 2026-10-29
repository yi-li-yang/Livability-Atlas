"""The health care indicators that are walks: the minutes on foot to the nearest GP practice, and
the patients per GP of the practices within reach."""

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


def located_practices(practices: pd.DataFrame, postcodes: pd.DataFrame) -> pd.DataFrame:
    """The practices (`nhs_gp.read_practices`) with the `Easting` and `Northing` of their
    postcode. A practice whose postcode is not in Code-Point Open is left out."""
    keys = pd.Index([normalise(p) for p in practices["Postcode"]])
    places = postcodes[["Easting", "Northing"]].reindex(keys)
    places.index = practices.index
    return practices.join(places).dropna(subset=["Easting", "Northing"])


def patients_per_gp(
    network: Network,
    places: np.ndarray,
    patients: np.ndarray,
    gps: np.ndarray,
    cells: list[str],
    minutes: float = 15.0,
) -> pd.Series:
    """The registered patients of the practices within a walk of each cell's centre, over their
    full-time fully qualified GPs. `places`, `patients` and `gps` have a row for each practice.
    A cell with no practice in reach, or whose practices have no GP, has no value."""
    reach = network.places_within(places, cell_centres_bng(cells), minutes)
    ratio = np.full(len(cells), np.nan)
    for position, found in enumerate(reach):
        total_gps = gps[found].sum()
        if len(found) and total_gps > 0:
            ratio[position] = patients[found].sum() / total_gps
    return pd.Series(ratio, index=cells)
