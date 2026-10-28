"""TfL's Public Transport Accessibility Levels, the 2015 release (dataset `tfl-ptal`).

The release is a 100 m grid of points in British National Grid, each with a PTAL band. Spike S1
(docs/spikes/S1-ptal.md) decided how it becomes hex cells: a cell takes the band that covers most
of its grid points, a tie goes to the lower band, and a cell with no grid point has no value, which
is not band 0.
"""

import zipfile
from pathlib import Path

import h3
import pandas as pd
from pyproj import Transformer

from atlas.fetch import download

# The URL of the release's grid values, on the London Datastore (Open Government Licence v2).
URL = (
    "https://data.london.gov.uk/download/24rz6/514d2847-94a8-4b9d-8a70-fdded01719a0/"
    "2015%20%20PTALs%20Grid%20Values.zip"
)
BANDS = ["0", "1a", "1b", "2", "3", "4", "5", "6a", "6b"]  # worst to best
_TO_WGS84 = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


def read_grid(path: Path) -> pd.DataFrame:
    """The grid points of TfL's spreadsheet: columns `x` and `y` in metres, and `band` as text."""
    frame = pd.read_excel(path, sheet_name="Query1", usecols=["X", "Y", "PTAL2015"], dtype=object)
    return pd.DataFrame(
        {
            "x": frame["X"].astype(float),
            "y": frame["Y"].astype(float),
            "band": frame["PTAL2015"].map(str),  # TfL writes band 0 as a number
        }
    )


def bands_by_cell(grid: pd.DataFrame, resolution: int) -> pd.Series:
    """Each hex cell's band from `read_grid`'s points: the most common, a tie to the lower."""
    unknown = set(grid["band"]) - set(BANDS)
    if unknown:
        raise ValueError(f"unknown PTAL bands {sorted(unknown)}")
    lng, lat = _TO_WGS84.transform(grid["x"].to_numpy(), grid["y"].to_numpy())
    cells = [h3.latlng_to_cell(a, o, resolution) for a, o in zip(lat, lng, strict=True)]
    counts = (
        pd.DataFrame({"cell": cells, "band": grid["band"].to_numpy()})
        .groupby(["cell", "band"])
        .size()
        .to_frame("n")
        .reset_index()
    )
    counts["order"] = counts["band"].map(BANDS.index)
    # Most points first, then the lower band: the first row of each cell is its band.
    best = counts.sort_values(
        ["cell", "n", "order"], ascending=[True, False, True]
    ).drop_duplicates("cell")
    return pd.Series(best["band"].to_numpy(), index=pd.Index(best["cell"]), name="service_level")


def fetch(data_dir: Path) -> Path:
    """Downloads the release to `data/raw/ptal/` once, unzips it, and returns the spreadsheet."""
    folder = data_dir / "raw" / "ptal"
    archive = folder / "ptal-2015.zip"
    download(URL, archive)
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(folder)
    return next(folder.glob("*Grid Values*.xlsx"))
