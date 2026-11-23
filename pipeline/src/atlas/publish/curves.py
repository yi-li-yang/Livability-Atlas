"""The ends of a region ramp (D25, docs/methodology/scoring.md, section 3).

A region ramp is for a measured indicator that no standard gives thresholds. Its ends come from
the region's own values: from each end, the most extreme cells are left out, up to `TRIM` of
them, but never a value that a whole area shares (`AREA` of the cells, and at least two cells),
such as a borough's rent. The build writes the result into the bundle as a plain ramp with stated
numbers, so the app and the reference scorer only ever see ramps.
"""

import math
from collections.abc import Iterable
from typing import Any

import numpy as np

from atlas.catalogue.models import RegionRamp
from atlas.publish.manifest import ManifestRamp

TRIM = 0.01  # at most this share of the cells is left out at each end
AREA = 0.001  # a value that at least this share of the cells share is a whole area: never left out


def _numbers(values: Iterable[Any]) -> np.ndarray:
    kept = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    return np.asarray(kept, dtype=float)


def _end(values: np.ndarray, counts: np.ndarray, n: int) -> float:
    """The first value, walking in from one end, that is not left out."""
    area = max(2.0, AREA * n)
    cut = 0
    for value, count in zip(values, counts, strict=True):
        if count >= area or cut + count > TRIM * n:
            return float(value)
        cut += count
    return float(values[-1])


def region_ends(values: Iterable[Any]) -> tuple[float, float] | None:
    """The lowest and the highest value that a region ramp keeps, or None where there is none."""
    numbers = _numbers(values)
    if numbers.size == 0:
        return None
    distinct, counts = np.unique(numbers, return_counts=True)
    n = int(numbers.size)
    return _end(distinct, counts, n), _end(distinct[::-1], counts[::-1], n)


def resolve(curve: RegionRamp, values: Iterable[Any]) -> ManifestRamp | None:
    """The plain ramp that a region ramp becomes over these values (the cells with homes), or
    None where the values cannot tell cells apart: none, a single one, or none above 0 on a log
    scale without an offset."""
    numbers = _numbers(values)
    offset = (curve.offset or 0.0) if curve.log else 0.0
    if curve.log:
        # A log scale has no place for a value at or below -offset: the ends come from the values
        # above it, trimmed as any others, and a value below scores as the low end.
        numbers = numbers[numbers + offset > 0]
    ends = region_ends(numbers)
    if ends is None:
        return None
    low, high = ends
    if low == high:
        return None
    t0, t1 = (high, low) if curve.better == "lower" else (low, high)
    return ManifestRamp(
        shape="ramp",
        t0=t0,
        t1=t1,
        log=curve.log,
        offset=curve.offset if curve.log else None,
        from_region=True,
    )
