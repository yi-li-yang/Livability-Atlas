import h3
import pandas as pd
import pytest

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import ons_local_authorities, ons_wellbeing
from atlas.families import Context, discover
from atlas.families import life_satisfaction as family
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
HEADER = (
    "v4_3,Data marking,Lower limit,Upper limit,yyyy-yy,Time,administrative-geography,Geography,"
    "measure-of-wellbeing,MeasureOfWellbeing,wellbeing-estimate,Estimate"
)


def write(tmp_path, rows: list[str]):
    path = tmp_path / "w.csv"
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def row(value, period, code, measure="Life satisfaction", estimate="Average (mean)", mark=""):
    return f"{value},{mark},1,9,{period},{period},{code},Area,x,{measure},x,{estimate}"


def test_a_borough_takes_the_mean_of_its_averages_over_the_latest_three_years(tmp_path):
    path = write(
        tmp_path,
        [
            row(7.0, "2022-23", "E09000001"),
            row(7.2, "2021-22", "E09000001"),
            row(7.4, "2020-21", "E09000001"),
            row(9.0, "2019-20", "E09000001"),  # older than the latest three years
            row(50.0, "2022-23", "E09000001", estimate="Good"),  # a share, not the mean
            row(6.0, "2022-23", "E09000001", measure="Happiness"),
        ],
    )
    values = ons_wellbeing.read_life_satisfaction(path)
    assert values["E09000001"] == pytest.approx(7.2)


def test_an_estimate_the_ons_marks_as_unusable_is_left_out(tmp_path):
    path = write(
        tmp_path,
        [
            row(7.0, "2022-23", "E09000002"),
            row("", "2021-22", "E09000002", mark="[x]"),
        ],
    )
    assert ons_wellbeing.read_life_satisfaction(path)["E09000002"] == pytest.approx(7.0)


def test_the_file_is_fetched_once(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(ons_wellbeing, "download", lambda url, target: asked.append(url))
    path = ons_wellbeing.fetch(tmp_path)
    assert path == tmp_path / "raw" / "ons-wellbeing" / "wellbeing-local-authority.csv"
    assert asked[0].endswith("versions/4.csv")


def test_a_cell_takes_the_value_of_its_borough(tmp_path, monkeypatch):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    monkeypatch.setattr(ons_local_authorities, "fetch", lambda data_dir, region_id: tmp_path / "la")
    monkeypatch.setattr(
        ons_local_authorities, "borough_of", lambda path, cells: {CELL: "E09000033"}
    )
    monkeypatch.setattr(ons_wellbeing, "fetch", lambda data_dir: tmp_path / "w.csv")
    monkeypatch.setattr(ons_wellbeing, "read_life_satisfaction", lambda path: {"E09000033": 7.4})
    assert family.columns(ctx) == {"life-satisfaction": [7.4]}


def test_a_borough_without_a_value_gives_none(tmp_path, monkeypatch):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    monkeypatch.setattr(ons_local_authorities, "fetch", lambda data_dir, region_id: tmp_path / "la")
    monkeypatch.setattr(
        ons_local_authorities, "borough_of", lambda path, cells: {CELL: "E09000001"}
    )
    monkeypatch.setattr(ons_wellbeing, "fetch", lambda data_dir: tmp_path / "w.csv")
    monkeypatch.setattr(ons_wellbeing, "read_life_satisfaction", lambda path: {})
    assert family.columns(ctx) == {"life-satisfaction": [None]}


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "life_satisfaction" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "life-satisfaction" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
