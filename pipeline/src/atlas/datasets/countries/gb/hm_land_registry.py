"""HM Land Registry's Price Paid Data (dataset `hm-land-registry-price-paid`).

One CSV of every sale of a home in England and Wales for each year, with no header, updated
monthly. Open Government Licence v3.0 for the prices; the addresses come from Ordnance Survey and
Royal Mail (see the dataset's `licence_note`).
"""

from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://price-paid-data.publicdata.landregistry.gov.uk/pp-{year}.csv"
COLUMNS = [
    "id",
    "price",
    "date",
    "postcode",
    "type",
    "new",
    "tenure",
    "paon",
    "saon",
    "street",
    "locality",
    "town",
    "district",
    "county",
    "category",
    "status",
]
YEARS = [2024, 2025, 2026]  # the last 24 months of the data fall in these
HOMES = {"D", "S", "T", "F"}  # detached, semi-detached, terraced, flat; "O" is other
STANDARD = "A"  # "B" is a repossession, a buy-to-let sale or another sale not at market value


def fetch(data_dir: Path, years: list[int]) -> list[Path]:
    """Downloads each year's file to `data/raw/landregistry/` once, and returns them. The file of
    the current year grows each month: delete it to get the new sales."""
    folder = data_dir / "raw" / "landregistry"
    paths = []
    for year in years:
        path = folder / f"pp-{year}.csv"
        download(URL.format(year=year), path)
        paths.append(path)
    return paths


def years_of(ending: pd.Timestamp, months: int = 24) -> list[int]:
    """The years whose files hold the `months` months that end at `ending`."""
    start = ending - pd.DateOffset(months=months)
    return list(range(start.year, ending.year + 1))


def latest_date(paths: list[Path]) -> pd.Timestamp:
    """The date of the latest sale in the files."""
    latest = [
        pd.to_datetime(
            pd.read_csv(path, header=None, names=COLUMNS, usecols=["date"])["date"].str[:10]
        ).max()
        for path in paths
    ]
    return max(latest)


def read_window(paths: list[Path], ending: pd.Timestamp, months: int = 24) -> pd.DataFrame:
    """The standard sales of homes in the `months` months that end at `ending` (the last day
    counts), with `price`, `date`, `postcode`, `type`, `paon`, `saon` and `street`. Each file is
    cut to the window as it is read, because a year of sales is a million rows."""
    cutoff = ending - pd.DateOffset(months=months)
    kept = []
    for path in paths:
        sales = pd.read_csv(
            path,
            header=None,
            names=COLUMNS,
            usecols=["price", "date", "postcode", "type", "paon", "saon", "street", "category"],
            dtype={"paon": str, "saon": str, "street": str},
            keep_default_na=False,
        )
        sales["date"] = pd.to_datetime(sales["date"].str[:10])
        kept.append(
            sales.loc[
                (sales["category"] == STANDARD)
                & sales["type"].isin(sorted(HOMES))
                & (sales["date"] > cutoff)
                & (sales["date"] <= ending)
            ]
        )
    return pd.concat(kept, ignore_index=True).drop(columns="category")


def read_sales(paths: list[Path], months: int = 24) -> pd.DataFrame:
    """The standard sales of homes in the last `months` months of the data."""
    return read_window(paths, latest_date(paths), months)
