"""The ONS's personal well-being estimates by local authority (dataset
`ons-personal-wellbeing-local-authority`): how people rate their life satisfaction, from the
Annual Population Survey. Open Government Licence v3.0.

The ONS paused the local release in 2024, so the series ends in 2022-23. The estimates for one
borough carry wide intervals, so the latest three years are averaged. The release is pinned: the
file is version 4 of the dataset.
"""

from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv

from atlas.fetch import download

URL = (
    "https://download.ons.gov.uk/downloads/datasets/wellbeing-local-authority/"
    "editions/time-series/versions/4.csv"
)
YEARS = 3
MEASURE = "Life satisfaction"
ESTIMATE = "Average (mean)"  # the mean score from 0 to 10, not a share of people


def fetch(data_dir: Path) -> Path:
    """Downloads the table (about 9 MB) to `data/raw/ons-wellbeing/` once, and returns it."""
    path = data_dir / "raw" / "ons-wellbeing" / "wellbeing-local-authority.csv"
    download(URL, path)
    return path


def read_life_satisfaction(path: Path) -> dict[str, float]:
    """The mean life satisfaction, from 0 to 10, of each local authority by ONS code, averaged
    over the latest `YEARS` years of the table. An estimate the ONS marks as unusable is left
    out."""
    table = pacsv.read_csv(
        path,
        convert_options=pacsv.ConvertOptions(
            include_columns=[
                "v4_3",
                "Data marking",
                "yyyy-yy",
                "administrative-geography",
                "MeasureOfWellbeing",
                "Estimate",
            ],
            column_types={
                "v4_3": pa.string(),
                "Data marking": pa.string(),
                "yyyy-yy": pa.string(),
                "administrative-geography": pa.string(),
                "MeasureOfWellbeing": pa.string(),
                "Estimate": pa.string(),
            },
        ),
    )
    value = table["v4_3"].to_pylist()
    mark = table["Data marking"].to_pylist()
    period = table["yyyy-yy"].to_pylist()
    code = table["administrative-geography"].to_pylist()
    measure = table["MeasureOfWellbeing"].to_pylist()
    kind = table["Estimate"].to_pylist()
    wanted = [
        i
        for i in range(len(code))
        if measure[i] == MEASURE and kind[i] == ESTIMATE and not (mark[i] or "").strip()
    ]
    latest = sorted({period[i] for i in wanted})[-YEARS:]
    sums: dict[str, list[float]] = {}
    for i in wanted:
        if period[i] in latest and value[i]:
            sums.setdefault(code[i], []).append(float(value[i]))
    return {area: sum(v) / len(v) for area, v in sums.items()}
