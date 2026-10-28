import json
import zipfile
from pathlib import Path

import h3
import numpy as np
import pyarrow.parquet as pq
from openpyxl import Workbook
from pyproj import Transformer
from shapely.geometry import box
from typer.testing import CliRunner

from atlas import build as build_module
from atlas.build import build_region
from atlas.cli import app
from atlas.datasets.cities.london import ptal
from atlas.datasets.countries.gb import ons_regions
from atlas.datasets.countries.gb.ea_flood_risk import LOW, MEDIUM, VERY_LOW, Mosaic
from atlas.indicators import crime

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
AREA = box(-0.150, 51.505, -0.125, 51.520)  # part of the West End


def synthetic_boundary(tmp_path: Path) -> Path:
    path = tmp_path / "London.geojson"
    feature = {
        "type": "Feature",
        "properties": {ons_regions.NAME_FIELD: "London"},
        "geometry": AREA.__geo_interface__,
    }
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}), encoding="utf-8"
    )
    return path


def synthetic_grid(tmp_path: Path) -> Path:
    """A 100 m grid over AREA: band 3 in the west, band 5 in the east."""
    x0, y0 = TO_BNG.transform(AREA.bounds[0], AREA.bounds[1])
    x1, y1 = TO_BNG.transform(AREA.bounds[2], AREA.bounds[3])
    workbook = Workbook()
    sheet = workbook.create_sheet("Query1")
    sheet.append(["ID", "X", "Y", "AI2015", "PTAL2015"])
    number = 0
    x = x0 - 200
    while x < x1 + 200:
        y = y0 - 200
        while y < y1 + 200:
            number += 1
            sheet.append([number, round(x), round(y), 10, 3 if x < (x0 + x1) / 2 else 5])
            y += 100
        x += 100
    path = tmp_path / "grid.xlsx"
    workbook.save(path)
    return path


MIDDLE = -0.1375  # the longitude that splits AREA into a west half and an east half


def synthetic_output_areas(tmp_path: Path) -> Path:
    """Two output areas that cover AREA, with a margin: the west one and the east one."""
    x0, y0 = TO_BNG.transform(AREA.bounds[0] - 0.01, AREA.bounds[1] - 0.01)
    x1, y1 = TO_BNG.transform(AREA.bounds[2] + 0.01, AREA.bounds[3] + 0.01)
    xm, _ = TO_BNG.transform(MIDDLE, 51.51)

    def feature(code: str, left: float, right: float) -> dict:
        ring = [[left, y0], [right, y0], [right, y1], [left, y1], [left, y0]]
        return {
            "type": "Feature",
            "properties": {"OA21CD": code},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        }

    path = tmp_path / "output-areas.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [feature("W1", x0, xm), feature("E1", xm, x1)],
            }
        ),
        encoding="utf-8",
    )
    return path


