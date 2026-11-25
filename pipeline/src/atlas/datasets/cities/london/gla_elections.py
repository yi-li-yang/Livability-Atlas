"""The London borough council elections of 5 May 2022 (dataset `gla-borough-elections-2022`): the
Greater London Authority's report, under the Open Government Licence v2.0.

Its "Turnout Summary Tables" give, for each of the 679 wards of the 32 boroughs, the seats, the
electorate, the ballot papers at the count and how many came from polling stations and by post.
The City of London's Common Council votes apart, and is not in it. The report is a PDF (about
13 MB), read with pypdf; the GLA's spreadsheet of the same results has the ballots but not the
electorate.
"""

import re
from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from atlas.fetch import download

URL = (
    "https://data.london.gov.uk/download/e16o8/a797f5c7-02a3-4a76-9629-b96b132a0b21/"
    "Local%20Elections%20Report.pdf"
)
SECTION = "Turnout Summary Tables"
ROW = re.compile(
    r"^\s*(?P<ward>\S.*?)\s{2,}(?P<seats>[123])\s+(?P<electorate>[\d,]+)\s+(?P<ballots>[\d,]+)"
    r"\s+[\d.]+%\s+(?P<polling>[\d,]+)\s+(?P<postal>[\d,]+)\s*$"
)
COUNTS = ("electorate", "ballots", "polling", "postal")


def _key(text: str) -> str:
    """A borough's name as a heading may spell it: lower case, "&" as "and", single spaces."""
    return " ".join(text.lower().replace("&", " and ").split())


def fetch(data_dir: Path) -> Path:
    """Downloads the report to `data/raw/gla-elections/` once, and returns it."""
    path = data_dir / "raw" / "gla-elections" / "borough-elections-2022.pdf"
    download(URL, path)
    return path


def read_turnout(path: Path, boroughs: Iterable[str]) -> pd.DataFrame:
    """The report's turnout tables (see `parse_tables`), from the pages after their heading."""
    pages = [page.extract_text(extraction_mode="layout") for page in PdfReader(path).pages]
    start = next((i for i, text in enumerate(pages) if SECTION in text), None)
    if start is None:
        raise ValueError(f"the report has no {SECTION!r}")
    return parse_tables(pages[start:], boroughs)


def parse_tables(pages: Sequence[str], boroughs: Iterable[str]) -> pd.DataFrame:
    """One row per ward: its `borough` (the heading above it, one of `boroughs`), `ward`, `seats`
    and the counts. Two wards of one borough with the same counts are left out, both: the 2022
    report gives Hounslow's Hanworth Village and Heston Central the same ballots, which cannot both
    be right, and which is wrong is unknown."""
    headings = {_key(name): name for name in boroughs}
    borough: str | None = None
    rows: list[dict[str, object]] = []
    for text in pages:
        last_was_row = False
        for line in text.splitlines():
            if _key(line) in headings:
                borough, last_was_row = headings[_key(line)], False
                continue
            found = ROW.match(line)
            if not found:
                # A long ward name wraps: its end is a line of words alone, just under its row.
                if last_was_row and line.strip() and not re.search(r"\d", line):
                    rows[-1]["ward"] = f"{rows[-1]['ward']} {line.strip()}"
                last_was_row = False
                continue
            last_was_row = True
            if borough is None:
                raise ValueError(f"a ward comes before any borough: {line.strip()!r}")
            row: dict[str, object] = {"borough": borough, "ward": found["ward"].strip()}
            row["seats"] = int(found["seats"])
            for name in COUNTS:
                row[name] = int(found[name].replace(",", ""))
            rows.append(row)
    table = pd.DataFrame(rows, columns=["borough", "ward", "seats", *COUNTS])
    copies = table.duplicated(["borough", "ballots", "polling", "postal"], keep=False)
    return table.loc[~copies].reset_index(drop=True)
