"""The 2011 lower layer super output areas of England and Wales (dataset `ons-lsoa-boundaries`).

The ONS's generalised, clipped boundaries (BGC), version 3, served by its ArcGIS service in British
National Grid. The Business Register and Employment Survey publishes its figures for these areas
(2011), not for the 2021 ones. Open Government Licence v3.0, with OS data under Crown copyright.
"""

from pathlib import Path
from typing import cast

import geopandas as gpd

from atlas.datasets.countries.gb.arcgis import Bounds, fetch_features

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "LSOA_Dec_2011_Boundaries_Generalised_Clipped_BGC_EW_V3/FeatureServer/0/query"
)


def fetch(data_dir: Path, bounds: Bounds) -> Path:
    """Downloads the areas that touch `bounds` to `data/raw/census/`, once, and returns the file."""
    return fetch_features(data_dir, "lsoa-2011", SERVICE, "LSOA11CD", bounds)


def read_boundaries(path: Path) -> gpd.GeoDataFrame:
    """The areas as a table with `LSOA11CD` and a geometry in British National Grid."""
    areas = gpd.read_file(path).set_crs("EPSG:27700", allow_override=True)
    return cast(gpd.GeoDataFrame, areas[["LSOA11CD", "geometry"]])
