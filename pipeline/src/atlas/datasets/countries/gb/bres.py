"""Jobs by lower layer super output area, from the Business Register and Employment Survey (dataset
`ons-bres`).

The ONS's open-access table on Nomis (NM_189_1): the number of jobs (employees and working
owners) at each workplace area, rounded by the ONS to the nearest 25 and suppressed where a figure
could identify a business. The areas are the 2011 LSOAs. Open Government Licence v3.0, through
Nomis. The survey's confidential figures are not used: only this open table.
"""

from pathlib import Path

import pandas as pd

from atlas.fetch import download

YEAR = 2024
BASE = (
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_189_1.data.csv?geography=TYPE151"
    f"&date={YEAR}&industry=37748736&employment_status=1&measure=1&measures=20100"
    "&select=geography_code,obs_value"
)
PAGE = 25000  # Nomis sends at most this many rows to an anonymous caller
PAGES = 2  # England and Wales have 35,672 areas


def fetch(data_dir: Path) -> list[Path]:
    """Downloads the table to `data/raw/nomis/` once, in pages, and returns the files."""
    folder = data_dir / "raw" / "nomis"
    files = []
    for page in range(PAGES):
        target = folder / f"bres-jobs-lsoa-{YEAR}-{page + 1}.csv"
        download(f"{BASE}&recordoffset={page * PAGE}", target)
        files.append(target)
    return files


def read_jobs(paths: list[Path]) -> pd.Series:
    """The jobs at each area, indexed by its code (`LSOA11CD`). An area with no figure (the ONS
    suppresses small ones) is left out."""
    table = pd.concat([pd.read_csv(p, encoding="utf-8") for p in paths], ignore_index=True)
    table = table.dropna(subset=["OBS_VALUE"])
    return pd.Series(
        table["OBS_VALUE"].to_numpy(dtype=float),
        index=pd.Index(table["GEOGRAPHY_CODE"], name="LSOA11CD"),
        name="jobs",
    )
