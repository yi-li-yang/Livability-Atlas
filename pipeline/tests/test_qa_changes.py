from dataclasses import replace

import pytest

from atlas.qa.cells import read_cells
from atlas.qa.changes import Snapshot, compare, snapshot
from atlas.qa.format import number, share
from atlas.qa.stats import ColumnStats
from tests.qa_sample import spoil, write_sample


def changes_since(now, before) -> list[str]:
    return compare(snapshot(now), snapshot(before))


def stat(**changes) -> ColumnStats:
    base = ColumnStats(
        column="minutes",
        indicator="minutes",
        name="Walk to a station",
        unit="minutes on foot",
        option=None,
        valued=1.0,
        median=10.0,
    )
    return replace(base, **changes)


def shot(*stats: ColumnStats, cells: int = 100, datasets=()) -> Snapshot:
    return Snapshot(cells=cells, stats=list(stats), datasets=list(datasets))


def test_two_identical_builds_have_no_change():
    assert compare(shot(stat()), shot(stat())) == []


def test_a_different_number_of_cells_is_reported():
    lines = compare(shot(stat(), cells=120), shot(stat(), cells=100))
    assert lines == ["Cells: 100 before, 120 now."]


def test_an_indicator_added_or_removed_is_reported_by_its_label():
    gone = stat(column="old", name="Old measure")
    new = stat(column="new", name="New measure", option="Sikh")
    lines = compare(shot(stat(), new), shot(stat(), gone))
    assert lines == ["Added: New measure (Sikh).", "Removed: Old measure."]


@pytest.mark.parametrize(
    ("before", "now", "moved"),
    [(0.700, 0.709, False), (0.700, 0.711, True), (0.700, 0.689, True), (0.700, 0.691, False)],
)
def test_a_share_of_cells_with_a_value_that_moves_a_point_or_more_is_reported(before, now, moved):
    lines = compare(shot(stat(valued=now)), shot(stat(valued=before)))
    assert bool(lines) is moved
    if moved:
        assert lines == [
            f"Walk to a station: the share of cells with a value moved from "
            f"{share(before)} to {share(now)}."
        ]


@pytest.mark.parametrize(
    ("before", "now", "moved"),
    [(10.0, 10.4, False), (10.0, 10.6, True), (10.0, 9.4, True), (10.0, 9.6, False)],
)
def test_a_median_that_moves_five_per_cent_or_more_is_reported(before, now, moved):
    lines = compare(shot(stat(median=now)), shot(stat(median=before)))
    assert bool(lines) is moved
    if moved:
        assert lines == [
            f"Walk to a station: the median moved from {number(before)} to {number(now)} "
            "(minutes on foot)."
        ]


def test_a_column_that_loses_all_its_values_is_reported_by_its_coverage():
    [line] = compare(shot(stat(median=None, valued=0.0)), shot(stat(median=10.0, valued=1.0)))
    assert "the share of cells with a value moved from 100% to 0%" in line


def test_a_text_column_is_compared_by_coverage_alone():
    text = stat(median=None)
    assert compare(shot(text), shot(text)) == []


def test_a_dataset_added_removed_or_re_dated_is_reported(tmp_path):
    before = read_cells(write_sample(tmp_path / "a"))

    def edit(manifest: dict) -> None:
        manifest["datasets"] = [d for d in manifest["datasets"] if d["id"] != "naptan"]
        for dataset in manifest["datasets"]:
            if dataset["id"] == "tfl-ptal":
                dataset["date"] = "2099-01"
        manifest["datasets"].append({**manifest["datasets"][0], "id": "zzz-new"})

    now = read_cells(spoil(write_sample(tmp_path / "b"), manifest=edit))
    lines = changes_since(now, before)
    assert "Added dataset: zzz-new." in lines
    assert "Removed dataset: naptan." in lines
    assert any(
        line.startswith("Dataset tfl-ptal: the date moved from") and "2099-01" in line
        for line in lines
    )
    assert len(lines) == 3


def test_a_real_pair_of_bundles_compares_to_no_change_when_identical(tmp_path):
    one = read_cells(write_sample(tmp_path / "a"))
    other = read_cells(write_sample(tmp_path / "b"))
    assert changes_since(one, other) == []
    assert snapshot(one).cells == 7


def test_a_real_pair_of_bundles_reports_a_changed_column(tmp_path):
    before = read_cells(write_sample(tmp_path / "a"))
    now = read_cells(
        write_sample(tmp_path / "b", columns={"station-proximity": [12, 13, 14, 15, 16, 17, 18]})
    )
    assert changes_since(now, before) == [
        "Walk to the nearest station: the median moved from 8.00 to 15.0 (minutes on foot)."
    ]
