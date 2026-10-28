"""Spike S6, step 2: how complete are Overture, OpenStreetMap and Foursquare places, and how far
do walks differ from straight lines?

Throwaway code, never imported by `atlas`. Run `s6_fetch.py` first. The ground truth for food is
the FSA's register of rated food businesses, which every business that serves food must join.
Run from `pipeline/` with `uv run python notebooks/s6_completeness.py`.
"""

import json
import random
import re
import time

import h3
import numpy as np
import pandas as pd
import requests
from pyproj import Transformer
from s2_crime_rates import london_cells, residents_by_area
from s6_fetch import fsa, osm, overture
from scipy.spatial import cKDTree

RADIUS = 100  # metres: a source place this close to a food business counts as the same place
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
TO_METRES = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
FOOT = "https://routing.openstreetmap.de/routed-foot/route/v1/foot"


def metres(frame: pd.DataFrame) -> np.ndarray:
    x, y = TO_METRES.transform(frame["lng"].to_numpy(), frame["lat"].to_numpy())
    return np.column_stack([x, y])


def tokens(name: object) -> frozenset[str]:
    if not isinstance(name, str):
        return frozenset()
    return frozenset(t for t in re.findall(r"[a-z0-9]+", name.lower()) if t not in STOP)


def same_name(a: frozenset[str], b: frozenset[str]) -> bool:
    return bool(a and b) and len(a & b) / min(len(a), len(b)) >= 0.5


