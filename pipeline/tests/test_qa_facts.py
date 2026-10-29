import pytest

from atlas.qa.cells import read_cells
from atlas.qa.facts import Facts, expect, fact_checks
from tests.qa_sample import PLACES, write_sample


@pytest.fixture
def cells(tmp_path):
    return read_cells(write_sample(tmp_path), PLACES)


def test_a_fact_that_holds_passes_with_the_numbers_it_found(cells):
    facts = Facts()

    @facts.add("Soho is a short walk from a station", needs=("station_proximity",))
    def short_walk(cells):
        minutes = cells.at("Soho", "station_proximity")
        expect(minutes < 6, f"{minutes:.0f} minutes")
        return f"{minutes:.0f} minutes"

    [result] = fact_checks(cells, facts.all)
    assert (result.group, result.name, result.status) == (
        "Known facts",
        "Soho is a short walk from a station",
        "pass",
    )
    assert result.detail.endswith("minutes")


def test_a_fact_that_does_not_hold_fails_with_what_it_found(cells):
    facts = Facts()

    @facts.add("Soho is a long way from a station", needs=("station_proximity",))
    def long_walk(cells):
        minutes = cells.at("Soho", "station_proximity")
        expect(minutes > 60, f"Soho is {minutes:.0f} minutes from a station")
        return ""

    [result] = fact_checks(cells, facts.all)
    assert result.status == "fail" and "minutes from a station" in result.detail


def test_a_fact_is_skipped_when_the_bundle_lacks_a_column_it_needs(cells):
    facts = Facts()

    @facts.add("Noise is low in Soho", needs=("road_noise", "station_proximity"))
    def quiet(cells):
        raise AssertionError("it should not run")

    [result] = fact_checks(cells, facts.all)
    assert result.status == "skipped" and "road_noise" in result.detail


def test_a_fact_about_a_place_outside_the_bundle_is_skipped(tmp_path):
    cells = read_cells(write_sample(tmp_path), {"Paris": (48.8566, 2.3522)})
    facts = Facts()

    @facts.add("Paris has a station", needs=("station_proximity",))
    def paris(cells):
        return str(cells.at("Paris", "station_proximity"))

    [result] = fact_checks(cells, facts.all)
    assert result.status == "skipped" and "Paris" in result.detail


def test_a_fact_that_breaks_is_a_failure_and_not_a_crash(cells):
    facts = Facts()

    @facts.add("Atlantis has a station", needs=("station_proximity",))
    def atlantis(cells):
        return str(cells.at("Atlantis", "station_proximity"))  # no such place: a mistake

    [result] = fact_checks(cells, facts.all)
    assert result.status == "fail" and "could not be checked" in result.detail
    assert "Atlantis" in result.detail


def test_the_facts_keep_their_order_and_each_has_an_id_from_its_function(cells):
    facts = Facts()

    @facts.add("First")
    def first(cells):
        return ""

    @facts.add("Second")
    def second(cells):
        return ""

    assert [(f.id, f.statement) for f in facts.all] == [("first", "First"), ("second", "Second")]
    assert [r.name for r in fact_checks(cells, facts.all)] == ["First", "Second"]


def test_two_facts_cannot_share_an_id():
    facts = Facts()

    @facts.add("One")
    def same(cells):
        return ""

    with pytest.raises(ValueError, match="same"):

        @facts.add("Two")
        def same(cells):  # noqa: F811
            return ""
