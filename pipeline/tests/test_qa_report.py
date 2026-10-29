from dataclasses import replace

import pytest

from atlas.catalogue.load import load_catalogue
from atlas.paths import CATALOGUE_DIR
from atlas.qa.facts import Facts, expect
from atlas.qa.regional import Regional
from atlas.qa.relations import Relation
from atlas.qa.report import check_bundle, write_report
from tests.qa_sample import PLACES, spoil, write_sample

NOTHING_REGIONAL = Regional(places={}, facts=[], relations=[])


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue(CATALOGUE_DIR)


def report_of(folder, catalogue, **kwargs):
    kwargs.setdefault("regional", NOTHING_REGIONAL)
    return check_bundle(folder, catalogue, **kwargs)


def table_row(markdown: str, first_cell: str) -> list[str]:
    """The cells of the table row that starts with `first_cell`."""
    [line] = [ln for ln in markdown.splitlines() if ln.startswith(f"| {first_cell} |")]
    return [cell.strip() for cell in line.strip("|").split(" | ")]


def section(markdown: str, title: str) -> str:
    """The text of one `## title` section."""
    parts = markdown.split(f"## {title}\n")
    assert len(parts) == 2, f"no section {title}"
    return parts[1].split("\n## ")[0]


def test_the_report_of_a_sound_bundle_says_that_it_passed(tmp_path, catalogue):
    folder = write_sample(tmp_path)
    report = report_of(folder, catalogue)
    text = report.markdown()
    assert not report.failed
    assert text.startswith("# QA report: London\n")
    assert f"`{folder.name}`" in text and "7 cells" in text and "5 indicators" in text
    assert "**Passed.** 13 checks passed, 0 warnings, 0 failed, 0 skipped." in text
    assert section(text, "What needs a look").strip() == "Nothing."


def test_a_large_number_of_cells_has_a_thousands_separator(tmp_path, catalogue):
    report = report_of(write_sample(tmp_path), catalogue)
    assert "16,668 cells" in replace(report, cells=16668).markdown()


def test_a_failed_check_makes_the_report_fail_and_is_listed_first(tmp_path, catalogue):
    folder = spoil(write_sample(tmp_path), manifest=lambda m: m.update(cell_count=8))
    report = report_of(folder, catalogue)
    text = report.markdown()
    assert report.failed
    assert "**Failed, so it is not published.**" in text
    look = section(text, "What needs a look")
    assert "Fail" in look and "The rows match the manifest's cell count" in look
    assert "the table has 7 rows and the manifest says 8" in look


def test_warnings_are_listed_but_do_not_fail_the_report(tmp_path, catalogue):
    def unknown(manifest: dict) -> None:
        manifest["datasets"][0]["licence"] = "unknown"

    report = report_of(spoil(write_sample(tmp_path), manifest=unknown), catalogue)
    text = report.markdown()
    assert not report.failed
    assert "**Passed.** 12 checks passed, 1 warning, 0 failed, 0 skipped." in text
    assert "Warning" in section(text, "What needs a look")


def test_the_data_table_has_a_row_for_each_column_with_its_spread(tmp_path, catalogue):
    text = report_of(write_sample(tmp_path), catalogue).markdown()
    row = table_row(text, "Walk to the nearest station")
    assert row == [
        "Walk to the nearest station", "minutes on foot", "100%",
        "2.00", "2.45", "8.00", "25.5", "30.0", "42.9%", "14.3%",
    ]  # fmt: skip
    # A percentile curve has no full or no marks, and a text column no spread.
    assert table_row(text, "Diversity")[-2:] == ["–", "–"]
    ptal = table_row(text, "Service level")
    assert ptal[2] == "100%" and ptal[3:] == ["–"] * 7
    assert table_row(text, "Faith (Sikh)")[1] == "minutes on foot"


def test_a_text_column_lists_its_categories_with_their_scores(tmp_path, catalogue):
    text = report_of(write_sample(tmp_path), catalogue).markdown()
    categories = section(text, "Text indicators")
    assert "**Service level** (PTAL band)" in categories
    assert "6b: 14.3% (scores 1.00)" in categories and "1b: 14.3% (scores 0.25)" in categories


def test_the_factors_table_shows_how_well_each_factor_is_covered(tmp_path, catalogue):
    folder = write_sample(tmp_path, columns={"station-proximity": [2, None, 5, 8, 12, 15, 30]})
    text = report_of(folder, catalogue).markdown()
    assert table_row(text, "Transport") == ["Transport", "2", "92.9%", "0%", "14.3%"]


