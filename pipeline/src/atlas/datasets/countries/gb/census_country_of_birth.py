"""Usual residents by country of birth and output area, from Census 2021 (dataset
`ons-census-2021-topic-summaries`, table TS004). Open Government Licence v3.0.

At the smallest areas the census gives the place of birth in broad groups only: the United
Kingdom, the European Union in three groups of accession and the rest, other European countries,
and the other continents.
"""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.nomisweb.co.uk/output/census/2021/census2021-ts004.zip"
FILE = "census2021-ts004-oa.csv"
PREFIX = "Country of birth: "
SUFFIX = "; measures: Value"


def fetch(data_dir: Path) -> Path:
    """Downloads the table to `data/raw/census/` once, and returns the zip."""
    archive = data_dir / "raw" / "census" / "census2021-ts004.zip"
    download(URL, archive)
    return archive


def read_groups(path: Path) -> pd.DataFrame:
    """The residents of each output area born in each place the table splits no further, indexed
    by the area's code. A place the table splits into others, such as Europe, and the total, are
    left out, because they only add up what is under them."""
    with zipfile.ZipFile(path) as archive, archive.open(FILE) as file:
        table = pd.read_csv(file, encoding="utf-8", index_col="geography code")
    paths = {
        column: column.removeprefix(PREFIX).removesuffix(SUFFIX).strip()
        for column in table.columns
        if column.startswith(PREFIX)
    }
    names = [text for text in paths.values() if text != "Total"]
    kept = {
        column: text.split(": ")[-1]
        for column, text in paths.items()
        if text != "Total" and not any(other.startswith(text + ": ") for other in names)
    }
    groups = pd.DataFrame(
        table[list(kept)].to_numpy(), index=table.index, columns=list(kept.values())
    )
    groups.index.name = "OA21CD"
    return groups
