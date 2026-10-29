"""Ofsted's latest inspection of each state-funded school (dataset `ofsted-school-inspections`).

The monthly management information file lists every state-funded school with the outcome of its
latest inspections. Since 10 November 2025 a full inspection ends in a report card that grades
up to eight areas on a five-point scale and says whether safeguarding standards are met. Before
that, a full inspection graded the overall effectiveness from 1 (outstanding) to 4 (inadequate),
and a school judged good was visited without grades, with an outcome that says whether it
remains good. The release is pinned: each month's file has its own address. Open Government
Licence v3.0.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from atlas.fetch import download

URL = (
    "https://assets.publishing.service.gov.uk/media/6ad095a72de3184ccf8b818d/"
    "Management_information_-_state-funded_schools_-_latest_inspections_as_at_30_Sep_2026.csv"
)
AREAS = [
    "Inclusion",
    "Curriculum and teaching",
    "Achievement",
    "Attendance and behaviour",
    "Personal development and wellbeing",
    "Leadership and governance",
    "Early years (where applicable)",
    "Post-16 provision (where applicable)",
]
COLUMNS = [
    "URN",
    "Ofsted phase",
    "Safeguarding standards",
    *AREAS,
    "Latest OEIF overall effectiveness",
    "Ungraded inspection overall outcome",
]
PHASES = {"Primary", "Secondary"}


def fetch(data_dir: Path) -> Path:
    """Downloads the file to `data/raw/ofsted/` once, and returns it."""
    target = data_dir / "raw" / "ofsted" / "latest-inspections.csv"
    download(URL, target)
    return target


def read_judgements(path: Path) -> pd.DataFrame:
    """The latest judgements of the primary and secondary schools in the file, with the school's
    `URN` and the columns of `COLUMNS`, all as text (the file is Windows-1252)."""
    frame = pd.read_csv(path, encoding="latin-1", usecols=COLUMNS, dtype=str, low_memory=False)
    kept = frame.loc[frame["Ofsted phase"].isin(sorted(PHASES))].copy()
    kept["URN"] = np.asarray(pd.to_numeric(kept["URN"]), dtype="int64")
    return kept.drop(columns="Ofsted phase").reset_index(drop=True)
