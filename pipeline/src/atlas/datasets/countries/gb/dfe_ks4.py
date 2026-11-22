"""How well pupils do in each school at GCSE (dataset `dfe-ks4-performance`), from the Department
for Education's key stage 4 performance tables, through its open statistics API. Open Government
Licence v3.0.

The data set "Performance tables schools data" has a row for each school, year and breakdown of its
pupils (by sex, by disadvantage and so on), with the average Attainment 8 score: the points of a
pupil's eight best GCSE results, out of 90. Progress 8 is not published for 2024/25 and 2025/26, so
Attainment 8 is the score. The API sends the CSV compressed, and the file is kept as saved.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

from atlas.fetch import download

DATA_SET = "19e39901-a96c-be76-b9c2-6af54ae076d2"
URL = f"https://api.education.gov.uk/statistics/v1/data-sets/{DATA_SET}/csv"
COLUMNS = [
    "time_period",
    "version",
    "school_urn",
    "breakdown",
    "pupil_count",
    "attainment8_average",
]
FINAL = "Final"
GZIP_START = bytes([0x1F, 0x8B])  # the first two bytes of a gzip file


def fetch(data_dir: Path) -> Path:
    """Downloads the table (about 14 MB, compressed) to `data/raw/dfe/` once, and returns it."""
    path = data_dir / "raw" / "dfe" / "ks4-schools.csv.gz"
    download(URL, path)
    return path


def read_attainment(path: Path) -> pd.DataFrame:
    """The average Attainment 8 score (`attainment8`) and the number of pupils (`pupils`, NaN
    where the DfE gives none) of each school, indexed by its URN: the whole school, in the latest
    year with final figures. A school with no score is left out."""
    table = pacsv.read_csv(
        _open(path),
        convert_options=pacsv.ConvertOptions(
            include_columns=COLUMNS, column_types={c: pa.string() for c in COLUMNS}
        ),
    )
    period = np.array(table["time_period"].to_pylist(), dtype=object)
    version = np.array(table["version"].to_pylist(), dtype=object)
    whole = np.array(table["breakdown"].to_pylist(), dtype=object) == "Total"
    final = whole & (version == FINAL)
    latest = max(period[final])
    rows = np.flatnonzero(final & (period == latest))
    urn = np.array(table["school_urn"].to_pylist(), dtype=object)[rows]
    score = _numbers(np.array(table["attainment8_average"].to_pylist(), dtype=object)[rows])
    pupils = _numbers(np.array(table["pupil_count"].to_pylist(), dtype=object)[rows])
    found = pd.DataFrame(
        {"attainment8": score, "pupils": pupils}, index=pd.Index(urn.astype(int), name="URN")
    )
    return found.loc[found["attainment8"].notna()]


def _open(path: Path) -> pa.NativeFile:
    """The file as a stream of text. The API sends the CSV compressed, and the HTTP library
    unpacks it as it is saved, so the file holds either: the start of a gzip file says which."""
    with path.open("rb") as file:
        packed = file.read(2) == GZIP_START
    stream = pa.OSFile(str(path))
    return pa.CompressedInputStream(stream, "gzip") if packed else stream


def _numbers(values: np.ndarray) -> np.ndarray:
    """The numbers among `values`; a code such as `z` or `c` (not applicable, suppressed) is NaN."""
    out = np.full(len(values), np.nan)
    for i, text in enumerate(values):
        try:
            out[i] = float(text)
        except (TypeError, ValueError):
            continue
    return out
