"""The QA report: runs every check on a built bundle and writes the result as `qa.md`."""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from atlas.catalogue.load import Catalogue
from atlas.publish.manifest import Manifest
from atlas.qa.cells import Cells, read_cells
from atlas.qa.changes import Snapshot, compare, snapshot
from atlas.qa.checks import bundle_checks, dataset_checks, value_checks
from atlas.qa.facts import fact_checks
from atlas.qa.format import number, share
from atlas.qa.regional import Regional
from atlas.qa.regional import regional as regional_of
from atlas.qa.relations import relation_checks
from atlas.qa.results import Result, some
from atlas.qa.stats import ColumnStats, FactorCoverage, column_stats, factor_coverage
from atlas.scoring.engine import LOW_COVERAGE

NONE = "–"  # a cell of a table that has nothing to show
WORDS = {"pass": "Pass", "warn": "Warning", "fail": "Fail", "skipped": "Skipped"}


@dataclass(frozen=True)
class DatasetRow:
    id: str
    licence: str
    commercial_use: bool | None  # None where the catalogue does not know the dataset
    date: str
    used_for: list[str]
    attribution: str


@dataclass(frozen=True)
class Report:
    region: str
    version: str
    cells: int
    indicators: int
    columns: int
    results: list[Result]
    stats: list[ColumnStats]
    factors: list[FactorCoverage]
    datasets: list[DatasetRow]
    previous: str | None  # the version this build is compared with
    changes: list[str] | None  # None where there is no previous build to compare with
    published: bool = False  # whether `latest.json` named this version when it was checked
    # False where the previous build is on disk but in a format this version cannot read, such as
    # a manifest with a curve shape that has gone (D25).
    previous_readable: bool = True

    @property
    def failed(self) -> bool:
        return any(r.status == "fail" for r in self.results)

    def count(self, status: str) -> int:
        return sum(1 for r in self.results if r.status == status)

    def markdown(self) -> str:
        return "\n".join(_lines(self)) + "\n"


def check_bundle(
    folder: Path,
    catalogue: Catalogue,
    *,
    previous: Path | None = None,
    published: bool = False,
    regional: Regional | None = None,
) -> Report:
    """Runs every check on the bundle in `folder`. `previous` is the bundle it replaces, to compare
    with, `published` says whether it is the published one already, and `regional` replaces the
    region's own places, facts and relations."""
    region_id = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))["region"]["id"]
    regional = regional or regional_of(region_id)
    cells = read_cells(folder, regional.places)
    results = [
        *bundle_checks(cells),
        *dataset_checks(cells),
        *value_checks(cells),
        *relation_checks(cells, regional.relations),
        *fact_checks(cells, regional.facts),
    ]
    stats = column_stats(cells)
    changes = None
    readable = True
    if previous is not None and (previous / "manifest.json").exists():
        # A build in an older format (such as one with the percentile curve, before D25) cannot be
        # read by this version, so it is named and not compared with.
        readable = _format_of(previous) == FORMAT_VERSION
        if readable:
            now = Snapshot(cells.count, stats, cells.manifest.datasets)
            changes = compare(now, snapshot(read_cells(previous)))
    return Report(
        region=cells.manifest.region.name,
        version=cells.manifest.version,
        cells=cells.count,
        indicators=len(cells.manifest.indicators),
        columns=len(cells.described()),
        results=results,
        stats=stats,
        factors=factor_coverage(cells),
        datasets=_datasets(cells, catalogue),
        previous=previous.name if previous is not None else None,
        changes=changes,
        published=published,
        previous_readable=readable,
    )


FORMAT_VERSION = Manifest.model_fields["format_version"].default


def _format_of(folder: Path) -> object:
    """The format version that a bundle's manifest says it is in."""
    return json.loads((folder / "manifest.json").read_text(encoding="utf-8")).get("format_version")


def write_report(folder: Path, report: Report) -> Path:
    path = folder / "qa.md"
    path.write_text(report.markdown(), encoding="utf-8", newline="\n")
    return path


