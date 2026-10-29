"""Usual residents by ethnic group and output area, from Census 2021 (dataset
`ons-census-2021-topic-summaries`, table TS021). Open Government Licence v3.0.

The table counts residents in the census's 19 detailed groups, each under one of five broad
groups. The detailed groups are what the diversity index mixes.
"""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts021.zip"
FILE = "census2021-ts021-oa.csv"
PREFIX = "Ethnic group: "
TOTAL = "Total: All usual residents"


def fetch(data_dir: Path) -> Path:
    """Downloads the table to `data/raw/census/` once, and returns the zip."""
    archive = data_dir / "raw" / "census" / "census2021-ts021.zip"
    download(URL, archive)
    return archive


def read_groups(path: Path) -> pd.DataFrame:
    """The residents of each output area in each of the detailed ethnic groups, indexed by the
    area's code. A group is named under its broad group, such as `White: Irish`. The broad groups
    and the total are left out, because they only add up the detailed ones."""
    with zipfile.ZipFile(path) as archive, archive.open(FILE) as file:
        table = pd.read_csv(file, encoding="utf-8", index_col="geography code")
    names = {
        column: column.removeprefix(PREFIX) for column in table.columns if column.startswith(PREFIX)
    }
    detailed = [column for column, name in names.items() if ": " in name and name != TOTAL]
    groups = pd.DataFrame(
        table[detailed].to_numpy(), index=table.index, columns=[names[c] for c in detailed]
    )
    groups.index.name = "OA21CD"
    return groups
