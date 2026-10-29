from atlas.qa.cells import read_cells
from atlas.qa.relations import Relation, relation_checks
from tests.qa_sample import write_sample

# In the sample, a longer walk to a station goes with a lower service level, perfectly.
WALK_AND_LEVEL = Relation("station_proximity", "service_level", -1, 0.5, "PTAL counts stations")


def check(tmp_path, relation, **columns):
    [result] = relation_checks(read_cells(write_sample(tmp_path, columns=columns)), [relation])
    return result


def test_two_columns_that_move_the_way_expected_pass_with_their_correlation(tmp_path):
    result = check(tmp_path, WALK_AND_LEVEL)
    assert result.group == "Relations" and result.status == "pass"
    assert "-1.00" in result.detail and "7 cells" in result.detail


def test_a_text_column_is_ranked_by_the_scores_of_its_lookup_curve(tmp_path):
    reversed_bands = [
        "1b",
        "2",
        "3",
        "4",
        "5",
        "6a",
        "6b",
    ]  # the best band where the walk is longest
    result = check(tmp_path, WALK_AND_LEVEL, **{"service-level": reversed_bands})
    assert result.status == "fail" and "+1.00" in result.detail


def test_the_wrong_sign_fails(tmp_path):
    relation = Relation("station_proximity", "service_level", 1, 0.5, "the wrong way round")
    result = check(tmp_path, relation)
    assert result.status == "fail" and "-1.00" in result.detail


def test_a_correlation_weaker_than_the_floor_fails(tmp_path):
    # Diversity falls with the walk (-0.96 in the sample), which is short of a floor of 0.99.
    relation = Relation("station_proximity", "diversity", -1, 0.99, "a made-up floor")
    result = check(tmp_path, relation)
    assert result.status == "fail" and "-0.96" in result.detail and "0.99" in result.detail


def test_a_correlation_that_reaches_the_floor_passes(tmp_path):
    relation = Relation("station_proximity", "diversity", -1, 0.9, "a made-up floor")
    assert check(tmp_path, relation).status == "pass"


def test_the_result_names_the_two_indicators_and_the_way_they_move(tmp_path):
    opposite = check(tmp_path, WALK_AND_LEVEL)
    assert opposite.name == "Walk to the nearest station and Service level move in opposite ways"
    together = check(
        tmp_path / "t", Relation("gigabit_broadband", "station_proximity", 1, 0.5, "made up")
    )
    assert together.name == "Gigabit broadband and Walk to the nearest station rise together"


def test_a_relation_names_an_option_by_its_indicator_and_its_name(tmp_path):
    relation = Relation("faith__hindu", "faith__sikh", 1, 0.5, "both are walks to a faith's places")
    result = check(tmp_path, relation)
    assert result.name == "Faith (Hindu) and Faith (Sikh) rise together"


def test_a_relation_on_a_column_the_bundle_lacks_is_skipped(tmp_path):
    relation = Relation("station_proximity", "nope", -1, 0.5, "no such column")
    result = check(tmp_path, relation)
    assert result.status == "skipped" and "nope" in result.detail


def test_a_relation_on_too_few_cells_is_skipped(tmp_path):
    values = [2, None, None, None, None, None, 30]
    result = check(tmp_path, WALK_AND_LEVEL, **{"station-proximity": values})
    assert result.status == "skipped" and "2 cells" in result.detail


def test_a_relation_on_a_column_that_never_varies_is_skipped(tmp_path):
    result = check(tmp_path, WALK_AND_LEVEL, **{"station-proximity": [5.0] * 7})
    assert result.status == "skipped" and "station_proximity" in result.detail


def test_only_the_cells_with_both_values_are_ranked(tmp_path):
    values = [2, 3.5, 5, 8, 12, None, None]
    result = check(tmp_path, WALK_AND_LEVEL, **{"station-proximity": values})
    assert result.status == "pass" and "5 cells" in result.detail
