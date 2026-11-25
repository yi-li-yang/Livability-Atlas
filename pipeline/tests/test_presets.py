import json
import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from atlas.catalogue.checks import check_preset
from atlas.catalogue.load import load_catalogue, validate_catalogue
from atlas.catalogue.models import Preset
from atlas.catalogue.schema import write_schemas
from atlas.paths import CATALOGUE_DIR

PRESET = {
    "id": "renter",
    "name": "Renter who commutes",
    "description": "Rent and the trip to work matter most.",
    "weights": {"housing-and-cost": 5, "renting-cost": 5, "safety": 2, "culture-and-leisure": 3},
    "flipped": ["nightlife"],
    "limits": [{"indicator": "renting-cost", "max": 2200}],
}


def factors():
    return load_catalogue(CATALOGUE_DIR).factors


class TestTheModel:
    def test_a_preset_with_weights_directions_and_limits_is_accepted(self):
        preset = Preset.model_validate(PRESET)
        assert preset.weights["renting-cost"] == 5 and preset.limits[0].max == 2200

    def test_a_limit_can_be_a_least_or_a_list_of_categories(self):
        data = {
            **PRESET,
            "limits": [{"indicator": "ptal", "min": 3}, {"indicator": "x", "in": ["a"]}],
        }
        limits = Preset.model_validate(data).limits
        assert limits[0].min == 3 and limits[1].in_ == ["a"]

    @pytest.mark.parametrize(
        "change",
        [
            {"weights": {"safety": 6}},  # above the scale
            {"weights": {"safety": 2.5}},  # not a whole number
            {"weights": {"Safety": 2}},  # not an id
            {"id": "Renter"},
            {"colour": "red"},  # an unknown field
            {"limits": [{"indicator": "renting-cost"}]},  # a limit with no bound
            {"limits": [{"indicator": "renting-cost", "max": 1, "min": 0}]},  # two bounds
        ],
    )
    def test_a_preset_that_breaks_a_rule_is_rejected(self, change):
        with pytest.raises(ValidationError):
            Preset.model_validate({**PRESET, **change})


class TestTheChecks:
    def test_a_good_preset_passes(self):
        assert check_preset(Preset.model_validate(PRESET), factors()) == []

    def test_a_weight_for_an_unknown_factor_is_a_problem(self):
        preset = Preset.model_validate({**PRESET, "weights": {"no-such-factor": 3}})
        assert any("no-such-factor" in p for p in check_preset(preset, factors()))

    def test_a_flipped_indicator_must_let_the_user_choose_its_direction(self):
        preset = Preset.model_validate({**PRESET, "flipped": ["renting-cost"]})  # a fixed one
        problems = check_preset(preset, factors())
        assert any("renting-cost" in p and "direction" in p for p in problems)

    def test_a_flipped_indicator_must_count(self):
        # Culture and leisure starts at "Not counted" (D14), so a flip of nightlife inside it would
        # count for nothing unless the preset counts it.
        weights = {k: v for k, v in PRESET["weights"].items() if k != "culture-and-leisure"}
        preset = Preset.model_validate({**PRESET, "weights": weights})
        problems = check_preset(preset, factors())
        assert any("nightlife" in p and "counts for nothing" in p for p in problems)

    def test_a_limit_on_an_unknown_indicator_is_a_problem(self):
        preset = Preset.model_validate({**PRESET, "limits": [{"indicator": "nope", "max": 1}]})
        assert any("nope" in p for p in check_preset(preset, factors()))

    def test_a_limit_on_a_factor_that_is_not_an_indicator_is_a_problem(self):
        preset = Preset.model_validate({**PRESET, "limits": [{"indicator": "safety", "max": 1}]})
        assert any(
            "safety" in p and "measured indicator" in p for p in check_preset(preset, factors())
        )

    def test_a_limit_on_an_indicator_not_built_is_a_problem(self):
        preset = Preset.model_validate(
            {**PRESET, "limits": [{"indicator": "cultural-activity", "min": 1}]}
        )
        assert any("built" in p for p in check_preset(preset, factors()))


class TestTheFiles:
    def test_the_real_presets_pass_and_are_loaded_by_id(self):
        assert validate_catalogue(CATALOGUE_DIR) == []
        presets = load_catalogue(CATALOGUE_DIR).presets
        assert {"renter-near-the-centre", "family-with-children", "retiree", "student"} <= set(
            presets
        )

    def test_the_file_name_is_the_id(self, tmp_path):
        directory = copy_catalogue(tmp_path)
        (directory / "presets" / "other.yaml").write_text(
            yaml.safe_dump({**PRESET, "id": "renter"}), encoding="utf-8"
        )
        assert any("other" in p and "id" in p for p in validate_catalogue(directory))

    def test_a_bad_preset_file_is_reported_with_its_name(self, tmp_path):
        directory = copy_catalogue(tmp_path)
        (directory / "presets" / "renter.yaml").write_text(
            yaml.safe_dump({**PRESET, "weights": {"safety": 9}}), encoding="utf-8"
        )
        assert any("renter" in p for p in validate_catalogue(directory))

    def test_every_preset_changes_something_and_has_a_plain_description(self):
        for preset in load_catalogue(CATALOGUE_DIR).presets.values():
            assert preset.weights or preset.limits or preset.flipped, preset.id
            assert preset.description.endswith("."), preset.id


def copy_catalogue(tmp_path: Path) -> Path:
    target = tmp_path / "catalogue"
    shutil.copytree(CATALOGUE_DIR, target)
    (target / "presets").mkdir(exist_ok=True)
    return target


def test_the_schema_of_a_preset_is_exported(tmp_path):
    names = [p.name for p in write_schemas(tmp_path)]
    assert "preset.schema.json" in names
    schema = json.loads((tmp_path / "preset.schema.json").read_text(encoding="utf-8"))
    assert "weights" in schema["properties"]
