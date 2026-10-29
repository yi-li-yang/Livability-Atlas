"""Council tax levels set by local authorities in England, 2026 to 2027, from the Ministry of
Housing, Communities and Local Government (dataset `mhclg-council-tax`). Open Government
Licence v3.0.

Tables 1 to 9 come as an OpenDocument spreadsheet. Table 9 gives the council tax of each billing
authority's area for a dwelling in each band, with the precepts of the Greater London Authority
and others included. The release is pinned: each year's file has its own address.
"""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from atlas.fetch import download

URL = (
    "https://assets.publishing.service.gov.uk/media/69de1fa63e81003ae0422508/Tables_1-9_2026-27.ods"
)
SHEET = "Table_9"
_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
MAX_COLUMNS = 40  # more than any table here: empty cells repeated past it are not read


def fetch(data_dir: Path) -> Path:
    """Downloads the tables to `data/raw/council-tax/` once."""
    target = data_dir / "raw" / "council-tax" / "Tables_1-9_2026-27.ods"
    download(URL, target)
    return target


def _rows(path: Path, sheet: str) -> list[list[str | float | None]]:
    """The rows of one sheet of an OpenDocument spreadsheet: a number where the cell holds one,
    its text otherwise, and None where it is empty."""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("content.xml"))
    for table in root.iter(f"{_TABLE}table"):
        if table.get(f"{_TABLE}name") != sheet:
            continue
        rows: list[list[str | float | None]] = []
        for row in table.iter(f"{_TABLE}table-row"):
            cells: list[str | float | None] = []
            for cell in row.findall(f"{_TABLE}table-cell"):
                text = "".join("".join(p.itertext()) for p in cell.findall(f"{_TEXT}p"))
                number = cell.get(f"{_OFFICE}value")
                value: str | float | None = float(number) if number is not None else text or None
                repeat = int(cell.get(f"{_TABLE}number-columns-repeated", "1"))
                cells += [value] * min(repeat, MAX_COLUMNS - len(cells))
                if len(cells) >= MAX_COLUMNS:
                    break
            rows.append(cells)
        return rows
    raise KeyError(f"{path.name} has no sheet {sheet}")


def read_band_d(path: Path) -> dict[str, float]:
    """The council tax (pounds a year) of a Band D dwelling in each authority's area, by ONS code.
    An authority without an ONS code, such as a police function, is left out."""
    rows = _rows(path, SHEET)
    header = next(row for row in rows if "ONS Code" in row and "Band D" in row)
    code, band = header.index("ONS Code"), header.index("Band D")
    found: dict[str, float] = {}
    for row in rows[rows.index(header) + 1 :]:
        if len(row) <= band:
            continue
        name, tax = row[code], row[band]
        if isinstance(name, str) and isinstance(tax, float) and name.startswith("E"):
            found[name] = tax
    return found
