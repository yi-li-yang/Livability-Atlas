import h3
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import nhs_ae, nhs_ae_waits
from atlas.families import Context, discover
from atlas.families import ae_waits as family
from atlas.paths import CATALOGUE_DIR

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)

HEADER = (
    "Period,Org Code,Parent Org,Org name,A&E attendances Type 1,A&E attendances Type 2,"
    "Attendances over 4hrs Type 1,Attendances over 4hrs Type 2"
)


def write(tmp_path, name: str, rows: list[str]):
    path = tmp_path / name
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_a_trusts_performance_is_the_share_of_type_1_attendances_seen_within_4_hours(tmp_path):
    month1 = write(tmp_path, "a.csv", ["M,R1A,NHS ENGLAND,A TRUST,1000,500,200,0"])
    month2 = write(tmp_path, "b.csv", ["M,R1A,NHS ENGLAND,A TRUST,3000,500,1000,0"])
    performance = nhs_ae_waits.read_performance([month1, month2])
    assert performance["R1A"] == pytest.approx(100 * (1 - 1200 / 4000))  # 70%, over both months


def test_a_provider_with_no_type_1_attendances_has_no_performance(tmp_path):
    path = write(
        tmp_path,
        "a.csv",
        ["M,R1A,E,A TRUST,0,0,0,0", "M,R1B,E,B TRUST,100,0,10,0"],
    )
    performance = nhs_ae_waits.read_performance([path])
    assert list(performance.index) == ["R1B"]


def test_the_months_are_fetched_once_each(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(nhs_ae_waits, "download", lambda url, target: asked.append(target.name))
    paths = nhs_ae_waits.fetch(tmp_path)
    assert len(paths) == len(nhs_ae_waits.MONTHS) == len(asked)
    assert paths[0].parent == tmp_path / "raw" / "nhs-ae-waits"


def context(tmp_path, cells):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    x, y = TO_BNG.transform(*h3.cell_to_latlng(CELL)[::-1])
    postcodes = pd.DataFrame(
        {"Easting": [x, x + 3000, x + 6000], "Northing": [y, y, y]},
        index=["W1F9AA", "W1F9AB", "W1F9AC"],
    )
    return Context("london", region, cells, tmp_path, postcodes, None)  # type: ignore[arg-type]


def test_a_cell_takes_the_performance_of_the_trust_of_its_nearest_department(tmp_path, monkeypatch):
    sites = pd.DataFrame(
        {
            "code": ["R1A01", "R1B02", "R1C03"],
            "name": ["Near", "Middle", "Far"],
            "Postcode": ["W1F 9AA", "W1F 9AB", "W1F 9AC"],
        }
    )
    monkeypatch.setattr(nhs_ae, "fetch", lambda data_dir, region_id, seeds: tmp_path / "s.csv")
    monkeypatch.setattr(nhs_ae, "read_sites", lambda path: sites)
    monkeypatch.setattr(nhs_ae_waits, "fetch", lambda data_dir: [])
    monkeypatch.setattr(
        nhs_ae_waits,
        "read_performance",
        lambda paths: pd.Series({"R1A": 60.0, "R1B": 75.0, "R1C": 90.0}),
    )
    out = family.columns(context(tmp_path, [CELL]))
    assert out == {"ae-waiting": [60.0]}


def test_a_department_whose_trust_has_no_figures_is_skipped_for_the_next_nearest(
    tmp_path, monkeypatch
):
    sites = pd.DataFrame(
        {"code": ["XXX01", "R1B02"], "name": ["Near", "Next"], "Postcode": ["W1F 9AA", "W1F 9AB"]}
    )
    monkeypatch.setattr(nhs_ae, "fetch", lambda data_dir, region_id, seeds: tmp_path / "s.csv")
    monkeypatch.setattr(nhs_ae, "read_sites", lambda path: sites)
    monkeypatch.setattr(nhs_ae_waits, "fetch", lambda data_dir: [])
    monkeypatch.setattr(nhs_ae_waits, "read_performance", lambda paths: pd.Series({"R1B": 75.0}))
    assert family.columns(context(tmp_path, [CELL])) == {"ae-waiting": [75.0]}


def test_a_department_whose_code_does_not_start_with_its_trusts_is_mapped_by_hand(
    tmp_path, monkeypatch
):
    sites = pd.DataFrame({"code": ["AXA02"], "name": ["Royal London"], "Postcode": ["W1F 9AA"]})
    monkeypatch.setattr(nhs_ae, "fetch", lambda data_dir, region_id, seeds: tmp_path / "s.csv")
    monkeypatch.setattr(nhs_ae, "read_sites", lambda path: sites)
    monkeypatch.setattr(nhs_ae_waits, "fetch", lambda data_dir: [])
    monkeypatch.setattr(nhs_ae_waits, "read_performance", lambda paths: pd.Series({"R1H": 66.0}))
    assert family.columns(context(tmp_path, [CELL])) == {"ae-waiting": [66.0]}


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "ae_waits" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "ae-waiting" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
