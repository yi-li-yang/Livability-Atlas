"""Spike S8: do the open food signals work for London, and do brand groups track house prices?

Throwaway code, never imported by `atlas`. Tests, in each homes cell, the food hygiene share,
cuisine variety from OpenStreetMap tags and from Overture's categories, independents (places with
no brand tag) against chains known from the FSA register, and brand groups against sale prices.
Michelin recognition comes from a Wikidata query. Needs what S1 to S3 and S6 need.
Run from `pipeline/` with `uv run python notebooks/s8_food_signals.py`.
"""

import json
import re

import h3
import numpy as np
import pandas as pd
import requests
from s2_crime_rates import london_cells, residents_by_area
from s3_sales_and_rents import postcodes, sales
from s6_completeness import TO_METRES, metres, tokens
from s6_fetch import fsa, osm, overture
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

WALK = 800  # metres, a 10-minute walk
SUPERMARKET_WALK = 1200  # the 15-minute walk the catalogue uses for the nearest shop
LAST_24 = "2024-10-01"
GROUPS = {
    "premium": ["waitrose", "gail"],
    "high footfall": ["pret a manger", "starbucks"],
    "value": ["aldi", "lidl"],
    "large catchment": ["costco", "ikea"],
}
KNOWN_STARRED = ["gordon ramsay", "core by clare smyth", "clove club", "dinner by heston"]
SAMPLE = {
    "Soho": (51.5136, -0.1337),
    "Brick Lane": (51.5215, -0.0715),
    "Orpington": (51.3743, 0.1000),
    "Chigwell": (51.6190, 0.0750),
    "Edgware": (51.6140, -0.2750),
}
GENERIC = {"restaurant", "fast_food_restaurant", "casual_eatery"}


def home_points() -> np.ndarray:
    cells = london_cells()
    residents = residents_by_area(cells)
    homes = np.array([h3.cell_to_latlng(c) for c in cells if residents.get(c, 0) >= 200])
    x, y = TO_METRES.transform(homes[:, 1], homes[:, 0])
    return np.column_stack([x, y])


def within(places: pd.DataFrame, points: np.ndarray, radius: int) -> list[list[int]]:
    return cKDTree(metres(places)).query_ball_point(points, radius)


def hygiene(food: pd.DataFrame, points: np.ndarray) -> dict[str, object]:
    rated = food[food["rating"].isin(list("012345"))].copy()
    rated["good"] = rated["rating"].isin(["4", "5"])
    found = within(rated, points, WALK)
    good = rated["good"].to_numpy()
    counts = np.array([len(f) for f in found])
    share = np.array([good[f].mean() if len(f) >= 10 else np.nan for f in found])
    ok = ~np.isnan(share)
    return {
        "rated food businesses": len(rated),
        "rated 4 or 5": round(float(rated["good"].mean()), 3),
        "rated 5": round(float((rated["rating"] == "5").mean()), 3),
        "awaiting inspection": int((food["rating"] == "AwaitingInspection").sum()),
        "homes cells with 10 or more rated businesses within 800 m": round(
            float((counts >= 10).mean()), 3
        ),
        "share rated 4 or 5 within 800 m, quantiles 5/25/50/75/95": np.quantile(
            share[ok], [0.05, 0.25, 0.5, 0.75, 0.95]
        )
        .round(3)
        .tolist(),
        "cells where the share is under 70%": round(float((share[ok] < 0.7).mean()), 3),
    }


