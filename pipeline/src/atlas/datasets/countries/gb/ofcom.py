"""Ofcom's Connected Nations data on broadband and mobile coverage, July 2025 (datasets
`ofcom-fixed-coverage` and `ofcom-mobile-coverage`). Open Government Licence v3.0.

The fixed broadband download is a zip that holds, among others, a zip of tables by census output
area. Ofcom reports gigabit-capable coverage, which includes full fibre and cable, and not full
fibre alone, which providers keep confidential. The mobile download has a table by local
authority, with the share of premises in each band of how many of the four networks provide a
signal. The release is pinned: each year's files have their own addresses.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

BASE = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/"
    "infrastructure-research/connected-nations-2025/"
)
FIXED_URL = f"{BASE}202507_fixed_broadband_coverage_r01.zip?v=407830"
MOBILE_URL = f"{BASE}202507_mobile_coverage_r01.zip?v=407840"
OUTER_TABLES = "202507_fixed_coverage_r01/202507_fixed_oa_coverage_r01.zip"
RESIDENTIAL_TABLE = "202507_fixed_oa_coverage_r01/202507_fixed_oa_res_coverage_r01.csv"
MOBILE_TABLE = "202507_mobile_coverage_r01/202507_mobile_coverage_laua_r01.csv"
FIVE_G = "5G_high_confidence_prem_out_4"  # outdoors, high confidence, from all four networks


def fetch(data_dir: Path) -> tuple[Path, Path]:
    """Downloads the fixed and the mobile files to `data/raw/ofcom/` once, and returns them."""
    folder = data_dir / "raw" / "ofcom"
    paths = (folder / "fixed.zip", folder / "mobile.zip")
    for url, path in zip((FIXED_URL, MOBILE_URL), paths, strict=True):
        download(url, path)
    return paths


def read_fixed(path: Path) -> pd.DataFrame:
    """The residential premises of each output area, indexed by its code, with `homes` (all of
    them) and `gigabit_homes` (those that can get a gigabit-capable connection)."""
    with zipfile.ZipFile(path) as outer:
        tables = zipfile.ZipFile(io.BytesIO(outer.read(OUTER_TABLES)))
    frame = pd.read_csv(
        io.BytesIO(tables.read(RESIDENTIAL_TABLE)),
        encoding="latin-1",
        usecols=["output_area", "All Premises", "Number of premises with Gigabit availability"],
        index_col="output_area",
    )
    frame.columns = pd.Index(["homes", "gigabit_homes"])
    return frame


def read_five_g(path: Path) -> dict[str, float]:
    """The percentage of premises in each local authority with a good outdoor 5G signal from all
    four networks, by the authority's ONS code. A band Ofcom leaves empty has no premises: 0."""
    with zipfile.ZipFile(path) as archive:
        frame = pd.read_csv(io.BytesIO(archive.read(MOBILE_TABLE)), encoding="latin-1")
    share = frame[FIVE_G].fillna(0.0)
    return {str(code): float(value) for code, value in zip(frame["laua"], share, strict=True)}
