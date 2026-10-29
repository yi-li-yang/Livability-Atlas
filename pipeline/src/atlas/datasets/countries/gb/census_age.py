"""Usual residents by five-year age band and output area, from Census 2021 (dataset
`ons-census-2021-topic-summaries`, table TS007A). Open Government Licence v3.0."""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts007a.zip"
FILE = "census2021-ts007a-oa.csv"
PREFIX = "Age: "
TOTAL = "Total"


def fetch(data_dir: Path) -> Path:
    """Downloads the table to `data/raw/census/` once, and returns the zip."""
    archive = data_dir / "raw" / "census" / "census2021-ts007a.zip"
    download(URL, archive)
    return archive


def read_groups(path: Path) -> pd.DataFrame:
    """The residents of each output area in each five-year age band, indexed by the area's code,
    youngest band first (such as `Aged 5 to 9 years`). The total is left out."""
    with zipfile.ZipFile(path) as archive, archive.open(FILE) as file:
        table = pd.read_csv(file, encoding="utf-8", index_col="geography code")
    kept = [c for c in table.columns if c.startswith(PREFIX) and c.removeprefix(PREFIX) != TOTAL]
    groups = pd.DataFrame(
        table[kept].to_numpy(),
        index=table.index,
        columns=[c.removeprefix(PREFIX) for c in kept],
    )
    groups.index.name = "OA21CD"
    return groups
