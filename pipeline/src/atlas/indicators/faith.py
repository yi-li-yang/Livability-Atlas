"""The faith indicator: the minutes on foot to the nearest place of worship of a religion.

Places of worship come from OpenStreetMap, which records the religion of a place. Spike S6 checks
how complete the tags are. A place that records several religions counts for each, and a place
that records none counts for none. A region offers the religions that have enough places.
"""

import numpy as np
import pandas as pd

from atlas.indicators.places import to_metres
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

MIN_PLACES = 10  # fewer places than this give too thin a picture to offer the religion
NAMES = {"bahai": "Bahai"}
NOT_A_FAITH = {"multifaith"}  # a prayer room for any faith: no one picks it as theirs


def name_of(religion: str) -> str:
    """The religion as the picker shows it."""
    return NAMES.get(religion, religion.replace("_", " ").title())


def places_of_worship(osm: pd.DataFrame, minimum: int = MIN_PLACES) -> dict[str, np.ndarray]:
    """The easting and northing of the places of each religion that has at least `minimum`
    places, keyed by the religion as OpenStreetMap writes it."""
    worship = osm.loc[(osm["amenity"] == "place_of_worship") & osm["religion"].notna()]
    xy = to_metres(worship["lng"].to_numpy(dtype=float), worship["lat"].to_numpy(dtype=float))
    by_religion: dict[str, list[int]] = {}
    for position, tag in enumerate(worship["religion"]):
        for religion in str(tag).split(";"):
            by_religion.setdefault(religion.strip(), []).append(position)
    return {
        religion: xy[rows]
        for religion, rows in sorted(by_religion.items())
        if religion and religion not in NOT_A_FAITH and len(rows) >= minimum
    }


def faith_minutes(
    network: Network, places: dict[str, np.ndarray], cells: list[str]
) -> dict[str, pd.Series]:
    """The walking minutes from each cell's centre to the nearest place of each religion, along
    streets and paths."""
    origins = cell_centres_bng(cells)
    return {
        religion: pd.Series(network.minutes_to_nearest(places=xy, origins=origins), index=cells)
        for religion, xy in places.items()
    }
