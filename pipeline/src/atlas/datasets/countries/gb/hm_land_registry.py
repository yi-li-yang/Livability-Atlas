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


def read_sales(paths: list[Path], months: int = 24) -> pd.DataFrame:
    """The standard sales of homes in the last `months` months of the data, with `price`, `date`,
    `postcode`, `type`, `paon`, `saon` and `street`."""
    sales = pd.concat(
        [
            pd.read_csv(
                path,
                header=None,
                names=COLUMNS,
                usecols=["price", "date", "postcode", "type", "paon", "saon", "street", "category"],
                dtype={"paon": str, "saon": str, "street": str},
                keep_default_na=False,
            )
            for path in paths
        ],
        ignore_index=True,
    )
    sales["date"] = pd.to_datetime(sales["date"].str[:10])
    cutoff = sales["date"].max() - pd.DateOffset(months=months)
    kept = sales.loc[
        (sales["category"] == STANDARD)
        & sales["type"].isin(sorted(HOMES))
        & (sales["date"] > cutoff)
    ]
    return kept.drop(columns="category").reset_index(drop=True)