def cuisines(pois: pd.DataFrame, places: pd.DataFrame, points: np.ndarray) -> dict[str, object]:
    restaurants = pois[pois["amenity"] == "restaurant"].reset_index(drop=True)
    tagged = restaurants["cuisine"].notna()
    cuisine_lists = [
        set(re.split(r"[;,]", str(c).lower().replace(" ", ""))) if t else set()
        for c, t in zip(restaurants["cuisine"], tagged, strict=True)
    ]
    category = places["category"].fillna("")
    overture_restaurants = places[
        category.str.contains("restaurant") & ~category.isin({"fast_food_restaurant"})
    ].reset_index(drop=True)
    kind = overture_restaurants["category"].where(
        overture_restaurants["category"].str.endswith("_restaurant")
    )
    kind = kind.where(~kind.isin(GENERIC))
    kind_lists = [{k.removesuffix("_restaurant")} if isinstance(k, str) else set() for k in kind]
    osm_found, overture_found = (
        within(restaurants, points, WALK),
        within(overture_restaurants, points, WALK),
    )
    osm_variety = np.array(
        [len(set().union(*[cuisine_lists[i] for i in f])) if f else 0 for f in osm_found]
    )
    overture_variety = np.array(
        [len(set().union(*[kind_lists[i] for i in f])) if f else 0 for f in overture_found]
    )
    result: dict[str, object] = {
        "OpenStreetMap restaurants": len(restaurants),
        "of them with a cuisine tag": round(float(tagged.mean()), 3),
        "Overture restaurants": len(overture_restaurants),
        "of them with a specific cuisine category": round(float(kind.notna().mean()), 3),
        "distinct cuisines in OpenStreetMap's tags": len(set().union(*cuisine_lists)),
        "distinct cuisines in Overture's categories": len(set().union(*kind_lists)),
        "cuisines within 800 m, OpenStreetMap, quantiles 5/50/95": np.quantile(
            osm_variety, [0.05, 0.5, 0.95]
        ).tolist(),
        "cuisines within 800 m, Overture, quantiles 5/50/95": np.quantile(
            overture_variety, [0.05, 0.5, 0.95]
        ).tolist(),
        "rank correlation of the two varieties across homes cells": round(
            float(spearmanr(osm_variety, overture_variety)[0]), 3
        ),
        "cells with no cuisine at all: OpenStreetMap, Overture": [
            round(float((osm_variety == 0).mean()), 3),
            round(float((overture_variety == 0).mean()), 3),
        ],
    }
    known: dict[str, object] = {}
    for name, (lat, lng) in SAMPLE.items():
        x, y = TO_METRES.transform(lng, lat)
        point = np.array([[x, y]])
        o = within(restaurants, point, WALK)[0]
        v = within(overture_restaurants, point, WALK)[0]
        known[name] = [
            len(set().union(*[cuisine_lists[i] for i in o])) if o else 0,
            len(set().union(*[kind_lists[i] for i in v])) if v else 0,
        ]
    result["cuisines within 800 m at known places (OpenStreetMap, Overture)"] = known
    return result


def michelin() -> dict[str, object]:
    query = """
    SELECT DISTINCT ?item ?itemLabel ?awardLabel WHERE {
      ?item wdt:P166 ?award . ?award rdfs:label ?l .
      FILTER(LANG(?l) = "en" && CONTAINS(LCASE(?l), "michelin"))
      ?item wdt:P131* wd:Q84 .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }"""
    reply = requests.get(
        "https://query.wikidata.org/sparql",
        params={"query": query, "format": "json"},
        headers={"User-Agent": "LivabilityAtlas-spike/0.1 (research)"},
        timeout=120,
    )
    rows = reply.json()["results"]["bindings"]
    names = sorted({r["itemLabel"]["value"] for r in rows})
    lower = [n.lower() for n in names]
    return {
        "London items with a Michelin award in Wikidata": len(names),
        "known starred restaurants found": {k: any(k in n for n in lower) for k in KNOWN_STARRED},
        "award labels": sorted({r["awardLabel"]["value"] for r in rows}),
    }


