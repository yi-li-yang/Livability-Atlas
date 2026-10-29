"""The ONS's boundaries of local authority districts, which include London's boroughs (dataset
`ons-local-authority-boundaries`), fetched for the districts of one region. Open Government
Licence v3.0, with credits to the ONS and the Ordnance Survey."""

import json
from pathlib import Path
from urllib.parse import urlencode

import h3
import numpy as np
import shapely
from shapely.geometry import shape

from atlas.fetch import download

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_DEC_2025_Boundaries_UK_BGC/FeatureServer/0/query"
)
CODE_FIELD = "LAD25CD"
NAME_FIELD = "LAD25NM"
# The start of the ONS codes of a region's districts: London's boroughs are E09.
CODE_PREFIXES = {"london": "E09"}


def url(region_id: str) -> str:
    """The query for a region's districts, as GeoJSON in longitude and latitude (WGS 84)."""
    query = {
        "where": f"{CODE_FIELD} LIKE '{CODE_PREFIXES[region_id]}%'",
        "outFields": f"{CODE_FIELD},{NAME_FIELD}",
        "outSR": 4326,
        "f": "geojson",
    }
    return f"{SERVICE}?{urlencode(query)}"


def fetch(data_dir: Path, region_id: str) -> Path:
    """Downloads the region's districts to `data/raw/ons-local-authorities/` once."""
    path = data_dir / "raw" / "ons-local-authorities" / f"{region_id}.geojson"
    download(url(region_id), path)
    return path


def borough_of(path: Path, cells: list[str]) -> dict[str, str | None]:
    """The ONS code of the district that holds each cell's centre, or None for a cell in none."""
    collection = json.loads(path.read_text(encoding="utf-8"))
    centres = np.array([h3.cell_to_latlng(cell) for cell in cells])
    lat, lng = centres[:, 0], centres[:, 1]
    owner: list[str | None] = [None] * len(cells)
    for feature in collection["features"]:
        inside = shapely.contains_xy(shape(feature["geometry"]), lng, lat)
        for index in np.flatnonzero(inside):
            owner[index] = feature["properties"][CODE_FIELD]
    return dict(zip(cells, owner, strict=True))
