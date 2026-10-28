"""Spike S7: does the culture evidence ladder work on a sample of neighbourhoods?

Throwaway code, never imported by `atlas`. It measures four rungs of the ladder in
docs/methodology/hard-to-measure.md at twelve places, and checks one known fact for each rung.
Needs `data/raw/cim/cim.gpkg`, the GLA's Cultural Infrastructure Map. It calls
planning.data.gov.uk (listed buildings, conservation areas), the Wikipedia geosearch API and the
Wikimedia page views API, slowly, and caches the answers.
Run from `pipeline/` with `uv run python notebooks/s7_culture_ladder.py`.
"""

import json
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import requests
from pyproj import Transformer
from shapely.geometry import Point

from atlas.paths import data_dir

RAW = data_dir() / "raw"
CACHE = data_dir() / "interim" / "s7_cache.json"
AGENT = {
    "User-Agent": "LivabilityAtlas-spike/0.1 (research; https://github.com/yi-li-yang/Livability-Atlas)"
}
WALK = 800  # metres, a 10-minute walk
WIKI_RADIUS = 1000
PLACES = {
    "Soho": (51.5136, -0.1337, "centre"),
    "South Bank": (51.5055, -0.1160, "centre"),
    "Shoreditch": (51.5246, -0.0780, "centre"),
    "Camden Town": (51.5392, -0.1426, "centre"),
    "Brixton": (51.4613, -0.1156, "centre"),
    "Greenwich": (51.4826, -0.0077, "centre"),
    "Orpington": (51.3743, 0.1000, "suburb"),
    "Chigwell": (51.6190, 0.0750, "suburb"),
    "Edgware": (51.6140, -0.2750, "suburb"),
    "Sutton": (51.3618, -0.1945, "suburb"),
    "Hayes, Bromley": (51.3768, 0.0100, "suburb"),
    "Upminster": (51.5590, 0.2510, "suburb"),
}
# The kinds of venue that the ladder's example lists for the direct rung.
LISTED_KINDS = {
    "Theatres",
    "Music_venues_all",
    "Commercial_galleries",
    "Museums_and_public_galleries",
    "Cinemas",
    "Libraries",
    "Arts_centres",
    "Dance_performance_venues",
}
IGNORED = {
    "Pubs",
    "Listed_buildings",
    "Heritage_at_risk",
}  # pubs are not culture here, and the last two are character
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
TO_WGS = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


class Cache:
    def __init__(self) -> None:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, object] = (
            json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        )

    def get(self, key: str, fetch):
        if key not in self.data:
            self.data[key] = fetch()
            CACHE.write_text(json.dumps(self.data), encoding="utf-8")
            time.sleep(0.4)
        return self.data[key]


def venues() -> gpd.GeoDataFrame:
    path = RAW / "cim" / "cim.gpkg"
    layers = [name for name, _ in pyogrio.list_layers(path)]
    frames = []
    for layer in layers:
        frame = pyogrio.read_dataframe(path, layer=layer)[["name", "geometry"]]
        frame["kind"] = layer
        frames.append(frame)
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs="EPSG:27700")


def polygon_wkt(lat: float, lng: float) -> str:
    x, y = TO_BNG.transform(lng, lat)
    circle = Point(x, y).buffer(WALK, 32)
    wgs = [TO_WGS.transform(px, py) for px, py in circle.exterior.coords]
    return "POLYGON((" + ",".join(f"{a:.6f} {b:.6f}" for a, b in wgs) + "))"


def planning(dataset: str, geometry: str, relation: str, cache: Cache) -> int:
    def fetch() -> int:
        total, offset = 0, 0
        while True:
            reply = requests.get(
                "https://www.planning.data.gov.uk/entity.json",
                headers=AGENT,
                timeout=90,
                params={
                    "dataset": dataset,
                    "geometry": geometry,
                    "geometry_relation": relation,
                    "limit": 500,
                    "offset": offset,
                },
            ).json()
            got = len(reply.get("entities", []))
            total += got
            if got < 500:
                return total
            offset += 500

    return int(cache.get(f"{dataset}|{relation}|{geometry}", fetch))


