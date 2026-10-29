import pytest

from atlas.qa import regional as regional_module
from atlas.qa.regional import Regional, regional


def test_london_has_its_places_facts_and_relations():
    london = regional("london")
    assert "Soho" in london.places
    assert len(london.facts) > 20 and len(london.relations) > 10


def test_a_region_without_a_facts_file_has_none():
    assert regional("atlantis") == Regional({}, [], [])


def test_a_hyphen_in_a_region_id_is_an_underscore_in_its_module(monkeypatch):
    asked = []

    def import_module(name):
        asked.append(name)
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr(regional_module, "import_module", import_module)
    assert regional("new-york") == Regional({}, [], [])
    assert asked == ["atlas.datasets.cities.new_york.facts"]


@pytest.mark.parametrize(
    "missing",
    [
        "atlas.datasets.cities.atlantis",  # the region's folder
        "atlas.datasets.cities.atlantis.facts",  # its facts file
    ],
)
def test_a_missing_folder_or_file_of_the_region_means_no_facts(monkeypatch, missing):
    def import_module(name):
        raise ModuleNotFoundError(name=missing)

    monkeypatch.setattr(regional_module, "import_module", import_module)
    assert regional("atlantis") == Regional({}, [], [])


@pytest.mark.parametrize(
    "missing",
    [
        "nonesuch",  # an import inside the facts file
        "atlas.datasets.cities.atl",  # starts like the region's folder, but is not a package of it
        "atlas.datasets.cities.atlantis.fact",
        "atlas.datasets.cities.atlantis.facts.more",
        None,
    ],
)
def test_any_other_missing_module_is_an_error(monkeypatch, missing):
    def import_module(name):
        raise ModuleNotFoundError("broken", name=missing)

    monkeypatch.setattr(regional_module, "import_module", import_module)
    with pytest.raises(ModuleNotFoundError):
        regional("atlantis")
