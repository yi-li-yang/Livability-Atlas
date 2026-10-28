from atlas.catalogue.checks import check_datasets, check_factors
from atlas.catalogue.models import DatasetsFile, FactorsFile

DATASET = {
    "id": "laei",
    "name": "LAEI",
    "publisher": "GLA",
    "url": "https://example.org/laei",
    "tier": "city",
    "area": "London",
    "resolution": "20 m grid",
    "date": 2022,
    "licence": "OGL-UK-3.0",
    "licence_checked": "2026-10-24",
    "public_build": True,
    "attribution": "GLA.",
    "tells": ["NO2"],
}
INDICATOR = {
    "id": "no2",
    "name": "NO2",
    "default_weight": 3,
    "status": "researched",
    "unit": "µg/m³",
    "preference_type": "fixed",
    "evidence_type": "direct",
    "comparable_across_regions": True,
    "method": "Mean.",
    "datasets": ["laei"],
    "curve_reason": "WHO.",
}


def top(**fields):
    return {
        "id": "environment",
        "name": "Environment",
        "default_weight": 4,
        "weight_reason": "Four of five sources.",
        "scales": ["within-city", "across-cities"],
        "children": [INDICATOR],
        **fields,
    }


def problems(factors, datasets=(DATASET,)):
    return check_factors(
        FactorsFile.model_validate({"factors": list(factors)}),
        DatasetsFile.model_validate({"datasets": list(datasets)}),
    )


def test_a_sound_catalogue_has_no_problems():
    assert problems([top()]) == []


def test_an_id_is_used_once_across_the_whole_tree():
    clash = top(id="no2")
    assert "no2: this id is used more than once." in problems([top(), clash])


def test_dataset_ids_are_unique():
    doc = DatasetsFile.model_validate({"datasets": [DATASET, DATASET]})
    assert check_datasets(doc) == ["dataset laei: this id is used more than once."]


def test_a_top_level_factor_gives_its_weight_reason_even_at_3():
    found = problems([top(default_weight=3, weight_reason=None)])
    assert found == ["environment: a top-level factor needs a weight_reason (D14)."]


def test_a_sub_factor_off_the_default_gives_its_reason():
    found = problems([top(children=[{**INDICATOR, "default_weight": 1}])])
    assert found == ["no2: a default_weight other than 3 needs a weight_reason."]


def test_a_top_level_factor_lists_its_scales():
    assert "environment: a top-level factor must list its scales." in problems([top(scales=None)])


def test_a_sub_factor_may_not_add_a_scale_its_parent_lacks():
    parent = top(scales=["within-city"], children=[{**INDICATOR, "scales": ["across-cities"]}])
    assert "no2: it lists a scale that its parent does not have." in problems([parent])


def test_a_sub_factor_may_list_a_subset_of_its_parent_scales():
    child = {**INDICATOR, "scales": ["within-city"]}
    assert problems([top(children=[child])]) == []


def test_an_indicator_names_datasets_that_exist():
    child = {**INDICATOR, "datasets": ["laei", "nowhere"]}
    assert problems([top(children=[child])]) == ["no2: datasets.yaml has no dataset nowhere."]


def test_an_indicator_lists_a_dataset_once():
    child = {**INDICATOR, "datasets": ["laei", "laei"]}
    assert problems([top(children=[child])]) == ["no2: dataset laei is listed twice."]


def test_a_ranking_needs_a_credibility_rating_on_each_dataset():
    child = {**INDICATOR, "evidence_type": "ranking"}
    assert problems([top(children=[child])]) == [
        "no2: evidence type ranking needs a credibility rating on dataset laei."
    ]
    rated = {**DATASET, "credibility": "high", "credibility_reason": "Open method."}
    assert problems([top(children=[child])], datasets=(rated,)) == []