def wikipedia(lat: float, lng: float, cache: Cache) -> list[str]:
    def fetch() -> list[str]:
        reply = requests.get(
            "https://en.wikipedia.org/w/api.php",
            headers=AGENT,
            timeout=60,
            params={
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{lat}|{lng}",
                "gsradius": WIKI_RADIUS,
                "gslimit": 500,
                "format": "json",
            },
        ).json()
        return [item["title"] for item in reply["query"]["geosearch"]]

    return cache.get(f"wiki|{lat}|{lng}", fetch)  # type: ignore[return-value]


def monthly_views(title: str, cache: Cache) -> float:
    def fetch() -> float:
        slug = requests.utils.quote(title.replace(" ", "_"), safe="")
        url = (
            "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
            f"{slug}/monthly/20250101/20251201"
        )
        reply = requests.get(url, headers=AGENT, timeout=60)
        if reply.status_code != 200:
            return 0.0
        return float(np.mean([item["views"] for item in reply.json()["items"]]))

    return float(cache.get(f"views|{title}", fetch))


def main() -> None:
    cache = Cache()
    points = venues()
    rows = []
    for name, (lat, lng, group) in PLACES.items():
        x, y = TO_BNG.transform(lng, lat)
        near = points[points.geometry.distance(Point(x, y)) <= WALK]
        counted = near[~near["kind"].isin(IGNORED)]
        titles = wikipedia(lat, lng, cache)
        views = sum(monthly_views(t, cache) for t in titles[:20])
        rows.append(
            {
                "place": name,
                "group": group,
                "direct: venues of the example kinds within 800 m": int(
                    near["kind"].isin(LISTED_KINDS).sum()
                ),
                "variety: kinds of venue within 800 m": int(counted["kind"].nunique()),
                "character: listed buildings within 800 m": planning(
                    "listed-building", polygon_wkt(lat, lng), "intersects", cache
                ),
                "character: in a conservation area": planning(
                    "conservation-area", f"POINT({lng} {lat})", "intersects", cache
                )
                > 0,
                "activity: Wikipedia articles within 1 km": len(titles),
                "activity: monthly views of the 20 nearest articles": round(views),
            }
        )
    table = pd.DataFrame(rows).set_index("place")
    print(table.to_string())

    c, s = table[table["group"] == "centre"], table[table["group"] == "suburb"]
    direct, variety = table.columns[1], table.columns[2]
    listed, conservation, articles, views_col = (
        table.columns[3],
        table.columns[4],
        table.columns[5],
        table.columns[6],
    )
    checks = {
        "direct: Soho has more venues than any suburb": bool(
            table.loc["Soho", direct] > s[direct].max()
        ),
        "direct: South Bank has at least 5 times the median suburb's venues": bool(
            table.loc["South Bank", direct] >= 5 * max(1, s[direct].median())
        ),
        "variety: Soho has at least 3 more kinds than the median suburb": bool(
            table.loc["Soho", variety] >= s[variety].median() + 3
        ),
        "variety: every centre has more kinds than the median suburb": bool(
            (c[variety] > s[variety].median()).all()
        ),
        "character: Greenwich has more listed buildings than every suburb": bool(
            table.loc["Greenwich", listed] > s[listed].max()
        ),
        "character: Greenwich is in a conservation area": bool(
            table.loc["Greenwich", conservation]
        ),
        "activity: Soho has more Wikipedia articles than any suburb": bool(
            table.loc["Soho", articles] > s[articles].max()
        ),
        "activity: the centres' views of nearby articles exceed the suburbs'": bool(
            c[views_col].median() > s[views_col].median()
        ),
    }
    print(json.dumps(checks, indent=2))
    numeric = table.drop(columns=["group", conservation])
    print("rank correlations between rungs:")
    print(numeric.rank().corr(method="spearman").round(2).to_string())
    print("centres' median against suburbs' median:")
    print(
        pd.DataFrame(
            {
                "centres": c.drop(columns=["group", conservation]).median(),
                "suburbs": s.drop(columns=["group", conservation]).median(),
            }
        ).to_string()
    )
    print("rank correlations between rungs, within the six centres only:")
    print(
        c.drop(columns=["group", conservation]).rank().corr(method="spearman").round(2).to_string()
    )


if __name__ == "__main__":
    main()