def independents(
    food: pd.DataFrame, pois: pd.DataFrame, places: pd.DataFrame, points: np.ndarray
) -> dict[str, object]:
    eating = food[
        food["type"].isin(["Restaurant/Cafe/Canteen", "Takeaway/sandwich shop"])
    ].reset_index(drop=True)
    key = eating["name"].map(lambda n: " ".join(sorted(tokens(n))))
    counts = key.value_counts()
    chains = set(counts[(counts >= 20) & (counts.index != "")].index)
    is_chain = key.isin(chains).to_numpy()
    found = within(eating, points, WALK)
    fsa_chain = np.array([is_chain[f].mean() if len(f) >= 10 else np.nan for f in found])

    pool = pd.concat(
        [
            pois[pois["amenity"].isin(["restaurant", "cafe", "fast_food"])][
                ["lng", "lat", "brand"]
            ],
            places[
                places["hierarchy"].map(
                    lambda h: h is not None and len(h) > 0 and h[0] == "food_and_drink"
                )
            ][["lng", "lat", "brand"]],
        ],
        ignore_index=True,
    ).reset_index(drop=True)
    branded = pool["brand"].notna().to_numpy()
    near = within(pool, points, WALK)
    tag_chain = np.array([branded[f].mean() if len(f) >= 10 else np.nan for f in near])
    ok = ~np.isnan(fsa_chain) & ~np.isnan(tag_chain)
    return {
        "chain names (20 or more FSA eating places)": len(chains),
        "FSA eating places with a chain name": round(float(is_chain.mean()), 3),
        "places in OpenStreetMap and Overture with a brand tag": round(float(branded.mean()), 3),
        "chain share within 800 m, from the FSA's names, quantiles 5/50/95": np.nanquantile(
            fsa_chain, [0.05, 0.5, 0.95]
        )
        .round(3)
        .tolist(),
        "chain share within 800 m, from brand tags, quantiles 5/50/95": np.nanquantile(
            tag_chain, [0.05, 0.5, 0.95]
        )
        .round(3)
        .tolist(),
        "rank correlation of the two chain shares": round(
            float(spearmanr(fsa_chain[ok], tag_chain[ok])[0]), 3
        ),
    }


def brands_and_prices(
    pois: pd.DataFrame, places: pd.DataFrame, points: np.ndarray
) -> dict[str, object]:
    cells = london_cells()
    residents = residents_by_area(cells)
    homes = [c for c in cells if residents.get(c, 0) >= 200]
    codes = postcodes().drop_duplicates("postcode")
    sold = sales().merge(codes, on="postcode", how="inner")
    sold = sold[sold["date"] >= LAST_24]
    by_cell = {c: g["price"].to_numpy() for c, g in sold.groupby("cell")}
    price = np.array(
        [
            np.median(
                np.concatenate(
                    [by_cell[c] for c in h3.grid_disk(cell, 2) if c in by_cell]
                    or [np.array([np.nan])]
                )
            )
            for cell in homes
        ]
    )
    named = pd.concat(
        [
            pois[["lng", "lat", "name", "brand"]],
            places[["lng", "lat", "name", "brand"]],
        ],
        ignore_index=True,
    )
    text = (named["name"].fillna("") + " " + named["brand"].fillna("")).str.lower()
    result: dict[str, object] = {"homes cells with a sale price": int((~np.isnan(price)).sum())}
    ok = ~np.isnan(price)
    presence: dict[str, np.ndarray] = {}
    for group, brands in GROUPS.items():
        for brand in brands:
            hit = named[text.str.contains(rf"\b{re.escape(brand)}\b", regex=True)].reset_index(
                drop=True
            )
            if hit.empty:
                continue
            near = within(hit, points, SUPERMARKET_WALK)
            present = np.array([len(f) > 0 for f in near], dtype=float)
            presence[brand] = present
            result[f"{group}: {brand}"] = {
                "places": len(hit),
                "homes cells with one within 1.2 km": round(float(present.mean()), 3),
                "rank correlation of presence with the median price nearby": round(
                    float(spearmanr(present[ok], price[ok])[0]), 3
                )
                if present[ok].std() > 0
                else None,
            }
    for group, brands in GROUPS.items():
        stack = [presence[b] for b in brands if b in presence]
        if stack:
            any_present = np.max(stack, axis=0)
            result[f"{group}, any of its brands"] = {
                "homes cells with one within 1.2 km": round(float(any_present.mean()), 3),
                "rank correlation with the median price nearby": round(
                    float(spearmanr(any_present[ok], price[ok])[0]), 3
                )
                if any_present[ok].std() > 0
                else None,
            }
    return result


def main() -> None:
    points = home_points()
    food, everything, pois = fsa(), overture(), osm()
    places = everything[everything["operating_status"] != "permanently_closed"]
    result = {
        "homes cells": len(points),
        "hygiene": hygiene(food, points),
        "cuisine variety": cuisines(pois, places, points),
        "guide recognition: Michelin in Wikidata": michelin(),
        "independents": independents(food, pois, places, points),
        "brand groups against sale prices": brands_and_prices(pois, places, points),
    }
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
