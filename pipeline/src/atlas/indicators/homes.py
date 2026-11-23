"""Where people live (D22): the number of homes in each cell.

A score describes the homes in a cell, so a cell with fewer than `MINIMUM_HOMES` homes has no
score. That covers every kind of land where nobody lives, such as parks, airports, reservoirs and
industrial estates, without a list of them. A home counts in the cell that holds its postcode's
centre. In London, 22% of cells have no home at all, and a cell with a few is mostly a park's
lodge or a farm: with the minimum at 10, about a quarter of the cells have no score.
"""

from collections.abc import Iterable

import pandas as pd

MINIMUM_HOMES = 10


def count_by_cell(home_cells: Iterable[str], cells: list[str]) -> list[int]:
    """The number of homes in each of `cells`, from the cell of each home."""
    counts = pd.Series(list(home_cells), dtype=object).value_counts()
    return [int(n) for n in counts.reindex(cells).fillna(0)]


def lived_in(count: int) -> bool:
    """Whether a cell with this many homes is a place where people live."""
    return count >= MINIMUM_HOMES
