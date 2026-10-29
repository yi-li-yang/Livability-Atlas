"""The 2021 output areas of England and Wales (dataset `ons-output-area-boundaries`).

The ONS's generalised, clipped boundaries (BGC), served by its ArcGIS service in British National
Grid. Open Government Licence v3.0, with OS data under Crown copyright.
"""

from pathlib import Path
from typing import cast

import geopandas as gpd

from atlas.datasets.countries.gb.arcgis import Bounds, fetch_features

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Output_Areas_2021_EW_BGC_V2/FeatureServer/0/query"
)


def fetch(data_dir: Path, bounds: Bounds) -> Path:
    """Downloads the output areas that touch `bounds` (x min, y min, x max, y max, in metres of
    British National Grid) to `data/raw/census/`, once, and returns the GeoJSON file."""
    return fetch_features(data_dir, "output-areas", SERVICE, "OA21CD", bounds)


def read_boundaries(path: Path) -> gpd.GeoDataFrame:
    """The output areas as a table with `OA21CD` and a geometry in British National Grid."""
    areas = gpd.read_file(path).set_crs("EPSG:27700", allow_override=True)
    return cast(gpd.GeoDataFrame, areas[["OA21CD", "geometry"]])
