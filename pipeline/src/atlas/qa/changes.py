"""Changes since the previous build: what moved enough to need a look."""

from dataclasses import dataclass

from atlas.publish.manifest import ManifestDataset
from atlas.qa.cells import Cells
from atlas.qa.format import number, share
from atlas.qa.stats import ColumnStats, column_stats

COVERAGE_MOVE = 0.01  # a point of the share of cells with a value
MEDIAN_MOVE = 0.05  # five per cent of the median


@dataclass(frozen=True)
class Snapshot:
    """What a build is compared by."""

    cells: int
    stats: list[ColumnStats]
    datasets: list[ManifestDataset]


def snapshot(cells: Cells) -> Snapshot:
    return Snapshot(cells.count, column_stats(cells), cells.manifest.datasets)


def compare(now: Snapshot, before: Snapshot) -> list[str]:
    """One plain sentence for each change, or none when the two builds agree."""
    lines: list[str] = []
    if now.cells != before.cells:
        lines.append(f"Cells: {before.cells:,} before, {now.cells:,} now.")
    old = {s.column: s for s in before.stats}
    new = {s.column: s for s in now.stats}
    added = [s.label for s in now.stats if s.column not in old]
    removed = [s.label for s in before.stats if s.column not in new]
    if added:
        lines.append(f"Added: {', '.join(added)}.")
    if removed:
        lines.append(f"Removed: {', '.join(removed)}.")
    for stat in now.stats:
        previous = old.get(stat.column)
        if previous is None:
            continue
        if abs(stat.valued - previous.valued) >= COVERAGE_MOVE - 1e-9:
            lines.append(
                f"{stat.label}: the share of cells with a value moved from "
                f"{share(previous.valued)} to {share(stat.valued)}."
            )
        if (
            stat.median is not None
            and previous.median is not None
            and abs(stat.median - previous.median) >= MEDIAN_MOVE * abs(previous.median) - 1e-12
            and stat.median != previous.median
        ):
            lines.append(
                f"{stat.label}: the median moved from {number(previous.median)} to "
                f"{number(stat.median)} ({stat.unit})."
            )
    lines += _dataset_changes(now.datasets, before.datasets)
    return lines


def _dataset_changes(now: list[ManifestDataset], before: list[ManifestDataset]) -> list[str]:
    old = {d.id: d for d in before}
    new = {d.id: d for d in now}
    lines = [f"Added dataset: {i}." for i in sorted(new.keys() - old.keys())]
    lines += [f"Removed dataset: {i}." for i in sorted(old.keys() - new.keys())]
    for dataset_id in sorted(new.keys() & old.keys()):
        for field in ("date", "licence"):
            a, b = getattr(old[dataset_id], field), getattr(new[dataset_id], field)
            if a != b:
                lines.append(f"Dataset {dataset_id}: the {field} moved from {a} to {b}.")
    return lines
