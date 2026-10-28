import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from atlas.catalogue.models import Dataset, Factor, IdealRange


def factor(**fields):
    return {"id": "air-quality", "name": "Air quality", "default_weight": 3, **fields}


RESEARCHED = {
    "status": "researched",
    "unit": "µg/m³",
    "preference_type": "fixed",
    "evidence_type": "direct",
    "comparable_across_regions": True,
    "method": "The mean over the cell.",
    "datasets": ["laei"],
    "curve_reason": "The WHO's 2021 guideline.",
}
RAMP = {"shape": "ramp", "t0": 25, "t1": 5}


def dataset(**fields):
    return {
        "id": "laei",
        "name": "London Atmospheric Emissions Inventory",
        "publisher": "Greater London Authority",
        "url": "https://data.london.gov.uk/dataset/laei",
        "tier": "city",
        "area": "Greater London",
        "resolution": "20 m grid",
        "date": 2022,
        "licence": "OGL-UK-3.0",
        "licence_checked": "2026-10-24",
        "public_build": True,
        "attribution": "Contains public sector information.",
        "tells": ["Annual mean NO2"],
        **fields,
    }


def problem(model, data):
    with pytest.raises(ValidationError) as caught:
        model.model_validate(data)
    return str(caught.value)


# --- factors ---


def test_an_idea_needs_only_a_name_and_a_weight():
    assert Factor.model_validate(factor()).status is None


def test_a_researched_indicator_needs_its_research():
    assert "at status researched, it needs unit" in problem(Factor, factor(status="researched"))


def test_a_complete_researched_indicator_passes():
    assert Factor.model_validate(factor(**RESEARCHED)).unit == "µg/m³"


def test_a_spiked_indicator_needs_a_curve():
    assert "it needs curve" in problem(Factor, factor(**{**RESEARCHED, "status": "spiked"}))


def test_an_unknown_field_is_rejected():
    assert "Extra inputs are not permitted" in problem(Factor, factor(colour="red"))


@pytest.mark.parametrize("weight", [-1, 6, True, 2.5])
def test_a_weight_must_be_a_whole_number_from_0_to_5(weight):
    assert "default_weight" in problem(Factor, factor(default_weight=weight))


def test_an_id_must_be_kebab_case():
    assert "id" in problem(Factor, factor(id="Air Quality"))


def test_a_factor_with_children_cannot_be_an_indicator():
    child = factor(id="no2")
    assert "cannot have unit" in problem(Factor, factor(children=[child], unit="µg/m³"))
    assert "none of its own" in problem(Factor, factor(children=[child], status="idea"))
    assert "non-empty" in problem(Factor, factor(children=[]))


def test_a_curve_needs_a_reason():
    assert "needs a curve_reason" in problem(Factor, factor(curve=RAMP))


def test_a_user_range_indicator_needs_an_ideal_range_curve():
    data = factor(curve=RAMP, curve_reason="Why.", preference_type="user-range")
    assert "needs an ideal-range curve" in problem(Factor, data)


def test_a_preference_type_must_be_known():
    assert "preference_type" in problem(Factor, factor(preference_type="whim"))


# --- curves ---


def test_a_ramp_needs_two_different_numbers():
    assert "two different numbers" in problem(
        Factor, factor(curve_reason="Why.", curve={"shape": "ramp", "t0": 5, "t1": 5})
    )


def test_a_lookup_scores_run_from_0_to_1():
    bad = {"shape": "lookup", "scores": {"low": 1.5}}
    assert "scores" in problem(Factor, factor(curve_reason="Why.", curve=bad))
    empty = {"shape": "lookup", "scores": {}}
    assert "scores" in problem(Factor, factor(curve_reason="Why.", curve=empty))


def test_a_lookup_may_use_numbers_as_categories():
    curve = {"shape": "lookup", "scores": {1: 1, 2: 0.5}}
    assert Factor.model_validate(factor(curve_reason="Why.", curve=curve)).curve is not None


def test_a_percentile_needs_a_direction():
    assert "better" in problem(
        Factor, factor(curve_reason="Why.", curve={"shape": "percentile", "better": "sideways"})
    )


def test_an_unknown_curve_shape_is_rejected():
    assert "shape" in problem(Factor, factor(curve_reason="Why.", curve={"shape": "wave"}))


def test_an_ideal_range_may_have_a_single_best_value():
    assert IdealRange(shape="ideal-range", l0=14, l1=20, u1=20, u0=32).l1 == 20


finite = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)
four_distinct = st.lists(finite, min_size=4, max_size=4, unique=True)


@given(four_distinct)
def test_an_ideal_range_accepts_numbers_in_order(values):
    l0, l1, u1, u0 = sorted(values)
    IdealRange(shape="ideal-range", l0=l0, l1=l1, u1=u1, u0=u0)


@given(four_distinct)
def test_an_ideal_range_rejects_numbers_out_of_order(values):
    l0, l1, u1, u0 = sorted(values, reverse=True)
    with pytest.raises(ValidationError):
        IdealRange(shape="ideal-range", l0=l0, l1=l1, u1=u1, u0=u0)


# --- datasets ---


def test_a_complete_public_dataset_passes():
    assert Dataset.model_validate(dataset()).public_build is True


def test_a_public_dataset_needs_an_open_licence():
    assert "not on D07's list" in problem(Dataset, dataset(licence="proprietary"))


def test_licences_joined_by_and_must_all_be_open():
    assert Dataset.model_validate(dataset(licence="CDLA-Permissive-2.0 AND Apache-2.0"))
    assert "CC-BY-NC-4.0 is not" in problem(Dataset, dataset(licence="CC-BY-4.0 AND CC-BY-NC-4.0"))


def test_a_public_dataset_needs_its_check_date_and_attribution():
    assert "licence_checked" in problem(Dataset, dataset(licence_checked=None))
    assert "attribution" in problem(Dataset, dataset(attribution=None))


def test_a_private_dataset_needs_a_licence_note():
    data = dataset(public_build=False, licence="unknown", licence_checked=None, attribution=None)
    assert "licence_note" in problem(Dataset, data)
    assert Dataset.model_validate({**data, "licence_note": "Not confirmed."})


def test_a_credibility_rating_needs_its_reason():
    assert "credibility_reason" in problem(Dataset, dataset(credibility="high"))


def test_a_dataset_date_may_be_a_year_or_text():
    assert Dataset.model_validate(dataset(date="updated daily"))
    assert "date" in problem(Dataset, dataset(date=True))


def test_a_dataset_url_must_be_web_address():
    assert "url" in problem(Dataset, dataset(url="data.london.gov.uk"))
