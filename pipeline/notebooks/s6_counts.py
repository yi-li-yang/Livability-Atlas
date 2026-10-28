"""Spike S6, step 3: how many cafés and restaurants lie within a 10-minute walk of a home?

Throwaway code, never imported by `atlas`. Pools OpenStreetMap and Overture (places Overture marks
permanently closed left out), counts those within 800 m of the centre of each homes cell, and
prints the spread. Run `s6_fetch.py` first.
Run from `pipeline/` with `uv run python notebooks/s6_counts.py`.
"""

import json

import h3
import numpy as np
import pandas as pd
from s2_crime_rates import london_cells, residents_by_area
from s6_completeness import TO_METRES, metres, same_name, tokens
from s6_fetch import osm, overture
from scipy.spatial import cKDTree

RADIUS = 800  # metres, a 10-minute walk at 4.8 km/h
DUPLICATE = (
    50  # an OpenStreetMap place this near to an Overture one of the same name is the same place
)


def pooled(overture_places: pd.DataFrame, osm_places: pd.DataFrame) -> pd.DataFrame:
    """Overture's places, plus OpenStreetMap's that Overture does not already have."""
    tree = cKDTree(metres(overture_places))
    names = [tokens(n) for n in overture_places["name"]]
    near = tree.query_ball_point(metres(osm_places), DUPLICATE)
    own = [tokens(n) for n in osm_places["name"]]
    new = [not any(same_name(own[k], names[i]) for i in found) for k, found in enumerate(near)]
    columns = ["name", "lng", "lat"]
    return pd.concat([overture_places[columns], osm_places[new][columns]], ignore_index=True)


def main() -> None:
    everything, pois = overture(), osm()
    places = everything[everything["operating_status"] != "permanently_closed"]
    category = places["category"].fillna("")
    is_cafe = category.str.contains("cafe|coffee|tea_room|bubble_tea")
    is_restaurant = category.str.contains("restaurant") & ~is_cafe
    cells = london_cells()
    residents = residents_by_area(cells)
    homes = np.array([h3.cell_to_latlng(c) for c in cells if residents.get(c, 0) >= 200])
    x, y = TO_METRES.transform(homes[:, 1], homes[:, 0])
    points = np.column_stack([x, y])
    result: dict[str, object] = {"homes cells": len(points)}
    result["cafés"] = spread_at(pooled(places[is_cafe], pois[pois["amenity"] == "cafe"]), points)
    result["restaurants"] = spread_at(
        pooled(places[is_restaurant], pois[pois["amenity"] == "restaurant"]), points
    )
    print(json.dumps(result, indent=2, default=float))


def spread_at(places: pd.DataFrame, points: np.ndarray) -> dict[str, object]:
    counts = np.array([len(f) for f in cKDTree(metres(places)).query_ball_point(points, RADIUS)])
    return {
        "places": len(places),
        "quantiles 5/25/50/75/95": np.quantile(counts, [0.05, 0.25, 0.5, 0.75, 0.95])
        .round(0)
        .tolist(),
        "cells with none": round(float((counts == 0).mean()), 3),
        "cells with 3 or fewer": round(float((counts <= 3).mean()), 3),
        "cells with 20 or more": round(float((counts >= 20).mean()), 3),
        "cells with 100 or more": round(float((counts >= 100).mean()), 3),
    }


if __name__ == "__main__":
    main()
