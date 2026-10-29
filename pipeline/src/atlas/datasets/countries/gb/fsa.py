"""Food hygiene ratings of food businesses, from the Food Standards Agency's Food Hygiene Rating
Scheme (dataset `fsa-food-hygiene-ratings`). Open Government Licence v3.0.

The register is served by an API, one local authority at a time. The first fetch is kept, so a
build reads the same ratings until the file is deleted. Ratings run from 0 to 5 in England, Wales
and Northern Ireland; a business awaiting inspection, or exempt, has none.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import requests
from pyproj import Transformer

BASE = "https://api.ratings.food.gov.uk"
HEADERS = {"x-api-version": "2", "accept": "application/json"}
# The FSA's name for the region, which picks the local authorities to ask for.
REGIONS = {"london": "London"}
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def fetch(data_dir: Path, region_id: str) -> Path:
    """Downloads the businesses of the region's local authorities to `data/raw/fsa/` once."""
    path = data_dir / "raw" / "fsa" / f"{region_id}.parquet"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    reply = requests.get(f"{BASE}/Authorities", headers=HEADERS, timeout=60)
    reply.raise_for_status()
    rows = []
    for authority in reply.json()["authorities"]:
        if authority.get("RegionName") != REGIONS[region_id]:
            continue
        establishments = requests.get(
            f"{BASE}/Establishments",
            headers=HEADERS,
            timeout=300,
            params={"localAuthorityId": authority["LocalAuthorityId"], "pageSize": 0},
        )
        establishments.raise_for_status()
        for e in establishments.json()["establishments"]:
            geo = e.get("geocode") or {}
            try:
                lng, lat = float(geo["longitude"]), float(geo["latitude"])
            except (KeyError, TypeError, ValueError):
                continue
            rows.append(
                {
                    "name": e["BusinessName"],
                    "type": e.get("BusinessType"),
                    "lng": lng,
                    "lat": lat,
                    "authority": authority["Name"],
                    "rating": e.get("RatingValue"),
                }
            )
    partial = path.with_name(path.name + ".part")
    pd.DataFrame(rows, columns=["name", "type", "lng", "lat", "authority", "rating"]).to_parquet(
        partial
    )
    partial.replace(path)
    return path


def read_ratings(path: Path) -> pd.DataFrame:
    """The businesses with a rating of 0 to 5: `lng`, `lat`, `Easting`, `Northing` and the
    `rating` as a number."""
    frame = pd.read_parquet(path)
    number = np.asarray(pd.to_numeric(frame["rating"], errors="coerce"), dtype=float)
    rated = (number >= 0) & (number <= 5)  # a missing rating is not a number, so it is left out
    lng, lat = frame["lng"].to_numpy(dtype=float)[rated], frame["lat"].to_numpy(dtype=float)[rated]
    x, y = _TO_BNG.transform(lng, lat)
    return pd.DataFrame(
        {"lng": lng, "lat": lat, "Easting": x, "Northing": y, "rating": number[rated].astype(int)}
    )
