"""The housing indicators that are measured for a whole borough: every cell takes the value of the
borough that holds its centre."""

import numpy as np
import pandas as pd


def by_borough(
    values: dict[str, float], owner: dict[str, str | None], cells: list[str]
) -> pd.Series:
    """The value of each cell's borough. A cell in no borough, or in a borough without a value,
    has none."""
    found = [
        values.get(code, np.nan) if code is not None else np.nan
        for code in (owner[cell] for cell in cells)
    ]
    return pd.Series(found, index=cells, dtype=float)
