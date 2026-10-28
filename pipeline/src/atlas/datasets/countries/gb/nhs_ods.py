"""England's GP practices and their branch surgeries, from NHS England's Organisation Data Service
(dataset `nhs-ods`). Open Government Licence v3.0.

The two files have no header. The columns used are the code (0), name (1), postcode (9), close date
(11, branches), status (12, practices), the code of the practice a branch belongs to (14, branches)
and the role (25, practices), of which `RO76` is a GP practice.
"""

from pathlib import Path

import pandas as pd

from atlas.fetch import download

URL = "https://www.odsdatasearchandexport.nhs.uk/api/getReport?report={report}"
GP_PRACTICE = "RO76"
COLUMNS = {
    0: "code",
    1: "name",
    9: "Postcode",
    11: "closed",
    12: "status",
    14: "parent",
    25: "role",
}


def fetch(data_dir: Path) -> tuple[Path, Path]:
    """Downloads the files of practices and of branch surgeries to `data/raw/ods/` once, and
    returns their paths."""
    folder = data_dir / "raw" / "ods"
    paths = (folder / "epraccur.csv", folder / "ebranchs.csv")
    for path in paths:
        download(URL.format(report=path.stem), path)
    return paths


def _read(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(
        path, header=None, usecols=list(COLUMNS), dtype=str, keep_default_na=False, encoding="utf-8"
    )
    return frame.rename(columns=COLUMNS)


def read_gp_sites(practices: Path, branches: Path) -> pd.DataFrame:
    """The active GP practices and the open branch surgeries of them, with their `Postcode`.

    Vaccination sites that the file lists as branches are left out, as are services that are not
    GP practices and records without a postcode.
    """
    main = _read(practices)
    main = main.loc[(main["status"] == "ACTIVE") & (main["role"] == GP_PRACTICE)]
    extra = _read(branches)
    extra = extra.loc[
        (extra["closed"] == "")
        & extra["parent"].isin(main["code"])
        & ~extra["name"].str.upper().str.contains("COVID")
    ]
    sites = pd.concat([main[["Postcode"]], extra[["Postcode"]]], ignore_index=True)
    return sites.loc[sites["Postcode"] != ""].reset_index(drop=True)
