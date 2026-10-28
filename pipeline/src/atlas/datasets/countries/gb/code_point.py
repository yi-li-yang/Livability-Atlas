"""The place of every postcode in Great Britain, from Ordnance Survey's Code-Point Open (dataset
`os-code-point-open`). Open Government Licence v3.0, through the OS OpenData Licence.

The file holds each postcode's easting and northing in metres of British National Grid.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://api.os.uk/downloads/v1/products/CodePointOpen/downloads?area=GB&format=CSV&redirect"
NO_PLACE = 90  # the positional quality of a postcode without a location


def fetch(data_dir: Path) -> Path:
    """Downloads the Great Britain file to `data/raw/codepoint/` once (about 15 MB)."""
    target = data_dir / "raw" / "codepoint" / "codepo_gb.zip"
    download(URL, target)
    return target


def normalise(postcode: str) -> str:
    """A postcode without spaces, in capitals: how the two files are matched."""
    return "".join(postcode.split()).upper()


def read_postcodes(path: Path) -> pd.DataFrame:
    """The `Easting` and `Northing` of each postcode, indexed by the normalised postcode."""
    tables = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith("Data/CSV/") and name.endswith(".csv"):
                tables.append(
                    pd.read_csv(
                        io.BytesIO(archive.read(name)),
                        header=None,
                        usecols=[0, 1, 2, 3],
                        names=["Postcode", "Quality", "Easting", "Northing"],
                        encoding="utf-8",
                    )
                )
    frame = pd.concat(tables, ignore_index=True)
    frame = frame.loc[frame["Quality"] != NO_PLACE]
    frame.index = pd.Index([normalise(p) for p in frame["Postcode"]])
    return frame[["Easting", "Northing"]]
