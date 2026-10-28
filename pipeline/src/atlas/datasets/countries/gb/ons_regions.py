"""The ONS's region boundaries (dataset `ons-region-boundaries`), fetched for one region by name."""

from pathlib import Path
from urllib.parse import urlencode

from atlas.fetch import download

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Regions_December_2025_Boundaries_EN_BGC/FeatureServer/0/query"
)
NAME_FIELD = "RGN25NM"


def url(name: str) -> str:
    """The query for one region's boundary, as GeoJSON in longitude and latitude (WGS 84)."""
    quoted = name.replace("'", "''")  # SQL doubles a quote inside a string
    query = {
        "where": f"{NAME_FIELD}='{quoted}'",
        "outFields": f"{NAME_FIELD},RGN25CD",
        "outSR": 4326,
        "f": "geojson",
    }
    return f"{SERVICE}?{urlencode(query)}"


def fetch(name: str, data_dir: Path) -> Path:
    """Downloads the region's boundary to `data/raw/ons-regions/`, once, and returns its path."""
    path = data_dir / "raw" / "ons-regions" / f"{name}.geojson"
    download(url(name), path)
    return path
