import h3
import pyarrow as pa
import pytest

from atlas.catalogue.load import load_catalogue
from atlas.paths import CATALOGUE_DIR
from atlas.qa.cells import read_cells
from atlas.qa.checks import allowed, bundle_checks, dataset_checks, value_checks
from atlas.qa.results import Result
from tests.qa_sample import CELLS, spoil, write_sample


def one(results: list[Result], part: str) -> Result:
    [found] = [r for r in results if part in r.name]
    return found


def replace_column(name: str, values: list):
    def edit(table: pa.Table) -> pa.Table:
        position = table.column_names.index(name)
        return table.set_column(position, name, pa.array(values))

    return edit


# --- the bundle ---


def test_a_sound_bundle_passes_every_check_of_the_bundle(tmp_path):
    results = bundle_checks(read_cells(write_sample(tmp_path)))
    assert len(results) == 5
    assert {r.status for r in results} == {"pass"}, [r for r in results if r.status != "pass"]


def test_a_row_count_that_differs_from_the_manifest_fails(tmp_path):
    folder = spoil(write_sample(tmp_path), manifest=lambda m: m.update(cell_count=8))
    result = one(bundle_checks(read_cells(folder)), "cell count")
    assert result.status == "fail" and "8" in result.detail and "7" in result.detail


def test_cells_out_of_order_or_repeated_fail(tmp_path):
    def reverse(table: pa.Table) -> pa.Table:
        return table.take(list(reversed(range(table.num_rows))))

    result = one(bundle_checks(read_cells(spoil(write_sample(tmp_path), table=reverse))), "sorted")
    assert result.status == "fail"

    repeated = replace_column("cell", [CELLS[0], CELLS[0], *CELLS[2:]])
    folder = spoil(write_sample(tmp_path / "again"), table=repeated)
    assert one(bundle_checks(read_cells(folder)), "sorted").status == "fail"


def test_a_cell_without_an_id_fails_and_does_not_stop_the_other_checks(tmp_path):
    folder = spoil(write_sample(tmp_path), table=replace_column("cell", [None, *CELLS[1:]]))
    results = bundle_checks(read_cells(folder))
    result = one(results, "sorted")
    assert result.status == "fail" and "1 cells have no id" in result.detail
    assert one(results, "H3").status == "pass"  # the cells that have an id are fine
    assert len(results) == 5


def test_a_cell_that_is_not_an_h3_cell_of_the_resolution_fails(tmp_path):
    coarse = h3.cell_to_parent(CELLS[0], 8)  # a real cell, but of resolution 8
    for bad in ("not-a-cell", coarse):
        edit = replace_column("cell", [bad] + CELLS[1:])
        folder = spoil(write_sample(tmp_path / bad), table=edit)
        result = one(bundle_checks(read_cells(folder)), "H3")
        assert result.status == "fail" and bad in result.detail


def test_a_column_the_manifest_lacks_or_the_table_lacks_fails(tmp_path):
    missing = spoil(write_sample(tmp_path / "a"), table=lambda t: t.drop_columns(["diversity"]))
    result = one(bundle_checks(read_cells(missing)), "columns")
    assert result.status == "fail" and "diversity" in result.detail

    def add(table: pa.Table) -> pa.Table:
        return table.append_column("mystery", pa.array([1.0] * table.num_rows))

    extra = spoil(write_sample(tmp_path / "b"), table=add)
    result = one(bundle_checks(read_cells(extra)), "columns")
    assert result.status == "fail" and "mystery" in result.detail


def test_a_neighbourhood_number_outside_the_list_fails(tmp_path):
    edit = replace_column("neighbourhood", [0, 0, 0, 0, 1, 5, None])
    folder = spoil(write_sample(tmp_path), table=edit)
    result = one(bundle_checks(read_cells(folder)), "neighbourhoods")
    assert result.status == "fail" and "5" in result.detail


def test_neighbourhoods_in_the_manifest_need_their_column_and_the_reverse(tmp_path):
    no_column = spoil(
        write_sample(tmp_path / "a"), table=lambda t: t.drop_columns(["neighbourhood"])
    )
    assert one(bundle_checks(read_cells(no_column)), "neighbourhoods").status == "fail"
    no_list = spoil(write_sample(tmp_path / "b"), manifest=lambda m: m.pop("neighbourhoods"))
    assert one(bundle_checks(read_cells(no_list)), "neighbourhoods").status == "fail"


# --- the datasets ---


def test_a_sound_bundle_passes_every_check_of_the_datasets(tmp_path):
    results = dataset_checks(read_cells(write_sample(tmp_path)))
    assert len(results) == 3 and {r.status for r in results} == {"pass"}


def test_an_indicator_that_cites_a_dataset_the_manifest_lacks_fails(tmp_path):
    def drop(manifest: dict) -> None:
        manifest["datasets"] = [d for d in manifest["datasets"] if d["id"] != "tfl-ptal"]

    result = one(dataset_checks(read_cells(spoil(write_sample(tmp_path), manifest=drop))), "cited")
    assert (
        result.status == "fail" and "tfl-ptal" in result.detail and "service-level" in result.detail
    )


def test_a_dataset_without_an_attribution_fails(tmp_path):
    blanked: list[str] = []

    def blank(manifest: dict) -> None:
        manifest["datasets"][0]["attribution"] = " "
        blanked.append(manifest["datasets"][0]["id"])

    folder = spoil(write_sample(tmp_path), manifest=blank)
    result = one(dataset_checks(read_cells(folder)), "attribution")
    assert result.status == "fail" and blanked[0] in result.detail


