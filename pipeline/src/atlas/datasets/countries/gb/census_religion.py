"""Usual residents by religion and output area, from Census 2021 (dataset
`ons-census-2021-topic-summaries`, table TS030). Open Government Licence v3.0.

The census asked an optional question, so each area also counts those who did not answer.
"""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts030.zip"
FILE = "census2021-ts030-oa.csv"
PREFIX = "Religion: "
TOTAL = "Total: All usual residents"


def fetch(data_dir: Path) -> Path:
    """Downloads the table to `data/raw/census/` once, and returns the zip."""
    archive = data_dir / "raw" / "census" / "census2021-ts030.zip"
    download(URL, archive)
    return archive


def read_groups(path: Path) -> pd.DataFrame:
    """The residents of each output area by religion (and those who did not answer), indexed by
    the area's code. The total is left out, because it only adds the rest up."""
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
