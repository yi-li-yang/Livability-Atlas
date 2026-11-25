"""The electoral wards of the United Kingdom, December 2022 (dataset `ons-ward-boundaries`).

The ONS's generalised, clipped boundaries (BGC), served by its ArcGIS service in British National
Grid, with each ward's code (`WD22CD`), name (`WD22NM`) and local authority (`LAD22NM`). In London
they are the wards of the borough elections of May 2022. Open Government Licence v3.0, with OS data
under Crown copyright.
"""

from pathlib import Path
from typing import cast

import geopandas as gpd

from atlas.datasets.countries.gb.arcgis import Bounds, fetch_features

SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Wards_December_2022_Boundaries_UK_BGC/FeatureServer/0/query"
)
FIELDS = ["WD22CD", "WD22NM", "LAD22NM"]


def fetch(data_dir: Path, bounds: Bounds) -> Path:
    """Downloads the wards that touch `bounds` (x min, y min, x max, y max, in metres of British
    National Grid) to `data/raw/census/`, once, and returns the GeoJSON file."""
    return fetch_features(data_dir, "wards-2022", SERVICE, ",".join(FIELDS), bounds)


def read_boundaries(path: Path) -> gpd.GeoDataFrame:
    """The wards as a table with `WD22CD`, `WD22NM`, `LAD22NM` and a geometry in British National
    Grid."""
    areas = gpd.read_file(path).set_crs("EPSG:27700", allow_override=True)
    return cast(gpd.GeoDataFrame, areas[[*FIELDS, "geometry"]])
