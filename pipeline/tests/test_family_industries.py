import geopandas as gpd
import h3
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import bres, ons_lsoa
from atlas.families import Context, discover
from atlas.families import industries as family
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform


def test_each_industry_is_fetched_in_pages_to_its_own_files(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(bres, "download", lambda url, target: asked.append((url, target.name)))
    files = bres.fetch_industry(tmp_path, "J")
    assert [f.name for f in files] == ["bres-J-lsoa-2024-1.csv", "bres-J-lsoa-2024-2.csv"]
    assert all("industry=150994954" in url for url, _ in asked)  # section J is 150994945 + 9
    assert [u.rsplit("recordoffset=", 1)[1] for u, _ in asked] == ["0", "25000"]


def test_the_total_is_still_the_all_industries_figure():
    assert "industry=37748736" in bres.BASE


def test_the_sections_run_from_a_to_u_in_order_of_their_codes():
    assert bres.section_code("A") == 150994945
    assert bres.section_code("U") == 150994965


def test_a_user_can_pick_among_the_industries_with_many_jobs_in_plain_words():
    assert family.INDUSTRIES["J"] == "Information and communication"
    assert family.INDUSTRIES["Q"] == "Health and social work"
    assert "A" not in family.INDUSTRIES and "T" not in family.INDUSTRIES


def test_a_cell_gets_the_jobs_a_square_kilometre_of_each_industry_around_it(tmp_path, monkeypatch):
    outline = transform(TO_BNG, Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(CELL)]))
    lsoas = gpd.GeoDataFrame({"LSOA11CD": ["l1"]}, geometry=[outline], crs="EPSG:27700")
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    monkeypatch.setattr(ons_lsoa, "fetch", lambda data_dir, bounds: tmp_path / "l")
    monkeypatch.setattr(ons_lsoa, "read_boundaries", lambda path: lsoas)
    monkeypatch.setattr(bres, "fetch_industry", lambda data_dir, letter: [tmp_path / letter])
    monkeypatch.setattr(
        bres,
        "read_jobs",
        lambda paths: pd.Series({"l1": 2000.0 if paths[0].name == "J" else 500.0}, name="jobs"),
    )
    options = family.choices(ctx)["your-industry"]
    by_id = {o.id: o.values for o in options}
    area = h3.cell_area(CELL, "km^2")
    assert by_id["j"][0] == pytest.approx(round(2000.0 / area), abs=1)
    assert by_id["q"][0] == pytest.approx(round(500.0 / area), abs=1)
    assert [o.group for o in options] == ["Industry"] * len(options)
    assert options[0].name == family.INDUSTRIES[options[0].id.upper()]


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "industries" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "your-industry" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
