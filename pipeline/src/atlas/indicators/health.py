"""The health care indicators that are walks: the minutes on foot to the nearest GP practice, and
the patients per GP of the practices within reach."""

import h3
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from atlas.datasets.countries.gb.code_point import normalise
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network


def site_places(sites: pd.DataFrame, postcodes: pd.DataFrame) -> np.ndarray:
    """The easting and northing of each site (a GP practice, a hospital), found from its
    `Postcode`. A site whose postcode is not in Code-Point Open is left out."""
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


gp_places = site_places


def ae_distance(places: np.ndarray, cells: list[str]) -> pd.Series:
    """The straight-line distance in kilometres from each cell's centre to the nearest A&E
    department. A straight line, because the evidence is in straight-line distance."""
    metres, _ = KDTree(places).query(cell_centres_bng(cells))
    return pd.Series(np.asarray(metres, dtype=float) / 1000.0, index=cells)


def ae_seed_postcodes(cells: list[str], postcodes: pd.DataFrame, resolution: int = 5) -> list[str]:
    """Postcodes to search the A&E departments from: the postcode nearest to the middle of each
    part of the region (the cells' parents at `resolution`), spaced as the search form wants."""
    parents = sorted({h3.cell_to_parent(c, resolution) for c in cells})
    centres = cell_centres_bng(parents)
    known = postcodes[["Easting", "Northing"]].to_numpy(dtype=float)
    _, nearest = KDTree(known).query(centres)
    names = {str(postcodes.index[i]) for i in np.atleast_1d(nearest)}
    return sorted(f"{name[:-3]} {name[-3:]}" for name in names)
