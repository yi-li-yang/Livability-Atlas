import geopandas as gpd
import h3
import pandas as pd
import pytest
from openpyxl import Workbook
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import ons_hsle
from atlas.families import Context, discover
from atlas.families import wellbeing as family
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
HEADER = ["Period", "Country", "Area type", "Area code", "Area name", "Sex", "Sex code", "HLE"]


def workbook(tmp_path, rows: list[list[object]]):
    book = Workbook()
    book.active.title = "Cover_sheet"  # type: ignore[union-attr]
    sheet = book.create_sheet("2")
    for text in (
        "Sheet 2: Healthy life expectancy",
        "",
        "This worksheet contains one table.",
        "",
        "",
        "",
    ):
        sheet.append([text])
    sheet.append(HEADER)
    for row in rows:
        sheet.append(row)
    path = tmp_path / "hsle.xlsx"
    book.save(path)
    return path


def row(code: str, sex: str, value: float, kind: str = "MSOA") -> list[object]:
    return ["2019 to 2023", "England", kind, code, "Name", sex, 1, value]


def test_an_msoa_takes_the_mean_of_the_healthy_life_expectancy_of_men_and_women(tmp_path):
    path = workbook(
        tmp_path,
        [
            row("E02000001", "Male", 70.0),
            row("E02000001", "Female", 74.0),
            row("E02000002", "Male", 60.0),
            row("E92000001", "Male", 63.0, kind="Country"),  # not an MSOA
        ],
    )
    found = ons_hsle.read_msoa(path)
    assert found["E02000001"] == pytest.approx(72.0)
    assert found["E02000002"] == pytest.approx(60.0)  # one sex only: that one
    assert "E92000001" not in found.index


def test_the_workbook_is_fetched_once(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(ons_hsle, "download", lambda url, target: asked.append(url))
    path = ons_hsle.fetch(tmp_path)
    assert path == tmp_path / "raw" / "ons-hsle" / "hslemsoa.xlsx"
    assert asked[0].endswith("2019to2023/hslemsoa.xlsx")


def test_a_cell_takes_the_value_of_the_neighbourhood_that_holds_its_centre(tmp_path, monkeypatch):
    outline = transform(TO_BNG, Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(CELL)]))
    msoas = gpd.GeoDataFrame({"MSOA21CD": ["E02000001"]}, geometry=[outline], crs="EPSG:27700")
    monkeypatch.setattr(ons_hsle, "fetch", lambda data_dir: tmp_path / "x.xlsx")
    monkeypatch.setattr(ons_hsle, "read_msoa", lambda path: pd.Series({"E02000001": 72.5}))
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    ctx.__dict__["msoas"] = msoas  # stands in for the cached property
    assert family.columns(ctx) == {"life-expectancy": [72.5]}


def test_a_cell_in_no_neighbourhood_or_one_without_an_estimate_has_no_value(tmp_path, monkeypatch):
    outline = transform(TO_BNG, Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(CELL)]))
    msoas = gpd.GeoDataFrame({"MSOA21CD": ["E02000009"]}, geometry=[outline], crs="EPSG:27700")
    monkeypatch.setattr(ons_hsle, "fetch", lambda data_dir: tmp_path / "x.xlsx")
    monkeypatch.setattr(ons_hsle, "read_msoa", lambda path: pd.Series({"E02000001": 72.5}))
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    ctx.__dict__["msoas"] = msoas
    assert family.columns(ctx) == {"life-expectancy": [None]}


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "wellbeing" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "life-expectancy" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
