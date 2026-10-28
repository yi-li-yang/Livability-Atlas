"""Usual residents by output area, from Census 2021 (dataset `ons-census-2021-residents`).

Table TS001 of the ONS's bulk download on Nomis, which holds one row per output area of England
and Wales. Open Government Licence v3.0.
"""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts001.zip"
FILE = "census2021-ts001-oa.csv"


def read_residents(path: Path) -> pd.Series:
    """The residents of each output area, indexed by its code (`OA21CD`)."""
    table = pd.read_csv(path, encoding="utf-8")
    code = table["geography code"]
    total = table["Residence type: Total; measures: Value"]
    return pd.Series(total.to_numpy(), index=pd.Index(code, name="OA21CD"), name="residents")


def fetch(data_dir: Path) -> Path:
    """Downloads the table to `data/raw/census/` once, and returns the output areas' file."""
    folder = data_dir / "raw" / "census"
    archive = folder / "census2021-ts001.zip"
    download(URL, archive)
    target = folder / FILE
    if not target.exists():
        with zipfile.ZipFile(archive) as zipped:
            zipped.extract(FILE, folder)
    return target
