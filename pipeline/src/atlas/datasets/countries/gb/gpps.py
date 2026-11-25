"""The GP Patient Survey, 2026 (dataset `nhs-gp-patient-survey`): NHS England's survey of patients
registered at each GP practice in England, run by Ipsos. Fieldwork from January to April 2026,
published on 9 July 2026.

The practice file has one row per practice, keyed by its ODS code, and over a thousand columns. Only
two are read: question 32's summary result, the weighted share of patients who rate their overall
experience of the practice as very or fairly good (`overallexp.pcteval`, from 0 to 1), and the
number of patients who answered it (`overallexp.baseevaluw`). A result from fewer than 10 answers is
suppressed (-97); a share under 0.5% is given as -98. Results from 2024 on are a new time series,
not comparable with 2023 and before. The file is pinned to the 2026 release (about 100 MB).
"""

from pathlib import Path

import numpy as np
import pandas as pd

from atlas.fetch import download

URL = (
    "https://www.gp-patient.co.uk/FileDownload/Download?fileRedirect=2026%2Fsurvey-results%2F"
    "practice-results%2Fpractice-data-csv%2FGPPS_2026_Practice_data_(weighted)_(csv)_PUBLIC.csv"
)
CODE = "ad_practicecode"
GOOD = "overallexp.pcteval"
ANSWERS = "overallexp.baseevaluw"
UNDER_HALF_A_PERCENT = -98.0


def fetch(data_dir: Path) -> Path:
    """Downloads the 2026 practice file to `data/raw/gpps/` once, and returns it."""
    path = data_dir / "raw" / "gpps" / "practice-2026.csv"
    download(URL, path)
    return path


def read_ratings(path: Path) -> pd.DataFrame:
    """Each practice's share of patients rating its overall experience good (`good`, from 0 to 1;
    NaN where the result is suppressed or missing) and the number who answered (`answers`), indexed
    by the practice's ODS code."""
    header = pd.read_csv(path, nrows=0, encoding="utf-8").columns
    missing = [c for c in (CODE, GOOD, ANSWERS) if c not in header]
    if missing:
        raise ValueError(f"the practice file has no {', '.join(missing)}")
    table = pd.read_csv(path, usecols=[CODE, GOOD, ANSWERS], encoding="utf-8", dtype={CODE: str})
    good = np.asarray(pd.to_numeric(table[GOOD], errors="coerce"), dtype=float)
    good = np.where(good == UNDER_HALF_A_PERCENT, 0.0025, good)
    good = np.where((good >= 0) & (good <= 1), good, np.nan)  # -97 (suppressed) and gaps
    answers = np.nan_to_num(np.asarray(pd.to_numeric(table[ANSWERS], errors="coerce"), float))
    return pd.DataFrame(
        {"good": good, "answers": answers.astype(int)},
        index=pd.Index(table[CODE].str.strip(), name="practice"),
    )
