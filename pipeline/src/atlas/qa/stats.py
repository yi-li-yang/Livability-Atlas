"""The QA report's statistics: how each column's values are spread, and how well each factor is
covered by data."""

from collections import Counter
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from atlas.catalogue.models import Curve
from atlas.publish.manifest import ManifestFactor
from atlas.qa.cells import Cells, Described
from atlas.scoring.engine import LOW_COVERAGE


@dataclass(frozen=True)
class Category:
    """A value of a text column, the share of all cells that have it, and its curve's score."""

    value: str
    share: float
    score: float | None


@dataclass(frozen=True)
class ColumnStats:
    column: str
    indicator: str
    name: str
    unit: str
    option: str | None  # the name of the option of a choice indicator that the column holds
    valued: float  # the share of cells with a value
    lowest: float | None = None
    p5: float | None = None
    median: float | None = None
    p95: float | None = None
    highest: float | None = None
    # The shares of the cells with a value that a ramp or an ideal-range curve scores in full and
    # at none: a curve that gives nearly every cell the same score adds little contrast.
    full: float | None = None
    none: float | None = None
    categories: tuple[Category, ...] | None = None  # a text column, in its curve's order

    @property
    def label(self) -> str:
        """ "Faith (Hindu)" for an option of a choice, and the indicator's name for any other."""
        return f"{self.name} ({self.option})" if self.option else self.name


def column_stats(cells: Cells) -> list[ColumnStats]:
    return [_stats(cells, d) for d in cells.described() if d.column in cells.columns]


def _stats(cells: Cells, described: Described) -> ColumnStats:
    column, total = described.column, max(cells.count, 1)
    base = {
        "column": column,
        "indicator": described.indicator,
        "name": described.name,
        "unit": described.unit,
        "option": described.option.name if described.option is not None else None,
    }
    if column in cells.texts():  # a text column: count its categories
        counts = Counter(v for v in cells.text(column) if v is not None)
        scores = _lookup(described.curve)
        order = [k for k in scores if k in counts] + sorted(k for k in counts if k not in scores)
        return ColumnStats(
            **base,
            valued=sum(counts.values()) / total,
            categories=tuple(Category(k, counts[k] / total, scores.get(k)) for k in order),
        )
    numbers = cells.numbers(column)
    present = numbers[~np.isnan(numbers)]
    if len(present) == 0:
        return ColumnStats(**base, valued=0.0)
    lowest, p5, median, p95, highest = (
        float(x) for x in np.percentile(present, [0, 5, 50, 95, 100])
    )
    full, none = curve_span(described.curve, present)
    return ColumnStats(
        **base,
        valued=len(present) / total,
        lowest=lowest,
        p5=p5,
        median=median,
        p95=p95,
        highest=highest,
        full=full,
        none=none,
    )


def _lookup(curve: Curve | None) -> dict[str, float]:
    if curve is None or curve.shape != "lookup":
        return {}
    return {str(key): float(score) for key, score in curve.scores.items()}


def curve_span(
    curve: Curve | None, present: NDArray[np.float64]
) -> tuple[float | None, float | None]:
    """The shares of values that a ramp or an ideal-range curve scores 1 and 0. The formulas are
    the reference scorer's (`atlas.scoring.engine.curve_score`), over a whole array."""
    if curve is None:
        return None, None
    if curve.shape == "ramp":
        scores = np.clip((present - curve.t0) / (curve.t1 - curve.t0), 0.0, 1.0)
    elif curve.shape == "ideal-range":
        rising = np.clip((present - curve.l0) / (curve.l1 - curve.l0), 0.0, 1.0)
        falling = np.clip((present - curve.u0) / (curve.u1 - curve.u0), 0.0, 1.0)
        scores = np.minimum(rising, falling)
    else:
        return None, None
    return float((scores >= 1.0).mean()), float((scores <= 0.0).mean())


@dataclass(frozen=True)
class FactorCoverage:
    """How much of a top-level factor's data a cell has: its measured indicators, each counted
    once, whatever the weights. A choice indicator counts when any of its options has a value."""

    id: str
    name: str
    indicators: int
    mean: float  # the average share of the indicators that a cell has
    unscored: float  # the share of cells with none of them: the factor cannot score them
    low: float  # the share of cells under the engine's coverage flag


def factor_coverage(cells: Cells) -> list[FactorCoverage]:
    columns: dict[str, list[str]] = {}
    for described in cells.described():
        if described.column in cells.columns:
            columns.setdefault(described.indicator, []).append(described.column)
    out = []
    for factor in cells.manifest.factors:
        have = [
            np.any([cells.valued(c) for c in columns[i]], axis=0)
            for i in _indicators(factor)
            if i in columns
        ]
        if not have:
            out.append(FactorCoverage(factor.id, factor.name, 0, 0.0, 1.0, 1.0))
            continue
        share = np.mean(have, axis=0)
        out.append(
            FactorCoverage(
                factor.id,
                factor.name,
                len(have),
                float(share.mean()),
                float((share == 0).mean()),
                float((share < LOW_COVERAGE).mean()),
            )
        )
    return out


def _indicators(factor: ManifestFactor) -> list[str]:
    if factor.children is None:
        return [factor.indicator] if factor.indicator is not None else []
    return [i for child in factor.children for i in _indicators(child)]
