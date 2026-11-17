import h3
import numpy as np
import pandas as pd

from atlas.catalogue.load import load_catalogue
from atlas.datasets.world import openstreetmap
from atlas.families import Context, discover, run
from atlas.families import cuisines as family
from atlas.indicators import places as place_pool
from atlas.paths import CATALOGUE_DIR

CELLS = [h3.latlng_to_cell(51.5136, -0.1337, 9), h3.latlng_to_cell(51.52, -0.12, 9)]


def restaurants(counts: dict[str | None, int]) -> pd.DataFrame:
    labels = [c for c, n in counts.items() for _ in range(n)]
    return pd.DataFrame(
        {
            "Easting": np.linspace(529000, 530000, len(labels)),
            "Northing": np.linspace(181000, 182000, len(labels)),
            "name": ["x"] * len(labels),
            "cuisine": labels,
        }
    )


class Network:
    def __init__(self):
        self.asked = []

    def minutes_to_nearest(self, places, origins):
        self.asked.append(len(places))
        return np.full(len(origins), 6.0)


def context(tmp_path, network) -> Context:
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, CELLS, tmp_path, pd.DataFrame(), network)  # type: ignore[arg-type]
    ctx.__dict__["overture"] = pd.DataFrame()  # stands in for the cached property
    return ctx


def patch(monkeypatch, table):
    monkeypatch.setattr(openstreetmap, "places", lambda data_dir, region_id: pd.DataFrame())
    monkeypatch.setattr(place_pool, "pool", lambda overture, osm: {"restaurant": table})


def test_a_cuisine_with_enough_restaurants_is_offered_with_the_walk_to_its_nearest(
    tmp_path, monkeypatch
):
    patch(monkeypatch, restaurants({"indian": 120, "greek": 105, "rare": 20, None: 40}))
    network = Network()
    options = family.choices(context(tmp_path, network))["your-cuisines"]
    assert [o.id for o in options] == ["greek", "indian"]
    assert options[0].values == [6.0, 6.0] and options[0].group == "Cuisine"
    assert network.asked == [105, 120]  # each cuisine's own restaurants


def test_a_walk_is_kept_to_a_tenth_of_a_minute(tmp_path, monkeypatch):
    patch(monkeypatch, restaurants({"indian": 120}))

    class Long(Network):
        def minutes_to_nearest(self, places, origins):
            return np.array([6.04321, np.nan])

    option = family.choices(context(tmp_path, Long()))["your-cuisines"][0]
    assert option.values == [6.0, None]


def test_a_label_that_is_a_kind_of_place_and_not_a_cuisine_is_left_out(tmp_path, monkeypatch):
    patch(monkeypatch, restaurants({"bar_and_grill": 200, "thai": 150}))
    options = family.choices(context(tmp_path, Network()))["your-cuisines"]
    assert [o.id for o in options] == ["thai"]


def test_a_cuisine_is_named_in_plain_words():
    assert family.name_of("fish_and_chips") == "Fish and Chips"
    assert family.name_of("indian") == "Indian"
    assert family.name_of("sri_lankan") == "Sri Lankan"


def test_a_city_with_no_restaurants_offers_no_cuisine(tmp_path, monkeypatch):
    monkeypatch.setattr(openstreetmap, "places", lambda data_dir, region_id: pd.DataFrame())
    monkeypatch.setattr(place_pool, "pool", lambda overture, osm: {})
    assert family.choices(context(tmp_path, Network())) == {"your-cuisines": []}


def test_the_family_builds_no_columns_of_its_own_and_runs_with_the_others(tmp_path, monkeypatch):
    patch(monkeypatch, restaurants({"indian": 150}))
    columns, choices = run([family.FAMILY], context(tmp_path, Network()))
    assert columns == {} and list(choices) == ["your-cuisines"]


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "cuisines" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "your-cuisines" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