def synthetic_residents(tmp_path: Path) -> Path:
    path = tmp_path / "ts001.csv"
    lines = [
        '"date","geography","geography code","Residence type: Total; measures: Value"',
        '"2021","W1","W1",30000',
        '"2021","E1","E1",30000',
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def synthetic_crimes(tmp_path: Path) -> tuple[Path, list[str]]:
    """Burglaries: 600 in the west half and 20 in the east, with equal residents. Nothing else."""
    rows = ["Crime ID,Month,Longitude,Latitude,Crime type"]
    for i in range(600):
        rows.append(f",2026-07,{-0.149 + 0.0000002 * i},{51.506 + 0.00002 * i},Burglary")
    for i in range(20):
        rows.append(f",2026-07,{-0.126 - 0.0000002 * i},{51.506 + 0.0007 * i},Burglary")
    path = tmp_path / "2026-07.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("2026-07/2026-07-metropolitan-street.csv", "\n".join(rows) + "\n")
    return path, ["2026-07"]


def synthetic_flood_risk(which: str, bounds) -> Mosaic:
    """Rivers and sea: medium risk in the west half of AREA and very low in the east. Surface water:
    low everywhere, so no area at risk."""
    x0, y0, x1, y1 = bounds
    xm, _ = TO_BNG.transform(MIDDLE, 51.51)
    rows, cols = int((y1 - y0) / 10) + 1, int((x1 - x0) / 10) + 1
    if which == "surface-water":
        classes = np.full((rows, cols), LOW, dtype=np.uint8)
    else:
        classes = np.full((rows, cols), VERY_LOW, dtype=np.uint8)
        xs = x0 + (np.arange(cols) + 0.5) * 10
        classes[:, xs < xm] = MEDIUM
    return Mosaic(classes=classes, x=x0, y=y1, resolution=10)


def use_synthetic_data(monkeypatch, tmp_path):
    boundary, grid = synthetic_boundary(tmp_path), synthetic_grid(tmp_path)
    areas, people = synthetic_output_areas(tmp_path), synthetic_residents(tmp_path)
    crimes = synthetic_crimes(tmp_path)
    monkeypatch.setattr(build_module.ons_regions, "fetch", lambda name, data_dir: boundary)
    monkeypatch.setattr(build_module.ptal, "fetch", lambda data_dir: grid)
    monkeypatch.setattr(build_module.output_areas, "fetch", lambda data_dir, bounds: areas)
    monkeypatch.setattr(build_module.census_residents, "fetch", lambda data_dir: people)
    monkeypatch.setattr(build_module.police_uk, "fetch", lambda data_dir: crimes)
    monkeypatch.setattr(
        build_module.ea_flood_risk,
        "fetch",
        lambda data_dir, which, bounds: synthetic_flood_risk(which, bounds),
    )


def test_a_region_is_built_into_a_bundle(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    assert bundle.parent.parent == tmp_path / "data" / "published"
    table = pq.read_table(bundle / "cells.parquet")
    cells = table["cell"].to_pylist()
    assert 20 <= len(cells) <= 60 and cells == sorted(cells)
    assert {h3.get_resolution(c) for c in cells} == {9}
    bands = set(table["service_level"].to_pylist())
    assert bands == {"3", "5"}


def test_building_twice_gives_the_same_bundle(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    first = build_region("london", data_dir=tmp_path / "one")
    second = build_region("london", data_dir=tmp_path / "two")
    assert first.name == second.name
    assert (first / "cells.parquet").read_bytes() == (second / "cells.parquet").read_bytes()
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()


def test_a_cell_without_a_grid_point_has_no_value(monkeypatch, tmp_path):
    """Outside TfL's grid there is no PTAL: that is missing, and not band 0."""
    use_synthetic_data(monkeypatch, tmp_path)
    wide = box(-0.30, 51.40, 0.0, 51.60)
    boundary = tmp_path / "London.geojson"
    feature = {
        "type": "Feature",
        "properties": {ons_regions.NAME_FIELD: "London"},
        "geometry": wide.__geo_interface__,
    }
    boundary.write_text(
        json.dumps({"type": "FeatureCollection", "features": [feature]}), encoding="utf-8"
    )
    bundle = build_region("london", data_dir=tmp_path / "data")
    values = pq.read_table(bundle / "cells.parquet")["service_level"].to_pylist()
    assert None in values and "3" in values and "0" not in values


def test_the_command_builds_a_region_and_says_where(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    result = CliRunner().invoke(app, ["build", "london", "--data-dir", str(tmp_path / "data")])
    assert result.exit_code == 0, result.output
    assert "cells" in result.output and "published" in result.output


def test_a_region_the_catalogue_does_not_have_is_an_error(tmp_path):
    result = CliRunner().invoke(app, ["build", "atlantis", "--data-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "atlantis" in result.output


def test_the_boundary_query_asks_for_one_region_in_longitude_and_latitude():
    url = ons_regions.url("London")
    assert "outSR=4326" in url and "f=geojson" in url
    assert "RGN25NM%3D%27London%27" in url
    assert "%27%27" in ons_regions.url("St. John's")  # a quote in a name is doubled


def test_the_ptal_release_is_unzipped_after_it_is_fetched(monkeypatch, tmp_path):
    source = tmp_path / "release.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("2015  PTALs Grid Values 280515.xlsx", b"workbook")
        archive.writestr("2015  PTALs Contours 280515.MAP", b"map")

    def fake_download(url, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        return "digest"

    monkeypatch.setattr(ptal, "download", fake_download)
    path = ptal.fetch(tmp_path)
    assert path.name == "2015  PTALs Grid Values 280515.xlsx" and path.read_bytes() == b"workbook"


def test_the_bundle_holds_each_crime_rate_per_1000_residents(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    for indicator in crime.CATEGORIES:
        assert table[indicator.replace("-", "_")].notna().all()
    # Burglary was 20 times as common in the west, with the same residents: its rate is higher
    # there, and a cell on the west edge of the area is above one on the east edge.
    cells = table.assign(
        lng=[h3.cell_to_latlng(c)[1] for c in table["cell"]],
    )
    west, east = cells[cells["lng"] < MIDDLE], cells[cells["lng"] >= MIDDLE]
    assert west["burglary"].median() > 2 * east["burglary"].median()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {i["id"] for i in manifest["indicators"]}
    assert set(crime.CATEGORIES) <= ids and "service-level" in ids
    assert any(d["id"] == "police-uk" for d in manifest["datasets"])


def test_the_bundle_holds_the_share_of_each_cell_at_risk_of_flooding(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = [h3.cell_to_latlng(c)[1] for c in table["cell"]]
    west = table[[x < MIDDLE - 0.002 for x in lng]]
    east = table[[x > MIDDLE + 0.002 for x in lng]]
    assert (west["river_and_sea_flooding"] > 90).all()
    assert (east["river_and_sea_flooding"] < 10).all()
    assert (table["surface_water_flooding"] == 0).all()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {i["id"] for i in manifest["indicators"]}
    assert {"river-and-sea-flooding", "surface-water-flooding"} <= ids
    assert {"ea-flood-risk-rivers-sea", "ea-flood-risk-surface-water"} <= {
        d["id"] for d in manifest["datasets"]
    }
