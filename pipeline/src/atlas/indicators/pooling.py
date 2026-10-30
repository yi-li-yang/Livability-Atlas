"""Pooling what happens at points over a cell and the cells around it.

A cell holds too few sales, certificates or places for a stable figure of its own, so a median is
taken over the cell and the cells within a number of steps of it, and a cell with too few around it
has no value.
"""

import h3
import numpy as np
import pandas as pd


def pooled_median(
    table: pd.DataFrame, column: str, cells: list[str], steps: int, minimum: int
) -> pd.Series:
    """The median of `column` over the rows of `table` (which has a `cell` for each) in each cell
    and the cells within `steps` of it. A cell with fewer than `minimum` values around it has no
    value. A missing value is not counted."""
    by_cell = {
        str(cell): group.dropna().to_numpy(dtype=float)
        for cell, group in table.groupby("cell")[column]
    }
    out = np.full(len(cells), np.nan)
    for position, cell in enumerate(cells):
        around = [by_cell[c] for c in h3.grid_disk(cell, steps) if c in by_cell]
        if around:
            values = np.concatenate(around)
            if len(values) >= minimum:
                out[position] = float(np.median(values))
    return pd.Series(out, index=cells)