def test_an_unknown_licence_is_a_warning_and_not_a_failure(tmp_path):
    marked: list[str] = []

    def unknown(manifest: dict) -> None:
        manifest["datasets"][0]["licence"] = "unknown"
        marked.append(manifest["datasets"][0]["id"])

    results = dataset_checks(read_cells(spoil(write_sample(tmp_path), manifest=unknown)))
    result = one(results, "licence")
    assert result.status == "warn" and marked[0] in result.detail
    assert not any(r.status == "fail" for r in results)


# --- the values ---


def test_a_sound_bundle_passes_every_check_of_the_values(tmp_path):
    results = value_checks(read_cells(write_sample(tmp_path)))
    assert len(results) == 5
    assert {r.status for r in results} == {"pass"}, [r for r in results if r.status != "pass"]


@pytest.mark.parametrize(
    ("column", "values"),
    [
        ("station_proximity", [2.0, 3.5, -1.0, 8.0, 12.0, 15.0, 30.0]),  # minutes below zero
        ("gigabit_broadband", [99.0, 98.0, 97.0, 95.0, 90.0, 80.0, 100.5]),  # a share above 100
        ("diversity", [0.7, 0.72, 0.65, 0.6, 0.5, 0.4, 1.2]),  # an index above 1
        ("station_proximity", [2.0, 3.5, float("inf"), 8.0, 12.0, 15.0, 30.0]),
    ],
)
def test_a_value_outside_what_its_unit_allows_fails(tmp_path, column, values):
    folder = spoil(write_sample(tmp_path), table=replace_column(column, values))
    result = one(value_checks(read_cells(folder)), "range")
    assert result.status == "fail" and column in result.detail


def test_a_share_may_be_a_hair_above_100_from_rounding(tmp_path):
    values = [99.0, 98.0, 97.0, 95.0, 90.0, 80.0, 100.0 + 1e-9]
    folder = spoil(write_sample(tmp_path), table=replace_column("gigabit_broadband", values))
    assert one(value_checks(read_cells(folder)), "range").status == "pass"


def test_a_text_value_that_the_curve_cannot_score_fails(tmp_path):
    values = ["6b", "6a", "5", "4", "3", "2", "7"]
    folder = spoil(write_sample(tmp_path), table=replace_column("service_level", values))
    result = one(value_checks(read_cells(folder)), "Text values")
    assert result.status == "fail" and "7" in result.detail and "service_level" in result.detail


def test_an_indicator_with_no_value_in_any_cell_fails(tmp_path):
    values = [None] * 7
    folder = spoil(write_sample(tmp_path), table=replace_column("diversity", values))
    result = one(value_checks(read_cells(folder)), "has values")
    assert result.status == "fail" and "diversity" in result.detail


def test_an_indicator_with_values_in_under_half_the_cells_is_a_warning(tmp_path):
    values = [0.7, 0.72, 0.65, None, None, None, None]
    folder = spoil(write_sample(tmp_path), table=replace_column("diversity", values))
    result = one(value_checks(read_cells(folder)), "half")
    assert result.status == "warn" and "diversity" in result.detail and "43%" in result.detail


def test_a_little_over_half_the_cells_is_enough(tmp_path):
    values = [0.7, 0.72, 0.65, 0.5, None, None, None]  # 4 of 7 is 57%
    folder = spoil(write_sample(tmp_path), table=replace_column("diversity", values))
    assert one(value_checks(read_cells(folder)), "half").status == "pass"


def test_an_indicator_that_never_varies_is_a_warning(tmp_path):
    values = [50.0] * 7
    folder = spoil(write_sample(tmp_path), table=replace_column("gigabit_broadband", values))
    result = one(value_checks(read_cells(folder)), "varies")
    assert result.status == "warn" and "gigabit_broadband" in result.detail


def test_a_column_with_a_single_value_is_sparse_but_does_not_fail_to_vary(tmp_path):
    values = [0.7, None, None, None, None, None, None]
    folder = spoil(write_sample(tmp_path), table=replace_column("diversity", values))
    results = value_checks(read_cells(folder))
    assert one(results, "half").status == "warn"
    assert one(results, "varies").status == "pass"


def test_every_unit_of_the_catalogue_gets_the_range_it_names():
    """The range comes from the wording of the unit, so a unit worded in a new way must be
    noticed: a share has to be bounded by 100, and an index by 1."""
    indicators = built(load_catalogue(CATALOGUE_DIR).factors.factors)
    assert len(indicators) > 30
    for node in indicators:
        unit = node.unit or ""
        if "%" in unit or "percent" in unit.lower():
            assert allowed(unit) == (0.0, 100.0), unit
        elif "0 to 1" in unit:
            assert allowed(unit) == (0.0, 1.0), unit
        else:
            assert allowed(unit) == (0.0, None), unit
            assert "index" not in unit.lower() and "share" not in unit.lower(), unit


def built(nodes):
    found = []
    for node in nodes:
        if node.children is None:
            if node.status == "built":
                found.append(node)
        else:
            found += built(node.children)
    return found


def test_a_choice_options_columns_are_checked_by_their_indicators_unit(tmp_path):
    values = [20.0, 25.0, 30.0, -5.0, 40.0, 45.0, 50.0]
    folder = spoil(write_sample(tmp_path), table=replace_column("faith__hindu", values))
    result = one(value_checks(read_cells(folder)), "range")
    assert result.status == "fail" and "faith__hindu" in result.detail
