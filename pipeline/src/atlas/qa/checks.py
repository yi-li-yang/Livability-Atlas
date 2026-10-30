"""The QA report's checks of a bundle's structure, its datasets and its values."""

import h3
import numpy as np

from atlas.qa.cells import Cells
from atlas.qa.results import Result, some

BUNDLE = "The bundle"
DATASETS = "Datasets"
VALUES = "Values"
TOLERANCE = 1e-6  # a share may be a hair above 100 from rounding
ENOUGH = 0.5  # the share of cells that should have a value, below which a column is flagged


def _result(
    group: str, name: str, problems: list[str], *, warn: bool = False, ok: str = ""
) -> Result:
    if not problems:
        return Result(group, name, "pass", ok)
    return Result(group, name, "warn" if warn else "fail", "; ".join(problems))


def bundle_checks(cells: Cells) -> list[Result]:
    """The bundle is what its manifest says it is."""
    manifest = cells.manifest
    named = cells.table["cell"].to_pylist()
    names = [c for c in named if isinstance(c, str)]
    resolution = manifest.grid.resolution

    count = []
    if cells.count != manifest.cell_count:
        count = [f"the table has {cells.count} rows and the manifest says {manifest.cell_count}"]

    order = []
    if len(names) != len(named):
        order.append(f"{len(named) - len(names)} cells have no id")
    if len(set(names)) != len(names):
        order.append(f"{len(names) - len(set(names))} cells are repeated")
    elif names != sorted(names):
        order.append("the cells are not in sorted order")

    bad = [c for c in names if not h3.is_valid_cell(c) or h3.get_resolution(c) != resolution]
    grid = [f"not cells of resolution {resolution}: {some(bad)}"] if bad else []

    expected = [d.column for d in cells.described()]
    missing = [c for c in expected if c not in cells.columns]
    extra = [c for c in cells.columns if c not in expected]
    columns = []
    if missing:
        columns.append(f"missing from the table: {some(missing)}")
    if extra:
        columns.append(f"not in the manifest: {some(extra)}")

    return [
        _result(BUNDLE, "The rows match the manifest's cell count", count),
        _result(BUNDLE, "The cells are sorted and unique", order),
        _result(BUNDLE, "The cells are H3 cells of the grid's resolution", grid),
        _result(BUNDLE, "The columns match the manifest", columns, ok=f"{len(expected)} columns"),
        _result(BUNDLE, "The neighbourhoods match their list", _neighbourhood_problems(cells)),
    ]


def _neighbourhood_problems(cells: Cells) -> list[str]:
    listing = cells.manifest.neighbourhoods
    has_column = "neighbourhood" in cells.table.column_names
    if listing is None:
        return (
            ["the table has a neighbourhood column and the manifest lists none"]
            if has_column
            else []
        )
    if not has_column:
        return [f"the manifest lists {len(listing)} neighbourhoods and the table has no column"]
    numbers = {n for n in cells.table["neighbourhood"].to_pylist() if n is not None}
    outside = sorted(n for n in numbers if not 0 <= n < len(listing))
    return (
        [f"numbers outside the list of {len(listing)}: {some([str(n) for n in outside])}"]
        if outside
        else []
    )


def dataset_checks(cells: Cells) -> list[Result]:
    """Every dataset behind the bundle is listed, credited and licensed."""
    datasets = cells.manifest.datasets
    listed = {d.id for d in datasets}
    cited: dict[str, list[str]] = {}
    for indicator in cells.manifest.indicators:
        for dataset in indicator.datasets:
            if dataset not in listed:
                cited.setdefault(dataset, []).append(indicator.id)
    unlisted = [f"{d} (cited by {some(i)})" for d, i in cited.items()]
    unattributed = [d.id for d in datasets if not d.attribution.strip()]
    unknown = [d.id for d in datasets if d.licence == "unknown"]
    return [
        _result(
            DATASETS,
            "Every cited dataset is in the manifest",
            unlisted,
            ok=f"{len(listed)} datasets",
        ),
        _result(DATASETS, "Every dataset has an attribution", unattributed),
        _result(
            DATASETS,
            "No dataset has an unknown licence",
            [f"unknown licence: {some(unknown)}"] if unknown else [],
            warn=True,
        ),
    ]


def allowed(unit: str) -> tuple[float, float | None]:
    """The lowest and the highest value that a unit allows (None where there is no highest)."""
    if unit.startswith("% change"):
        return -100.0, None  # a fall cannot pass all of it, and a rise has no end
    if unit.startswith("%"):
        return 0.0, 100.0
    if "from 0 to 1" in unit:
        return 0.0, 1.0
    return 0.0, None


def value_checks(cells: Cells) -> list[Result]:
    """The values are plausible: in range, scorable, present in enough cells, and not all alike."""
    out_of_range: list[str] = []
    unscorable: list[str] = []
    empty: list[str] = []
    sparse: list[str] = []
    constant: list[str] = []
    checked = 0
    texts = cells.texts()
    for described in cells.described():
        column = described.column
        if column not in cells.columns:
            continue  # the bundle checks report it
        checked += 1
        if column in texts:
            values = [v for v in cells.text(column) if v is not None]
            curve = described.curve
            if curve is not None and curve.shape == "lookup":
                keys = {str(k) for k in curve.scores}
                unknown = sorted({v for v in values if v not in keys})
                if unknown:
                    unscorable.append(f"{column}: {some(unknown)}")
            valued, distinct = len(values), len(set(values))
        else:
            numbers = cells.numbers(column)
            present = numbers[~np.isnan(numbers)]
            low, high = allowed(described.unit)
            if np.isinf(present).any():
                out_of_range.append(f"{column} has infinite values")
            else:
                outside = (present < low - TOLERANCE).sum()
                if high is not None:
                    outside += (present > high + TOLERANCE).sum()
                if outside:
                    top = f" to {high:g}" if high is not None else " or more"
                    out_of_range.append(
                        f"{column} has {outside} values outside {low:g}{top} ({described.unit})"
                    )
            valued, distinct = len(present), len(np.unique(present))
        if valued == 0:
            empty.append(column)
        elif valued / cells.count < ENOUGH:
            sparse.append(f"{column} ({valued / cells.count:.0%})")
        if valued >= 2 and distinct == 1:
            constant.append(column)
    return [
        _result(
            VALUES,
            "Values are finite, not negative, and within their unit's range",
            out_of_range,
            ok=f"{checked} columns",
        ),
        _result(VALUES, "Text values are ones the curve can score", unscorable),
        _result(
            VALUES, "Every indicator has values", [f"no values in {some(empty)}"] if empty else []
        ),
        _result(
            VALUES,
            "At least half of the cells have values",
            [f"under half: {some(sparse)}"] if sparse else [],
            warn=True,
        ),
        _result(
            VALUES,
            "Every indicator varies",
            [f"the same value in every cell: {some(constant)}"] if constant else [],
            warn=True,
        ),
    ]
