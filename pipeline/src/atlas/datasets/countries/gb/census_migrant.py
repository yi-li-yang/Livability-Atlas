"""Usual residents by where they lived a year before, from Census 2021 (dataset
`ons-census-2021-topic-summaries`, table TS019, "Migrant indicator"). Open Government Licence
v3.0. Census day was 21 March 2021, in the pandemic, when fewer people moved than usual.
"""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts019.zip"
FILE = "census2021-ts019-oa.csv"
TOTAL = "Migrant indicator: Total: All usual residents; measures: Value"
SAME = (
    "Migrant indicator: Address one year ago is the same as the address of enumeration; "
    "measures: Value"
)


def fetch(data_dir: Path) -> Path:
    """Downloads the table to `data/raw/census/` once, and returns the zip."""
    archive = data_dir / "raw" / "census" / "census2021-ts019.zip"
    download(URL, archive)
    return archive


def read_counts(path: Path) -> pd.DataFrame:
    """For each output area, indexed by its code: the `residents` and those of them who lived at
    the same address a year before (`same_address`)."""
    with zipfile.ZipFile(path) as archive, archive.open(FILE) as file:
        table = pd.read_csv(file, encoding="utf-8", index_col="geography code")
    counts = pd.DataFrame(
        {"residents": table[TOTAL].to_numpy(), "same_address": table[SAME].to_numpy()},
        index=table.index,
    )
    counts.index.name = "OA21CD"
    return counts
