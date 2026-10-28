"""Street-level crimes recorded by the police of England, Wales and Northern Ireland (dataset
`police-uk`).

data.police.uk publishes one archive a month that holds the latest 36 months, so the newest one is
enough. Greater London is policed by the Metropolitan Police and the City of London Police. Open
Government Licence v3.0.
"""

import zipfile
from pathlib import Path

import pandas as pd
import requests

from atlas.fetch import download

FORCES = ("metropolitan", "city-of-london")
MONTHS = 12  # a year, so that the seasons average out
COLUMNS = ["Month", "Longitude", "Latitude", "Crime type"]
LAST_UPDATED = "https://data.police.uk/api/crime-last-updated"


def archive_url(month: str) -> str:
    return f"https://data.police.uk/data/archive/{month}.zip"


def months_up_to(latest: str, count: int = MONTHS) -> list[str]:
    """The `count` months that end with `latest` ("2026-08"), oldest first."""
    year, month = (int(part) for part in latest.split("-"))
    index = year * 12 + month - 1
    return [f"{i // 12}-{i % 12 + 1:02d}" for i in range(index - count + 1, index + 1)]


def latest_month() -> str:
    """The newest month that data.police.uk has published."""
    reply = requests.get(LAST_UPDATED, timeout=60)
    reply.raise_for_status()
    return reply.json()["date"][:7]


def fetch(data_dir: Path) -> tuple[Path, list[str]]:
    """Downloads the newest archive to `data/raw/police/` once (it is about 1.7 GB), and returns
    it with the months to read from it."""
    latest = latest_month()
    archive = data_dir / "raw" / "police" / f"{latest}.zip"
    download(archive_url(latest), archive)
    return archive, months_up_to(latest)


def read_crimes(archive: Path, months: list[str]) -> pd.DataFrame:
    """The street-level records of Greater London's two forces for `months`, with the columns
    `Month`, `Longitude`, `Latitude` and `Crime type`."""
    frames = []
    with zipfile.ZipFile(archive) as zipped:
        names = set(zipped.namelist())
        for month in months:
            for force in FORCES:
                name = f"{month}/{month}-{force}-street.csv"
                if name in names:
                    with zipped.open(name) as file:
                        frames.append(pd.read_csv(file, usecols=COLUMNS))
    if not frames:
        raise ValueError(
            f"the archive {archive.name} holds no crimes for {months[0]} to {months[-1]}"
        )
    return pd.concat(frames, ignore_index=True)