def _datasets(cells: Cells, catalogue: Catalogue) -> list[DatasetRow]:
    commercial = {d.id: d.commercial_use for d in catalogue.datasets.datasets}
    used_for: dict[str, list[str]] = {}
    for indicator in cells.manifest.indicators:
        for dataset in indicator.datasets:
            used_for.setdefault(dataset, []).append(indicator.name)
    return [
        DatasetRow(
            id=d.id,
            licence=d.licence,
            commercial_use=commercial.get(d.id),
            date=d.date,
            used_for=used_for.get(d.id, ["The region's boundary and neighbourhoods"]),
            attribution=d.attribution,
        )
        for d in cells.manifest.datasets
    ]


# --- the markdown ---


def _plural(n: int, one: str, many: str) -> str:
    return f"{n:,} {one if n == 1 else many}"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    return lines + ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]


def _lines(report: Report) -> list[str]:
    counts = Counter(r.status for r in report.results)
    if not report.failed:
        verdict = "**Passed.**"
    elif report.published:
        verdict = (
            "**Failed.** This version is already published: correct the cause and publish another."
        )
    else:
        verdict = "**Failed, so it is not published.**"
    lines = [
        f"# QA report: {report.region}",
        "",
        f"Version `{report.version}`: {_plural(report.cells, 'cell', 'cells')}, "
        f"{_plural(report.indicators, 'indicator', 'indicators')} "
        f"({_plural(report.columns, 'column', 'columns')}).",
        "",
        f"{verdict} {_plural(counts['pass'], 'check', 'checks')} passed, "
        f"{_plural(counts['warn'], 'warning', 'warnings')}, {counts['fail']} failed, "
        f"{counts['skipped']} skipped.",
        "",
        "## What needs a look",
        "",
        *_look(report.results),
        "",
        "## Data by indicator",
        "",
        "The share of cells with a value, then the spread of the values. Full marks and no marks "
        "are the shares of the cells with a value that a ramp or an ideal-range curve scores 1 "
        "and 0: a curve that gives nearly every cell the same score adds little contrast.",
        "",
        *_data(report.stats),
        "",
        "### Region ramps",
        "",
        "The ends that the build took from the region's own values (D25): a cell scores 0 at the "
        "first and 1 at the second, and a cell past an end scores as that end. The build leaves "
        "out up to 1 in 100 cells at each end, but never a value that a whole area shares. The "
        "shares past each end count every cell with a value, so they include the cells with few "
        "homes, which set no end.",
        "",
        *_region_ramps(report.stats),
        "",
        "### Text indicators",
        "",
        *_categories(report.stats),
        "",
        "## Factors",
        "",
        "How many of each factor's indicators a cell has, whatever the weights. A choice "
        "indicator counts when any of its options has a value.",
        "",
        *_factors(report.factors),
        "",
        "## Datasets",
        "",
        *_datasets_table(report.datasets),
        "",
        "## Checks of the bundle",
        "",
        *_table(
            ["Group", "Check", "Result", "Found"],
            [
                [r.group, r.name, WORDS[r.status], r.detail]
                for r in report.results
                if r.group in ("The bundle", "Datasets", "Values")
            ],
        ),
        "",
        "## Relations",
        "",
        *_relations(report.results),
        "",
        "## Known facts",
        "",
        *_facts(report.results),
        "",
        "## Changes since the previous build",
        "",
        *_changes(report),
    ]
    return lines


def describe(result: Result) -> str:
    """A result as one plain line: its status, group and name, then what was found."""
    return f"{WORDS[result.status]}, {result.group}: {result.name}. {result.detail}".rstrip()


def _look(results: Sequence[Result]) -> list[str]:
    order = {"fail": 0, "warn": 1, "skipped": 2}
    shown = sorted(
        (r for r in results if r.status in order), key=lambda r: order[r.status]
    )  # a stable sort keeps the order within a status
    if not shown:
        return ["Nothing."]
    return [f"- **{WORDS[r.status]}**, {r.group}: {r.name}. {r.detail}".rstrip() for r in shown]


