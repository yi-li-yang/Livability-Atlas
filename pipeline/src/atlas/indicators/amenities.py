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


WALK_MINUTES = 10  # a walk of 800 m at 4.8 km/h, the distance CIHT calls acceptable
# The catalogue's indicator for the kind of place that it counts within a walk.
COUNTED = {"cafes": "cafe", "restaurant-choice": "restaurant"}
# The places within a walk of each cell: for each name, the indexes of the places in reach, by cell.
Reach = dict[str, list[np.ndarray]]


def _points(table: pd.DataFrame) -> np.ndarray:
    return np.column_stack([table["Easting"].to_numpy(), table["Northing"].to_numpy()])


def reach_of(network: Network, groups: dict[str, pd.DataFrame], cells: list[str]) -> Reach:
    """For each named table of places, the places within a 10-minute walk of each cell's centre.
    The street searches are shared by all the tables."""
    names = [name for name, table in groups.items() if not table.empty]
    found = network.groups_within(
        [_points(groups[name]) for name in names], cell_centres_bng(cells), WALK_MINUTES
    )
    return dict(zip(names, found, strict=True))


def counts_within_a_walk(
    network: Network, places: dict[str, pd.DataFrame], cells: list[str], reach: Reach | None = None
) -> dict[str, pd.Series]:
    """The number of places of each counted kind within a 10-minute walk of each cell's centre.
    `reach` holds the places in reach by kind, if already worked out with `reach_of`."""
    reach = reach if reach is not None else reach_of(network, places, cells)
    return {
        indicator: pd.Series([len(r) for r in reach[kind]], index=cells)
        if kind in reach
        else pd.Series(0, index=cells)
        for indicator, kind in COUNTED.items()
    }


def cuisine_variety(
    network: Network, places: dict[str, pd.DataFrame], cells: list[str], reach: Reach | None = None
) -> pd.Series:
    """The number of different cuisines among the restaurants within a 10-minute walk of each
    cell's centre. A restaurant whose cuisine is unknown counts for none."""
    reach = (
        reach
        if reach is not None
        else reach_of(network, {"restaurant": places.get("restaurant", pd.DataFrame())}, cells)
    )
    if "restaurant" not in reach:
        return pd.Series(0, index=cells)
    cuisine = np.array(
        [c if isinstance(c, str) else "" for c in places["restaurant"]["cuisine"]], dtype=object
    )
    return pd.Series([len({c for c in cuisine[r] if c}) for r in reach["restaurant"]], index=cells)


GOOD_RATING = 4  # the Food Hygiene Rating Scheme's "good"; 5 is "very good"
MIN_RATED = 5  # fewer rated businesses in reach than this say little about a share


def good_hygiene_share(
    network: Network, ratings: pd.DataFrame, cells: list[str], reach: Reach | None = None
) -> pd.Series:
    """The percentage of rated food businesses within a 10-minute walk of each cell's centre that
    are rated 4 or 5. A cell with fewer than five rated businesses in reach has no value. `reach`
    holds the businesses in reach under the name `ratings`, if worked out with `reach_of`."""
    reach = reach if reach is not None else reach_of(network, {"ratings": ratings}, cells)
    good = ratings["rating"].to_numpy() >= GOOD_RATING
    share = [
        100.0 * float(good[r].mean()) if len(r) >= MIN_RATED else np.nan
        for r in reach.get("ratings", [np.empty(0, dtype=np.int64)] * len(cells))
    ]
    return pd.Series(share, index=cells)
