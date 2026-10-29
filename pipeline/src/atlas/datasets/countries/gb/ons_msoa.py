"""The 2021 middle layer super output areas (MSOAs) of England and Wales (dataset
`ons-msoa-boundaries`).

The ONS's generalised, clipped boundaries (BGC), served by its ArcGIS service in British National
Grid. Each MSOA has about 7,000 to 10,000 residents. Open Government Licence v3.0, with OS data
under Crown copyright.
"""

from pathlib import Path
from typing import cast

import geopandas as gpd

from atlas.datasets.countries.gb.arcgis import Bounds, fetch_features

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V3/FeatureServer/0/query"
)


def fetch(data_dir: Path, bounds: Bounds) -> Path:
    """Downloads the MSOAs that touch `bounds` (x min, y min, x max, y max, in metres of British
    National Grid) to `data/raw/census/`, once, and returns the GeoJSON file."""
    return fetch_features(data_dir, "msoa", SERVICE, "MSOA21CD", bounds)


def read_boundaries(path: Path) -> gpd.GeoDataFrame:
    """The MSOAs as a table with `MSOA21CD` and a geometry in British National Grid."""
    areas = gpd.read_file(path).set_crs("EPSG:27700", allow_override=True)
    return cast(gpd.GeoDataFrame, areas[["MSOA21CD", "geometry"]])
