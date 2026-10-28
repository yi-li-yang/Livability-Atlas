"""The public green spaces of Great Britain and the ways into them, from Ordnance Survey's OS Open
Greenspace (dataset `os-open-greenspace`). Open Government Licence v3.0.

The download is a zip holding one GeoPackage with two layers: `greenspace_site` (the areas, with
the function of each) and `access_point` (the ways in, each naming its site). The GeoPackage is
unpacked once, because reading it from inside the zip takes over a minute.
"""

import zipfile
from pathlib import Path

import numpy as np
import pyogrio

from atlas.fetch import download

URL = "https://api.os.uk/downloads/v1/products/OpenGreenspace/downloads?area=GB&format=GeoPackage&redirect"
LAYER_FILE = "Data/opgrsp_gb.gpkg"
# The functions that are places to walk to for a green space. Play spaces and sports facilities
# are small or for members, and cemeteries and allotments are not for a walk.
FUNCTIONS = ("Public Park Or Garden", "Playing Field")
MIN_AREA = 20_000.0  # square metres: 2 ha, as Natural England's standard asks
ON_FOOT = ("Pedestrian", "Motor Vehicle And Pedestrian")


def fetch(data_dir: Path) -> Path:
    """Downloads the Great Britain file to `data/raw/greenspace/` once (about 60 MB), unpacks its
    GeoPackage beside it (about 140 MB), and returns that."""
    folder = data_dir / "raw" / "greenspace"
    archive = folder / "opgrsp_gb.zip"
    download(URL, archive)
    package = folder / "opgrsp_gb.gpkg"
    if not package.exists() or package.stat().st_mtime < archive.stat().st_mtime:
        with zipfile.ZipFile(archive) as unpacked, package.open("wb") as out:
            out.write(unpacked.read(LAYER_FILE))
    return package


def read_access_points(path: Path, bounds: tuple[float, float, float, float]) -> np.ndarray:
    """The easting and northing of each way in on foot to a park or playing field of at least 2 ha,
    inside `bounds` (west, south, east, north, in metres of British National Grid). A site with no
    way in on record is left out."""
    sites = pyogrio.read_dataframe(path, layer="greenspace_site", bbox=bounds)
    sites = sites.loc[sites["function"].isin(FUNCTIONS) & (sites.geometry.area >= MIN_AREA)]
    ways = pyogrio.read_dataframe(path, layer="access_point", bbox=bounds)
    ways = ways.loc[
        ways["ref_to_greenspace_site"].isin(sites["id"]) & ways["access_type"].isin(ON_FOOT)
    ]
    return np.column_stack([ways.geometry.x.to_numpy(), ways.geometry.y.to_numpy()])