def match(truth: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    """For each business in `truth`: a place in `source` within RADIUS, and one with its name."""
    if source.empty:
        return pd.DataFrame({"near": False, "named": False, "index": -1}, index=truth.index)
    tree = cKDTree(metres(source))
    near_lists = tree.query_ball_point(metres(truth), RADIUS)
    source_tokens = [tokens(n) for n in source["name"]]
    rows = []
    for name, found in zip(truth["name"], near_lists, strict=True):
        want = tokens(name)
        hit = next((i for i in found if same_name(want, source_tokens[i])), -1)
        rows.append({"near": bool(found), "named": hit >= 0, "index": hit})
    return pd.DataFrame(rows, index=truth.index)


def recall(truth: pd.DataFrame, source: pd.DataFrame) -> dict[str, float]:
    found = match(truth, source)
    moved = truth.assign(lng=truth["lng"] + 0.0045)  # about 300 m east: a place near by chance
    chance = match(moved, source)
    return {
        "a place within 100 m": round(float(found["near"].mean()), 3),
        "a place within 100 m, by chance": round(float(chance["near"].mean()), 3),
        "a place within 100 m with the same name": round(float(found["named"].mean()), 3),
    }


def main() -> None:
    food, everything, pois = fsa(), overture(), osm()
    places = everything[everything["operating_status"] != "permanently_closed"]
    result: dict[str, object] = {}

    eating_truth = food[food["type"].isin(["Restaurant/Cafe/Canteen", "Takeaway/sandwich shop"])]
    pub_truth = food[food["type"] == "Pub/bar/nightclub"]
    super_truth = food[food["type"] == "Retailers - supermarkets/hypermarkets"]
    drink = places["category"].fillna("").str.contains("bar|pub|lounge|brewery|nightclub")
    is_food = places["hierarchy"].map(
        lambda h: h is not None and len(h) > 0 and h[0] == "food_and_drink"
    )
    overture_sets = {
        "eating places": places[is_food & ~drink],
        "pubs and bars": places[drink],
        "supermarkets": places[
            places["category"].isin(["supermarket", "grocery_store", "convenience_store"])
        ],
    }
    osm_sets = {
        "eating places": pois[pois["amenity"].isin(["restaurant", "cafe", "fast_food"])],
        "pubs and bars": pois[pois["amenity"].isin(["pub", "bar"])],
        "supermarkets": pois[pois["shop"].isin(["supermarket", "convenience"])],
    }
    truth_sets = {
        "eating places": eating_truth,
        "pubs and bars": pub_truth,
        "supermarkets": super_truth,
    }

    for kind, truth in truth_sets.items():
        row: dict[str, object] = {"FSA businesses": len(truth)}
        row["OpenStreetMap"] = recall(truth, osm_sets[kind])
        row["Overture, every source"] = recall(truth, overture_sets[kind])
        has_fs = overture_sets[kind]["source_list"].map(
            lambda sources: "Foursquare" in list(sources)
        )
        row["Overture records with Foursquare among their sources"] = recall(
            truth, overture_sets[kind][has_fs]
        )
        row["Overture records without Foursquare"] = recall(truth, overture_sets[kind][~has_fs])
        union = pd.concat(
            [osm_sets[kind][["name", "lng", "lat"]], overture_sets[kind][["name", "lng", "lat"]]],
            ignore_index=True,
        )
        row["OpenStreetMap and Overture together"] = recall(truth, union)
        result[kind] = row

    # Which Overture dataset the matched places come from.
    found = match(eating_truth, overture_sets["eating places"].reset_index(drop=True))
    sources = overture_sets["eating places"].reset_index(drop=True)["source"]
    result["Overture eating places that match a food business, by the dataset of the record"] = (
        sources.iloc[found.loc[found["index"] >= 0, "index"]].value_counts().to_dict()
    )
    result["Overture eating places, by dataset"] = (
        overture_sets["eating places"]["source"].value_counts().to_dict()
    )

    # The other way round: places in a source that no food business is near.
    for label, source in (
        ("OpenStreetMap", osm_sets["eating places"]),
        ("Overture", overture_sets["eating places"]),
    ):
        back = match(
            source.reset_index(drop=True),
            pd.concat([eating_truth, pub_truth]).reset_index(drop=True),
        )
        result[f"{label} eating places with no FSA business within 100 m"] = round(
            float(1 - back["near"].mean()), 3
        )
    result["Overture places by operating status"] = (
        everything["operating_status"].value_counts().to_dict()
    )

    # Brand tags, on chains: names that at least 20 FSA businesses share.
    names = eating_truth["name"].map(lambda n: " ".join(sorted(tokens(n)))).value_counts()
    chains = set(names[(names >= 20) & (names.index != "")].index)
    chain_truth = eating_truth[
        eating_truth["name"].map(lambda n: " ".join(sorted(tokens(n))) in chains)
    ]
    result["chain names among the FSA's eating places"] = len(chains)
    result["FSA businesses with a chain name"] = len(chain_truth)
    for label, source, brand in (
        ("OpenStreetMap", osm_sets["eating places"].reset_index(drop=True), "brand"),
        ("Overture", overture_sets["eating places"].reset_index(drop=True), "brand"),
    ):
        hits = match(chain_truth, source)
        matched = hits[hits["index"] >= 0]
        has_brand = source[brand].notna().to_numpy()
        result[f"{label}: chain businesses found by name and place"] = round(
            float(hits["named"].mean()), 3
        )
        result[f"{label}: of those, share that carry a brand"] = round(
            float(has_brand[matched["index"]].mean()), 3
        )
        result[f"{label}: share of all its eating places with a brand"] = round(
            float(has_brand.mean()), 3
        )
    wikidata = osm_sets["eating places"]["brand:wikidata"].notna().mean()
    result["OpenStreetMap: eating places with a brand:wikidata tag"] = round(float(wikidata), 3)

    # Walking against the straight line.
    cells = london_cells()
    residents = residents_by_area(cells)
    homes = [h3.cell_to_latlng(c) for c in cells if residents.get(c, 0) >= 200]
    rng = random.Random(6)
    target = eating_truth.reset_index(drop=True)
    tree = cKDTree(metres(target))
    ratios = []
    for _ in range(400):
        if len(ratios) >= 150:
            break
        lat, lng = rng.choice(homes)
        x, y = TO_METRES.transform(lng, lat)
        near = [
            i
            for i in tree.query_ball_point([x, y], 1500)
            if np.hypot(*(tree.data[i] - [x, y])) >= 300
        ]
        if not near:
            continue
        pick = target.iloc[rng.choice(near)]
        line = float(np.hypot(*(tree.data[pick.name] - [x, y])))
        time.sleep(1.2)
        reply = requests.get(
            f"{FOOT}/{lng:.6f},{lat:.6f};{pick['lng']:.6f},{pick['lat']:.6f}",
            params={"overview": "false"},
            timeout=60,
        )
        if reply.status_code == 200 and reply.json().get("routes"):
            ratios.append(reply.json()["routes"][0]["distance"] / line)
    ratios_a = np.array(ratios)
    result["walking routes compared with the straight line"] = {
        "routes": len(ratios_a),
        "network distance over straight line, quantiles 5/25/50/75/95": np.quantile(
            ratios_a, [0.05, 0.25, 0.5, 0.75, 0.95]
        )
        .round(2)
        .tolist(),
        "mean": round(float(ratios_a.mean()), 2),
        "share of routes more than 1.5 times the straight line": round(
            float((ratios_a > 1.5).mean()), 3
        ),
    }
    print(json.dumps(result, indent=2, default=float))


if __name__ == "__main__":
    main()
