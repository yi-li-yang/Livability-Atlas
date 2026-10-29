"""Cross-checks: independent datasets that measure related things should agree.

A relation names two columns and the sign that their rank correlation (Spearman's) should have.
Ranks, not values, so that a skewed column and a column of bands compare. The floor is set from
the reason the two should agree, well under the strength seen in the data, so that only a broken
input trips it.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.stats import rankdata

from atlas.qa.cells import Cells
from atlas.qa.results import Result, Status, some

GROUP = "Relations"
MIN_CELLS = 5  # fewer cells with both values than this cannot show a correlation


@dataclass(frozen=True)
class Relation:
    a: str  # the column of one indicator or option
    b: str
    sign: Literal[1, -1]  # +1: they rise together; -1: one falls as the other rises
    floor: float  # how strong the correlation must be, from 0 to 1
    reason: str  # why the two should agree, as a short clause


def relation_checks(cells: Cells, relations: Sequence[Relation]) -> list[Result]:
    labels = {d.column: d.label for d in cells.described()}
    return [_check(cells, relation, labels) for relation in relations]


def _check(cells: Cells, relation: Relation, labels: dict[str, str]) -> Result:
    a, b = relation.a, relation.b
    moves = "rise together" if relation.sign > 0 else "move in opposite ways"
    name = f"{labels.get(a, a)} and {labels.get(b, b)} {moves}"
    why = relation.reason

    def result(status: Status, detail: str) -> Result:
        return Result(GROUP, name, status, detail, why)

    missing = [c for c in (a, b) if not cells.has(c)]
    if missing:
        return result("skipped", f"the bundle lacks {some(missing)}")
    x, y = cells.scored(a), cells.scored(b)
    both = ~np.isnan(x) & ~np.isnan(y)
    n = int(both.sum())
    if n < MIN_CELLS:
        return result("skipped", f"only {n} cells have both")
    x, y = x[both], y[both]
    for column, values in ((a, x), (b, y)):
        if np.all(values == values[0]):
            return result("skipped", f"{column} has one value in these cells")
    rho = float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])
    needs = f"{relation.sign * relation.floor:+.2f} {'or more' if relation.sign > 0 else 'or less'}"
    detail = f"rank correlation {rho:+.2f} over {n:,} cells; needs {needs}"
    return result("pass" if relation.sign * rho >= relation.floor else "fail", detail)
