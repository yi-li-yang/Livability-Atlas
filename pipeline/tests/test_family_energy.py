import h3
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import epc
from atlas.families import Context, discover
from atlas.families import energy as energy_family
from atlas.paths import CATALOGUE_DIR

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
CENTRE = h3.latlng_to_cell(51.5133, -0.0886, 9)


def context(tmp_path, cells) -> Context:
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    x, y = TO_BNG.transform(*h3.cell_to_latlng(CENTRE)[::-1])
    postcodes = pd.DataFrame(
        {"Easting": [x, x + 4000], "Northing": [y, y]}, index=["EC3V3ND", "EC3V9ZZ"]
    )
    return Context("london", region, cells, tmp_path, postcodes, network=None)  # type: ignore[arg-type]


def homes(points: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "postcode": ["EC3V3ND"] * len(points),
            "efficiency": points,
            "built": [1900.0] * len(points),
            "tenure": ["owner"] * len(points),
            "property_type": ["Flat"] * len(points),
        }
    )


def test_a_cell_takes_the_median_points_of_the_homes_at_its_postcodes(tmp_path, monkeypatch):
    cells = [CENTRE, h3.grid_ring(CENTRE, 1)[0], h3.grid_ring(CENTRE, 2)[0]]
    asked = {}

    def fake_stock(data_dir, region_id, postcodes):
        asked["postcodes"] = postcodes
        return homes([40.0] * 15 + [70.0] * 15 + [90.0] * 15)

    monkeypatch.setattr(epc, "stock", fake_stock)
    out = energy_family.columns(context(tmp_path, cells))
    assert out["energy-efficiency"][0] == 70.0  # the median of 45 homes
    assert out["energy-efficiency"][1] == 70.0  # a neighbour pools the same homes
    assert out["energy-efficiency"][2] is None  # two steps away is out of reach of them
    assert asked["postcodes"] == {"EC3V3ND"}  # the postcode 4 km away is outside the region


def test_a_cell_with_fewer_than_30_homes_around_it_has_no_value(tmp_path, monkeypatch):
    monkeypatch.setattr(epc, "stock", lambda *a: homes([70.0] * 29))
    out = energy_family.columns(context(tmp_path, [CENTRE]))
    assert out["energy-efficiency"][0] is None


def test_the_family_names_the_datasets_a_commercial_build_cannot_use():
    assert energy_family.FAMILY.built_from == {"energy-efficiency": ("epc-domestic",)}


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "energy" in {f.name for f in discover()}
    catalogue = load_catalogue(CATALOGUE_DIR)
    ids = {n.id for n in _leaves(catalogue.factors.factors)}
    assert "energy-efficiency" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)


@pytest.mark.parametrize("points", [[]])
def test_no_homes_gives_no_values(tmp_path, monkeypatch, points):
    monkeypatch.setattr(epc, "stock", lambda *a: homes(points))
    out = energy_family.columns(context(tmp_path, [CENTRE]))
    assert out["energy-efficiency"][0] is None
