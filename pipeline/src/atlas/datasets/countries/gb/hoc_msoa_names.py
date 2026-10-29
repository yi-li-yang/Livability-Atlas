"""The House of Commons Library's names for the 2021 MSOAs (dataset `hoc-msoa-names`).

Local people and councillors name most MSOAs, and the Library publishes the names, so that "Soho"
stands for "Westminster 014". Open Parliament Licence v3.0, which allows use in products with an
acknowledgement of the source.
"""

from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://houseofcommonslibrary.github.io/msoanames/MSOA-Names-Latest2.csv"


def fetch(data_dir: Path) -> Path:
    """Downloads the names to `data/raw/msoa/` once, and returns the file."""
    target = data_dir / "raw" / "msoa" / "MSOA-Names-Latest2.csv"
    download(URL, target)
    return target


def read_names(path: Path) -> pd.DataFrame:
    """The name and the local authority (`area`) of each MSOA, indexed by its code. An MSOA that has
    no name of the Library's keeps the ONS's, such as `Westminster 013`."""
    table = pd.read_csv(path, encoding="utf-8-sig", keep_default_na=False)
    friendly = table["msoa21hclnm"].where(table["msoa21hclnm"] != "", table["msoa21nm"])
    names = pd.DataFrame(
        {"name": friendly.to_numpy(), "area": table["localauthorityname"].to_numpy()},
        index=pd.Index(table["msoa21cd"], name="MSOA21CD"),
    )
    return names
