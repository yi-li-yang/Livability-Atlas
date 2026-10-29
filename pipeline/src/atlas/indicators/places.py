"""The places that the amenity indicators count, pooled from Overture and OpenStreetMap.

Neither source is complete, and together they find more (spike S6: 66% of the Food Standards
Agency's cafés, restaurants and takeaways, and 76% of its supermarkets and convenience shops, as
lower bounds). A place that both list counts once: an OpenStreetMap place is the same as an
Overture one of its kind when it is within 50 m and their names share at least half of the shorter
name's words. Places are placed in metres of British National Grid.
"""

import re

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import KDTree

DUPLICATE = 50.0  # metres
STOP = {
    "the",
    "and",
    "ltd",
    "limited",
    "restaurant",
    "cafe",
    "bar",
    "pub",
    "london",
    "uk",
    "co",
    "of",
}
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

# Overture's categories of each kind of place.
GROCERY = {"supermarket", "grocery_store", "convenience_store", "greengrocer"}
OVERTURE_KINDS = {
    "pharmacy": {"pharmacy", "drugstore"},
    "gym": {"gym", "boxing_gym", "rock_climbing_gym"},
    "library": {"library"},
    "cafe": {"cafe", "coffee_shop", "tea_room", "bubble_tea_shop"},
}
# Restaurants whose category names no cuisine.
GENERIC_RESTAURANTS = {"restaurant", "fast_food_restaurant"}

# OpenStreetMap's tag of each kind of place: key, then value.
OSM_KINDS = {
    ("shop", "supermarket"): "grocery",
    ("shop", "convenience"): "grocery",
    ("shop", "greengrocer"): "grocery",
    ("amenity", "pharmacy"): "pharmacy",
    ("leisure", "fitness_centre"): "gym",
    ("amenity", "library"): "library",
    ("amenity", "cafe"): "cafe",
    ("amenity", "restaurant"): "restaurant",
    ("amenity", "fast_food"): "restaurant",
}


def _overture_kind(category: object) -> str | None:
    if not isinstance(category, str):
        return None
    if category in GROCERY or category.endswith("_grocery_store"):
        return "grocery"
    if category == "restaurant" or category.endswith("_restaurant"):
        return "restaurant"
    return next((kind for kind, names in OVERTURE_KINDS.items() if category in names), None)


def _overture_cuisine(category: str) -> str | None:
    if category in GENERIC_RESTAURANTS or not category.endswith("_restaurant"):
        return None
    return category.removesuffix("_restaurant")


def _osm_cuisine(tag: object) -> str | None:
    if not isinstance(tag, str) or not tag.strip():
        return None
    first = tag.split(";")[0].strip().lower().replace(" ", "_")
    return first or None


def tokens(name: object) -> frozenset[str]:
    """The words of a name that tell places apart."""
    if not isinstance(name, str):
        return frozenset()
    return frozenset(t for t in re.findall(r"[a-z0-9]+", name.lower()) if t not in STOP)


def same_name(a: frozenset[str], b: frozenset[str]) -> bool:
    return bool(a and b) and len(a & b) / min(len(a), len(b)) >= 0.5


def _metres(lng: np.ndarray, lat: np.ndarray) -> np.ndarray:
    x, y = _TO_BNG.transform(lng, lat)
    return np.column_stack([x, y])


def pool(overture: pd.DataFrame, osm: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The places of each kind, from both sources, as tables with `Easting`, `Northing`, `name` and
    `cuisine` (restaurants only; missing where unknown). Kinds with no place are left out."""
    rows = []
    for source, frame in (("overture", overture), ("osm", osm)):
        if frame.empty:
            continue
        if source == "overture":
            kinds = [_overture_kind(c) for c in frame["category"]]
            cuisine = [
                _overture_cuisine(c) if isinstance(c, str) else None for c in frame["category"]
            ]
            name = frame["name"]
        else:
            kinds = pd.Series([None] * len(frame), index=frame.index, dtype=object)
            for (key, value), kind in OSM_KINDS.items():
                kinds = kinds.mask(frame[key] == value, kind)
            cuisine = [_osm_cuisine(c) for c in frame["cuisine"]]
            name = frame["name"].where(frame["name"].notna(), frame["brand"])
        xy = _metres(frame["lng"].to_numpy(dtype=float), frame["lat"].to_numpy(dtype=float))
        rows.append(
            pd.DataFrame(
                {
                    "kind": kinds,
                    "name": name.to_numpy(),
                    "cuisine": cuisine,
                    "Easting": xy[:, 0],
                    "Northing": xy[:, 1],
                    "source": source,
                }
            )
        )
    if not rows:
        return {}
    every = pd.concat(rows, ignore_index=True)
    every = every.loc[every["kind"].notna()]
    return {
        str(kind): _without_duplicates(every.loc[every["kind"] == kind].reset_index(drop=True))
        for kind in sorted(every["kind"].unique())
    }


def _without_duplicates(group: pd.DataFrame) -> pd.DataFrame:
    """The places of one kind, with each OpenStreetMap place that an Overture place already lists
    left out. The Overture place borrows its cuisine if it has none."""
    source = group["source"].to_numpy()
    first, second = np.flatnonzero(source == "overture"), np.flatnonzero(source == "osm")
    cuisine = [c if isinstance(c, str) else None for c in group["cuisine"]]
    xy = np.column_stack([group["Easting"].to_numpy(), group["Northing"].to_numpy()])
    names = [tokens(n) for n in group["name"]]
    drop = np.zeros(len(group), dtype=bool)
    if len(first) and len(second):
        tree = KDTree(xy[first])
        for j, near in zip(second, tree.query_ball_point(xy[second], DUPLICATE), strict=True):
            twin = next((int(first[i]) for i in near if same_name(names[j], names[first[i]])), None)
            if twin is None:
                continue
            drop[j] = True
            if cuisine[twin] is None:
                cuisine[twin] = cuisine[j]
    keep = ~drop
    return pd.DataFrame(
        {
            "Easting": xy[keep, 0],
            "Northing": xy[keep, 1],
            "name": np.array(group["name"].tolist(), dtype=object)[keep],
            "cuisine": np.array(cuisine, dtype=object)[keep],
        }
    )
