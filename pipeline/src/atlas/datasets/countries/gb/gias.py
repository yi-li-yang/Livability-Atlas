"""England's register of schools, Get Information About Schools (dataset `dfe-gias`), from the
Department for Education. Open Government Licence v3.0.

The register is one file of every school ever recorded, named by the day it was made. The first file
downloaded is kept, so a build reads the same one until it is deleted.
"""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from atlas.fetch import download

URL = (
    "https://ea-edubase-api-prod.azurewebsites.net/edubase/downloads/public/edubasealldata{day}.csv"
)
DAYS_BACK = 7  # today's file may not be made yet

OPEN = {"Open", "Open, but proposed to close"}
# The groups of state-funded schools. Independent schools, universities and colleges are not.
STATE_FUNDED = {"Local authority maintained schools", "Academies", "Free Schools"}
# Types of state-funded establishment that are not mainstream schools for a child to walk to.
NOT_MAINSTREAM = ("special", "alternative provision", "pupil referral", "16 to 19", "post 16")
PRIMARY = {"Primary", "Middle-deemed primary", "All-through"}
SECONDARY = {"Secondary", "Middle-deemed secondary", "All-through"}
COLUMNS = [
    "URN",
    "EstablishmentStatus (name)",
    "EstablishmentTypeGroup (name)",
    "TypeOfEstablishment (name)",
    "PhaseOfEducation (name)",
    "Easting",
    "Northing",
]


def fetch(data_dir: Path, today: date | None = None) -> Path:
    """The newest register in `data/raw/gias/`, or the newest that can be downloaded."""
    folder = data_dir / "raw" / "gias"
    kept = sorted(folder.glob("edubasealldata*.csv"))
    if kept:
        return kept[-1]
    day = today or date.today()
    for back in range(DAYS_BACK + 1):
        stamp = (day - timedelta(days=back)).strftime("%Y%m%d")
        target = folder / f"edubasealldata{stamp}.csv"
        try:
            download(URL.format(day=stamp), target)
        except requests.HTTPError:
            continue
        return target
    raise RuntimeError(f"the register of schools has no file for the last {DAYS_BACK} days")


def read_schools(path: Path) -> pd.DataFrame:
    """The open, state-funded, mainstream schools with a location, as a table with the columns
    `URN`, `Easting`, `Northing` (metres of British National Grid), `primary` and `secondary`. An
    all-through school is both."""
    frame = pd.read_csv(path, encoding="cp1252", usecols=COLUMNS, low_memory=False)
    kind = frame["TypeOfEstablishment (name)"].fillna("").str.lower()
    mainstream = ~kind.str.contains("|".join(NOT_MAINSTREAM), regex=True)
    wanted = (
        frame["EstablishmentStatus (name)"].isin(list(OPEN))
        & frame["EstablishmentTypeGroup (name)"].isin(list(STATE_FUNDED))
        & mainstream
        & frame["Easting"].notna()
        & frame["Northing"].notna()
    )
    schools = frame.loc[wanted].copy()
    phase = schools["PhaseOfEducation (name)"]
    schools["primary"] = phase.isin(list(PRIMARY))
    schools["secondary"] = phase.isin(list(SECONDARY))
    return schools.loc[schools["primary"] | schools["secondary"]].reset_index(drop=True)[
        ["URN", "Easting", "Northing", "primary", "secondary"]
    ]
