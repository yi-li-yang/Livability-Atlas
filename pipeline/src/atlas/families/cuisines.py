"""Daily amenities: the cuisines a user can choose (`your-cuisines`, D19).

For each cuisine that enough restaurants serve, the minutes on foot from each cell to the nearest
restaurant of that cuisine, from Overture's places and OpenStreetMap's pooled. A cell scores the
best of the cuisines the user picks. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np

from atlas.datasets.world import openstreetmap
from atlas.families import Context, Family
from atlas.indicators import places as place_pool
from atlas.publish.bundle import Choice
from atlas.spatial.grid import cell_centres_bng

# A walk is kept to a tenth of a minute: it is a table with few distinct values, which compresses
# to a fifth of what the long decimals take, and 6 seconds is finer than the walk can be known.
MIN_PLACES = 100  # fewer restaurants than this give too thin a picture to offer the cuisine
NOT_A_CUISINE = {"bar_and_grill"}  # a kind of place, not a way of cooking
SMALL_WORDS = {"and", "or", "of"}


def name_of(cuisine: str) -> str:
    """The cuisine as the picker shows it, in title case: "Sri Lankan", "Fish and Chips"."""
    words = cuisine.split("_")
    return " ".join(w if i and w in SMALL_WORDS else w.capitalize() for i, w in enumerate(words))


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    return {}


def choices(ctx: Context) -> dict[str, list[Choice]]:
    found = place_pool.pool(ctx.overture, openstreetmap.places(ctx.data_dir, ctx.region_id))
    restaurants = found.get("restaurant")
    if restaurants is None or restaurants.empty:
        return {"your-cuisines": []}
    origins = cell_centres_bng(ctx.cells)
    options = []
    for cuisine, group in sorted(restaurants.dropna(subset=["cuisine"]).groupby("cuisine")):
        if str(cuisine) in NOT_A_CUISINE or len(group) < MIN_PLACES:
            continue
        xy = np.column_stack([group["Easting"].to_numpy(), group["Northing"].to_numpy()])
        minutes = ctx.network.minutes_to_nearest(places=xy, origins=origins)
        options.append(
            Choice(
                id=str(cuisine),
                name=name_of(str(cuisine)),
                group="Cuisine",
                values=[None if np.isnan(m) else round(float(m), 1) for m in minutes],
            )
        )
    return {"your-cuisines": options}


FAMILY = Family("cuisines", columns, choices=choices)
