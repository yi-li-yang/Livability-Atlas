import h3
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import epc
from atlas.families import Context, discover
from atlas.families import urban_form as family
from atlas.paths import CATALOGUE_DIR

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
CENTRE = h3.latlng_to_cell(51.5133, -0.0886, 9)


def context(tmp_path, cells) -> Context:
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    x, y = TO_BNG.transform(*h3.cell_to_latlng(CENTRE)[::-1])
    postcodes = pd.DataFrame({"Easting": [x], "Northing": [y]}, index=["EC3V3ND"])
    ctx = Context("london", region, cells, tmp_path, postcodes, network=None)  # type: ignore[arg-type]
    ctx.__dict__["residents"] = pd.Series(100.0, index=cells)  # stands in for the cached property
    return ctx


def homes(built: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "postcode": ["EC3V3ND"] * len(built),
            "cell": [CENTRE] * len(built),
            "efficiency": [70.0] * len(built),
            "built": built,
            "tenure": ["owner"] * len(built),
            "property_type": ["Flat"] * len(built),
        }
    )


def test_density_is_the_residents_a_square_kilometre_around_a_cell(tmp_path):
    cells = list(h3.grid_disk(CENTRE, 2))
    out = family.columns_with(context(tmp_path, cells), homes([1900.0] * 40))
    area = h3.cell_area(CENTRE, "km^2")
    assert out["density"][cells.index(CENTRE)] == pytest.approx(100.0 / area, rel=0.01)


def test_building_age_is_the_median_year_the_homes_around_a_cell_were_built(tmp_path, monkeypatch):
    monkeypatch.setattr(
        epc, "stock", lambda *a: homes([1880.0] * 15 + [1930.0] * 15 + [2010.0] * 15)
    )
    out = family.columns(context(tmp_path, [CENTRE]))
    assert out["building-age"] == [1930.0]


def test_a_cell_with_fewer_than_30_dated_homes_has_no_building_age(tmp_path):
    out = family.columns_with(context(tmp_path, [CENTRE]), homes([1930.0] * 29))
    assert out["building-age"] == [None]


def test_homes_with_no_date_are_not_counted(tmp_path):
    dated = [1930.0] * 20 + [float("nan")] * 50
    assert family.columns_with(context(tmp_path, [CENTRE]), homes(dated))["building-age"] == [None]


def test_the_family_is_found_and_its_indicators_are_in_the_catalogue():
    assert "urban_form" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert {"density", "building-age"} <= ids


def test_a_commercial_build_leaves_out_the_age_that_comes_from_the_certificates():
    assert family.FAMILY.built_from == {"building-age": ("epc-domestic",)}


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
