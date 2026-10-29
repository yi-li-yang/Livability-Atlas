"""GP practices' registered patients and GPs, September 2026 (datasets `nhs-gp-registered-patients`
and `nhs-gp-workforce`). NHS England, under the Open Government Licence v3.0.

The patients file counts the people registered at each practice, with the practice's postcode.
The workforce file counts the full-time equivalent staff of each practice by role. The release is
pinned: each month's files have their own addresses.
"""

import zipfile
from pathlib import Path

import pandas as pd

from atlas.fetch import download

PATIENTS_URL = "https://files.digital.nhs.uk/2F/09F237/gp-reg-pat-prac-all.zip"
WORKFORCE_URL = "https://files.digital.nhs.uk/78/760FF2/GPWPracticeCSV.092026.zip"
WORKFORCE_TABLE = "High level.csv"
TOTAL = "Total"
TRAINING = "GP in Training"  # trainees are not fully qualified GPs


def fetch(data_dir: Path) -> tuple[Path, Path]:
    """Downloads the patients and the workforce files to `data/raw/nhs-gp/` once, and returns
    them."""
    folder = data_dir / "raw" / "nhs-gp"
    paths = (folder / "patients.zip", folder / "workforce.zip")
    for url, path in zip((PATIENTS_URL, WORKFORCE_URL), paths, strict=True):
        download(url, path)
    return paths


def read_practices(patients: Path, workforce: Path) -> pd.DataFrame:
    """The GP practices, indexed by code, with their `Postcode`, registered `patients` and `gps`:
    the full-time equivalent fully qualified GPs (partners, salaried GPs, locums and retainers,
    not trainees). A practice with no GP on record has 0."""
    with zipfile.ZipFile(patients) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".csv"))
        registered = pd.read_csv(archive.open(name), encoding="utf-8", keep_default_na=False)
    registered = registered.loc[
        (registered["TYPE"] == "GP") & (registered["SEX"] == "ALL") & (registered["AGE"] == "ALL")
    ]
    practices = registered.set_index("CODE")[["POSTCODE", "NUMBER_OF_PATIENTS"]]
    practices.columns = pd.Index(["Postcode", "patients"])
    with zipfile.ZipFile(workforce) as archive:
        name = next(n for n in archive.namelist() if n.endswith(WORKFORCE_TABLE))
        staff = pd.read_csv(archive.open(name), encoding="utf-8-sig")
    qualified = staff.loc[
        (staff["STAFF_GROUP"] == "GP")
        & (staff["MEASURE"] == "FTE")
        & (staff["DETAILED_STAFF_ROLE"] != TOTAL)
        & ~staff["DETAILED_STAFF_ROLE"].str.startswith(TRAINING)
    ]
    gps = qualified.groupby("PRAC_CODE")["VALUE"].sum()
    practices["gps"] = gps.reindex(practices.index).fillna(0.0).to_numpy(dtype=float)
    practices.index.name = "code"
    return practices