def test_the_datasets_table_marks_commercial_use_from_the_catalogue(tmp_path, catalogue):
    def add_laei(manifest: dict) -> None:
        manifest["datasets"].append({**manifest["datasets"][0], "id": "laei", "licence": "unknown"})

    text = report_of(spoil(write_sample(tmp_path), manifest=add_laei), catalogue).markdown()
    ptal = table_row(text, "tfl-ptal")
    assert ptal[1] == "OGL-UK-2.0" and ptal[2] == "Yes"
    assert table_row(text, "laei")[2] == "No"
    assert "Service level" in ptal[4]  # what it is used for


def test_a_pipe_or_a_line_break_in_a_dataset_does_not_break_its_row(tmp_path, catalogue):
    def awkward(manifest: dict) -> None:
        manifest["datasets"][0]["attribution"] = "One | two\nthree"

    text = report_of(spoil(write_sample(tmp_path), manifest=awkward), catalogue).markdown()
    assert "One \\| two three" in text


def test_the_regions_relations_and_facts_have_sections_with_what_they_found(tmp_path, catalogue):
    facts = Facts()

    @facts.add("Soho is a short walk from a station", needs=("station_proximity",))
    def short(cells):
        minutes = cells.at("Soho", "station_proximity")
        expect(minutes < 6, f"{minutes:.0f} minutes")
        return f"{minutes:.0f} minutes"

    relation = Relation("station_proximity", "service_level", -1, 0.5, "PTAL counts stations")
    regional = Regional(places=PLACES, facts=facts.all, relations=[relation])
    text = report_of(write_sample(tmp_path), catalogue, regional=regional).markdown()
    [relation_row] = [
        r for r in section(text, "Relations").splitlines() if r.startswith("| Walk to the")
    ]
    assert (
        "Pass" in relation_row
        and "-1.00" in relation_row
        and "PTAL counts stations" in relation_row
    )
    fact_row = table_row(text, "Soho is a short walk from a station")
    assert fact_row[1] == "Pass" and fact_row[2].endswith("minutes")


def test_a_region_without_relations_or_facts_says_so(tmp_path, catalogue):
    text = report_of(write_sample(tmp_path), catalogue).markdown()
    assert "No relations are listed for this region." in section(text, "Relations")
    assert "No known facts are listed for this region." in section(text, "Known facts")


def test_a_report_with_no_previous_build_says_so(tmp_path, catalogue):
    text = report_of(write_sample(tmp_path), catalogue).markdown()
    changes = section(text, "Changes since the previous build")
    assert "There is no previous build to compare with." in changes


def test_a_previous_build_that_agrees_is_no_change(tmp_path, catalogue):
    previous = write_sample(tmp_path / "a")
    now = write_sample(tmp_path / "b")  # the same data gives the same version, in another place
    assert now.name == previous.name
    text = report_of(now, catalogue, previous=previous).markdown()
    assert f"No change since `{previous.name}`." in section(
        text, "Changes since the previous build"
    )


def test_a_previous_build_that_differs_lists_what_changed(tmp_path, catalogue):
    previous = write_sample(tmp_path / "a")
    now = write_sample(tmp_path / "b", columns={"station-proximity": [12, 13, 14, 15, 16, 17, 18]})
    text = report_of(now, catalogue, previous=previous).markdown()
    changes = section(text, "Changes since the previous build")
    assert f"Compared with `{previous.name}`." in changes
    assert "- Walk to the nearest station: the median moved from 8.00 to 15.0" in changes


def test_a_previous_build_that_is_gone_is_named_and_not_compared_with(tmp_path, catalogue):
    report = report_of(write_sample(tmp_path), catalogue, previous=tmp_path / "gone")
    assert report.previous == "gone" and report.changes is None
    assert "The previous build `gone` is no longer on disk" in report.markdown()


def test_the_same_bundle_gives_the_same_report_with_no_date_in_it(tmp_path, catalogue):
    one = report_of(write_sample(tmp_path / "a"), catalogue).markdown()
    two = report_of(write_sample(tmp_path / "b"), catalogue).markdown()
    assert one == two


def test_the_report_is_written_beside_the_bundle(tmp_path, catalogue):
    folder = write_sample(tmp_path)
    report = report_of(folder, catalogue)
    path = write_report(folder, report)
    assert path == folder / "qa.md"
    assert path.read_text(encoding="utf-8") == report.markdown()
    assert report.markdown().endswith("\n") and not report.markdown().endswith("\n\n")
