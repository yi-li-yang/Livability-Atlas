"""Spike S6, step 1: fetch London's places from Overture, OpenStreetMap and the FSA, into data/raw/.

Throwaway code, never imported by `atlas`. Run from `pipeline/` with
`uv run python notebooks/s6_fetch.py`. Needs `data/raw/osm/greater-london.osm.pbf`
(Geofabrik). Each source is fetched once and cached.
"""

import json

import duckdb
import pandas as pd
import quackosm
import requests

from atlas.paths import data_dir

RAW = data_dir() / "raw"
OVERTURE_RELEASE = "2026-10-21.0"
BBOX = (-0.51, 51.28, 0.34, 51.69)  # Greater London's bounding box
FSA = "https://api.ratings.food.gov.uk"
FSA_HEADERS = {"x-api-version": "2", "accept": "application/json"}
OSM_TAGS = {
    "amenity": [
        "restaurant",
        "cafe",
        "fast_food",
        "pub",
        "bar",
        "pharmacy",
        "doctors",
        "clinic",
        "hospital",
        "library",
    ],
    "shop": ["supermarket", "convenience", "greengrocer", "bakery", "butcher"],
    "leisure": ["fitness_centre"],
}


def overture() -> pd.DataFrame:
    path = RAW / "overture" / f"places-london-{OVERTURE_RELEASE}.parquet"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect()
        con.sql(
            "INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';"
        )
        source = f"s3://overturemaps-us-west-2/release/{OVERTURE_RELEASE}/theme=places/type=place/*"
        con.sql(f"""
            COPY (
              SELECT id, ST_X(geometry) AS lng, ST_Y(geometry) AS lat, names.primary AS name,
                     brand.names.primary AS brand, brand.wikidata AS brand_wikidata,
                     taxonomy.primary AS category, taxonomy.hierarchy AS hierarchy, basic_category,
                     confidence, operating_status, sources[1].dataset AS source,
                     list_transform(sources, x -> x.dataset) AS source_list
              FROM read_parquet('{source}', hive_partitioning=1)
              WHERE bbox.xmin BETWEEN {BBOX[0]} AND {BBOX[2]}
                AND bbox.ymin BETWEEN {BBOX[1]} AND {BBOX[3]}
            ) TO '{path.as_posix()}' (FORMAT parquet)
        """)
    return pd.read_parquet(path)


def osm() -> pd.DataFrame:
    path = RAW / "osm" / "places-london.parquet"
    if not path.exists():
        frame = quackosm.convert_pbf_to_geodataframe(
            RAW / "osm" / "greater-london.osm.pbf",
            tags_filter=OSM_TAGS,
            keep_all_tags=True,
            working_directory=RAW / "osm" / "work",
        )
        centre = frame.geometry.to_crs("EPSG:27700").centroid.to_crs("EPSG:4326")
        wanted = ["name", "brand", "brand:wikidata", "cuisine", "amenity", "shop", "leisure"]
        out = pd.DataFrame(
            {"feature_id": frame.index, "lng": centre.x.to_numpy(), "lat": centre.y.to_numpy()}
        )
        for key in wanted:
            out[key] = [tags.get(key) for tags in frame["tags"]]
        out.to_parquet(path)
    return pd.read_parquet(path)


def fsa() -> pd.DataFrame:
    path = RAW / "fsa" / "london.parquet"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        authorities = requests.get(f"{FSA}/Authorities", headers=FSA_HEADERS, timeout=60).json()[
            "authorities"
        ]
        rows = []
        for authority in authorities:
            if authority.get("RegionName") != "London":
                continue
            reply = requests.get(
                f"{FSA}/Establishments",
                headers=FSA_HEADERS,
                timeout=300,
                params={"localAuthorityId": authority["LocalAuthorityId"], "pageSize": 0},
            ).json()
            for e in reply["establishments"]:
                geo = e.get("geocode") or {}
                try:
                    lng, lat = float(geo["longitude"]), float(geo["latitude"])
                except (KeyError, TypeError, ValueError):
                    continue
                rows.append(
                    {
                        "name": e["BusinessName"],
                        "type": e["BusinessType"],
                        "type_id": e["BusinessTypeID"],
                        "lng": lng,
                        "lat": lat,
                        "authority": authority["Name"],
                        "rating": e.get("RatingValue"),
                    }
                )
        pd.DataFrame(rows).to_parquet(path)
    return pd.read_parquet(path)


def main() -> None:
    summary = {}
    places = overture()
    summary["overture places in London's box"] = len(places)
    summary["overture sources"] = places["source"].value_counts().head(8).to_dict()
    summary["overture top categories"] = places["category"].value_counts().head(25).to_dict()
    pois = osm()
    summary["osm features"] = len(pois)
    food = fsa()
    summary["fsa establishments with a location"] = len(food)
    summary["fsa business types"] = food["type"].value_counts().to_dict()
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
