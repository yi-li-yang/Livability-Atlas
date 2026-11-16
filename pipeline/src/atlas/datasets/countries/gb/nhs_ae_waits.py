"""How long people wait in A&E, by hospital trust (dataset `nhs-england-ae-waiting-times`).

NHS England's monthly "A&E attendances and emergency admissions": one row for each provider, with
the attendances at each type of department and how many of them took over four hours from arrival
to being admitted, transferred or discharged. Open Government Licence v3.0. Each month's file has
its own address, so the months are pinned here.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

from atlas.fetch import download

BASE = "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/"
MONTHS = {
    "2026-04": "2026/11/April-2026-Revised-12.11.26-CSV-28KB-aW27FD.csv",
    "2026-05": "2026/11/May-2026-Revised-12.11.26-CSV-28KB-Ea65dF.csv",
    "2026-06": "2026/11/June-2026-Revised-12.11.26-CSV-28KB-Re79AS.csv",
    "2026-07": "2026/11/July-2026-Revised-12.11.26-CSV-28KB-ws81YT.csv",
    "2026-08": "2026/11/August-2026-Revised-12.11.26-CSV-28KB-Pq49Sq.csv",
    "2026-09": "2026/10/September-2026-CSV-Re72Eh.csv",
    "2026-10": "2026/11/October-2026-CSV-WD35qg.csv",
}
CODE = "Org Code"
ATTENDANCES = "A&E attendances Type 1"
OVER = "Attendances over 4hrs Type 1"


def fetch(data_dir: Path) -> list[Path]:
    """Downloads each month's file to `data/raw/nhs-ae-waits/` once, and returns them."""
    paths = []
    for month, name in MONTHS.items():
        target = data_dir / "raw" / "nhs-ae-waits" / f"ae-{month}.csv"
        download(BASE + name, target)
        paths.append(target)
    return paths


def read_performance(paths: list[Path]) -> pd.Series:
    """The percent of each provider's type 1 attendances (the 24-hour emergency departments) that
    were over within four hours, over all the months, indexed by the provider's code. A provider
    with no type 1 attendances is left out."""
    attended: dict[str, float] = {}
    waited: dict[str, float] = {}
    for path in paths:
        table = pacsv.read_csv(
            path,
            convert_options=pacsv.ConvertOptions(
                include_columns=[CODE, ATTENDANCES, OVER],
                column_types={CODE: pa.string(), ATTENDANCES: pa.float64(), OVER: pa.float64()},
            ),
        )
        codes = table[CODE].to_pylist()
        seen = np.nan_to_num(table[ATTENDANCES].to_numpy(zero_copy_only=False))
        over = np.nan_to_num(table[OVER].to_numpy(zero_copy_only=False))
        for code, n, slow in zip(codes, seen, over, strict=True):
            attended[code] = attended.get(code, 0.0) + float(n)
            waited[code] = waited.get(code, 0.0) + float(slow)
    return pd.Series(
        {code: 100.0 * (1 - waited[code] / n) for code, n in attended.items() if n > 0},
        dtype=float,
    )