def _data(stats: Sequence[ColumnStats]) -> list[str]:
    headers = [
        "Indicator", "Unit", "Cells with a value", "Lowest", "5th percentile", "Median",
        "95th percentile", "Highest", "Full marks", "No marks",
    ]  # fmt: skip

    def spread(value: float | None) -> str:
        return NONE if value is None else number(value)

    def marks(value: float | None) -> str:
        return NONE if value is None else share(value)

    rows = [
        [
            s.label,
            s.unit,
            share(s.valued),
            spread(s.lowest),
            spread(s.p5),
            spread(s.median),
            spread(s.p95),
            spread(s.highest),
            marks(s.full),
            marks(s.none),
        ]  # fmt: skip
        for s in stats
    ]
    return _table(headers, rows)


def _region_ramps(stats: Sequence[ColumnStats]) -> list[str]:
    headers = ["Indicator", "Unit", "Scores 0 at", "Scores 1 at", "Scale", "Past 0", "Past 1"]
    rows = []
    for s in stats:
        ramp = s.region_ramp
        if ramp is None:
            continue
        scale = "log" if ramp.log else "linear"
        if ramp.log and ramp.offset:
            scale = f"log of the value + {number(ramp.offset)}"
        rows.append(
            [
                s.label,
                s.unit,
                number(ramp.t0),
                number(ramp.t1),
                scale,
                share(s.past_none or 0.0),
                share(s.past_full or 0.0),
            ]
        )
    return _table(headers, rows) if rows else ["None."]


def _categories(stats: Sequence[ColumnStats]) -> list[str]:
    lines = []
    for s in stats:
        if s.categories is None:
            continue
        parts = [
            f"{c.value}: {share(c.share)} "
            + (f"(scores {c.score:.2f})" if c.score is not None else "(not scored)")
            for c in s.categories
        ]
        lines.append(f"- **{s.label}** ({s.unit}): " + ", ".join(parts) + ".")
    return lines or ["None."]


def _factors(factors: Sequence[FactorCoverage]) -> list[str]:
    headers = [
        "Factor", "Indicators", "Average share with data", "Cells with none",
        f"Cells with under {LOW_COVERAGE:.0%} of the indicators",
    ]  # fmt: skip
    rows = [
        [f.name, str(f.indicators), share(f.mean), share(f.unscored), share(f.low)] for f in factors
    ]
    return _table(headers, rows)


def _datasets_table(datasets: Sequence[DatasetRow]) -> list[str]:
    marks = {True: "Yes", False: "No", None: NONE}
    headers = ["Dataset", "Licence", "Commercial use", "Date", "Used for", "Attribution"]
    rows = [
        [d.id, d.licence, marks[d.commercial_use], d.date, some(d.used_for), d.attribution]
        for d in datasets
    ]
    return _table(headers, rows)


def _relations(results: Sequence[Result]) -> list[str]:
    rows = [[r.name, WORDS[r.status], r.detail, r.why] for r in results if r.group == "Relations"]
    if not rows:
        return ["No relations are listed for this region."]
    return _table(["Check", "Result", "Found", "Why they should agree"], rows)


def _facts(results: Sequence[Result]) -> list[str]:
    rows = [[r.name, WORDS[r.status], r.detail] for r in results if r.group == "Known facts"]
    if not rows:
        return ["No known facts are listed for this region."]
    return _table(["Fact", "Result", "Found"], rows)


def _changes(report: Report) -> list[str]:
    if report.changes is None and report.previous is not None and not report.previous_readable:
        return [
            f"The previous build `{report.previous}` is in an older format that this version "
            "cannot read, so there is nothing to compare with."
        ]
    if report.changes is None and report.previous is not None:
        return [
            f"The previous build `{report.previous}` is no longer on disk, "
            "so there is nothing to compare with."
        ]
    if report.changes is None:
        return ["There is no previous build to compare with."]
    if not report.changes:
        return [f"No change since `{report.previous}`."]
    return [f"Compared with `{report.previous}`.", "", *[f"- {line}" for line in report.changes]]
