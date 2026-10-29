import json
import zipfile
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest
import rasterio
from openpyxl import Workbook
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import Point, box
from typer.testing import CliRunner

from atlas import build as build_module
from atlas.build import build_region
from atlas.cli import app
from atlas.datasets.cities.london import ptal
from atlas.datasets.countries.gb import (
    ons_regions,
)
from atlas.datasets.countries.gb.addresses import address_key
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


def synthetic_streets(tmp_path: Path) -> Path:
    """A grid of streets over AREA, about 170 m apart, as an OpenStreetMap file."""
    lats = [51.504 + 0.0015 * i for i in range(12)]
    lngs = [-0.151 + 0.0025 * j for j in range(12)]
    parts = []
    for i, lat in enumerate(lats):
        for j, lng in enumerate(lngs):
            parts.append(f'<node id="{i * 100 + j + 1}" lat="{lat:.6f}" lon="{lng:.6f}"/>')
    for i in range(len(lats)):
        refs = "".join(f'<nd ref="{i * 100 + j + 1}"/>' for j in range(len(lngs)))
        parts.append(f'<way id="{1000 + i}">{refs}<tag k="highway" v="residential"/></way>')
    for j in range(len(lngs)):
        refs = "".join(f'<nd ref="{i * 100 + j + 1}"/>' for i in range(len(lats)))
        parts.append(f'<way id="{2000 + j}">{refs}<tag k="highway" v="footway"/></way>')
    path = tmp_path / "streets.osm"
    head = "<?xml version='1.0' encoding='UTF-8'?><osm version=\"0.6\">"
    path.write_text(head + "".join(parts) + "</osm>", encoding="utf-8")
    return path


def synthetic_stations(tmp_path: Path) -> Path:
    """One station entrance, at the west end of AREA."""
    path = tmp_path / "naptan.csv"
    rows = ["StopType,Status,Longitude,Latitude", "RLY,active,-0.1510,51.5120"]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def synthetic_schools(tmp_path: Path) -> Path:
    """A primary school in the west of AREA and a secondary school in the east, in the register's
    columns and in metres of British National Grid."""
    west = TO_BNG.transform(-0.1495, 51.5120)
    east = TO_BNG.transform(-0.1255, 51.5120)
    rows = [
        "URN,EstablishmentStatus (name),EstablishmentTypeGroup (name),TypeOfEstablishment (name),"
        "PhaseOfEducation (name),Easting,Northing",
        f"1,Open,Academies,Academy converter,Primary,{west[0]:.0f},{west[1]:.0f}",
        f"2,Open,Academies,Academy converter,Secondary,{east[0]:.0f},{east[1]:.0f}",
    ]
    path = tmp_path / "edubasealldata20261028.csv"
    path.write_text("\n".join(rows) + "\n", encoding="cp1252")
    return path


def synthetic_gp_practices(tmp_path: Path) -> tuple[Path, Path]:
    """One GP practice in the east of AREA, in the layout of NHS England's two files."""
    row = [""] * 27
    row[0], row[1], row[9], row[12], row[25] = "A1", "EAST PRACTICE", "W1 1AA", "ACTIVE", "RO76"
    practices, branches = tmp_path / "epraccur.csv", tmp_path / "ebranchs.csv"
    practices.write_text(",".join(f'"{v}"' for v in row) + "\n", encoding="utf-8")
    other = [""] * 27
    other[0], other[1], other[9], other[14] = "Z9", "ELSEWHERE", "N1 1AA", "NONE"
    branches.write_text(",".join(f'"{v}"' for v in other) + "\n", encoding="utf-8")
    return practices, branches


def synthetic_gp_lists() -> pd.DataFrame:
    """The practice of `synthetic_gp_practices` with 6,000 patients and 2 GPs."""
    return pd.DataFrame(
        {"Postcode": ["W1 1AA"], "patients": [6000], "gps": [2.0]},
        index=pd.Index(["A1"], name="code"),
    )


def synthetic_line_stops() -> pd.DataFrame:
    """Two rail lines and three bus routes that stop at one place in the east of AREA."""
    rows = [("rail", line) for line in ("A", "B")] + [("bus", route) for route in ("1", "2", "3")]
    return pd.DataFrame(
        {
            "kind": [r[0] for r in rows],
            "line": [r[1] for r in rows],
            "stop": ["S1"] * len(rows),
            "Latitude": 51.5120,
            "Longitude": -0.1285,
        }
    )


def synthetic_sales() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Thirty sales at 600,000 and the certificates of their homes, all of 60 m², at the postcode
    of the practice in the east of AREA: 10,000 pounds a square metre."""
    houses = [str(n) for n in range(1, 31)]
    sales = pd.DataFrame(
        {
            "price": [600000] * 30,
            "postcode": ["W1 1AA"] * 30,
            "type": ["T"] * 30,
            "paon": houses,
            "saon": [""] * 30,
            "street": ["EAST ROAD"] * 30,
        }
    )
    certificates = pd.DataFrame(
        {
            "key": [address_key("W1 1AA", f"{n} East Road") for n in houses],
            "floor_area": [60.0] * 30,
        }
    )
    return sales, certificates


def synthetic_postcodes(tmp_path: Path) -> Path:
    """The place of that practice's postcode, in the east of AREA."""
    east = TO_BNG.transform(-0.1285, 51.5120)
    path = tmp_path / "codepo_gb.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("Data/CSV/w.csv", f'"W1 1AA",10,{east[0]:.0f},{east[1]:.0f},"E92000001"\n')
    return path


def synthetic_greenspace(tmp_path: Path) -> Path:
    """A park of 3 ha with one way in on foot, at the west end of AREA."""
    west = TO_BNG.transform(-0.1500, 51.5120)
    package = tmp_path / "opgrsp_gb.gpkg"
    x, y = west
    park = box(x - 150, y - 100, x - 150 + 300, y - 100 + 100)  # 3 ha
    gpd.GeoDataFrame(
        {"id": ["park"], "function": ["Public Park Or Garden"]}, geometry=[park], crs="EPSG:27700"
    ).to_file(package, layer="greenspace_site", driver="GPKG")
    gpd.GeoDataFrame(
        {"id": ["gate"], "access_type": ["Pedestrian"], "ref_to_greenspace_site": ["park"]},
        geometry=[Point(x, y)],
        crs="EPSG:27700",
    ).to_file(package, layer="access_point", driver="GPKG", mode="a")
    return package


def synthetic_air(tmp_path: Path) -> Path:
    """The LAEI's concentrations over AREA and around it: NO2 rises eastwards, PM2.5 is flat."""
    x0, y0 = TO_BNG.transform(-0.160, 51.500)
    x1, y1 = TO_BNG.transform(-0.115, 51.525)
    path = tmp_path / "LAEI2022-Concentrations-Data-CSV.zip"
    points = [
        (x, y)
        for x in range(round(x0 / 20) * 20, round(x1 / 20) * 20 + 1, 20)
        for y in range(round(y0 / 20) * 20, round(y1 / 20) * 20 + 1, 20)
    ]
    with zipfile.ZipFile(path, "w") as archive:
        no2 = ["x,y,conc"] + [f"{x},{y},{20 + (x - x0) / 100}" for x, y in points]
        pm25 = ["x,y,conc"] + [f"{x},{y},9.5" for x, y in points]
        archive.writestr("CSV/LAEI2022_V1_NO2.csv", "\n".join(no2) + "\n")
        archive.writestr("CSV/LAEI2022_V1_PM25.csv", "\n".join(pm25) + "\n")
    return path


def synthetic_noise_tile(tmp_path: Path, kind: str, east_level: float) -> Path:
    """A tile of 10 m pixels over AREA and around it: 45 dB in the west half, `east_level` in the
    east half."""
    x0, y0 = TO_BNG.transform(-0.160, 51.500)
    x1, y1 = TO_BNG.transform(-0.115, 51.525)
    west, north = (x0 // 10) * 10, (y1 // 10 + 1) * 10
    columns, rows = int((x1 - west) // 10) + 2, int((north - y0) // 10) + 2
    split = int((TO_BNG.transform(-0.1375, 51.5)[0] - west) // 10)
    levels = np.full((rows, columns), 45.0, dtype="float32")
    levels[:, split:] = east_level
    path = tmp_path / f"{kind}.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=columns,
        count=1,
        dtype="float32",
        crs="EPSG:27700",
        transform=from_origin(west, north, 10, 10),
        nodata=-96.0,
    ) as file:
        file.write(levels, 1)
    return path


def synthetic_places(tmp_path: Path) -> tuple[Path, pd.DataFrame]:
    """Overture's places: a grocery in the west and a pharmacy in the east of AREA. OpenStreetMap's:
    a gym in the west and a library in the east."""
    west, east = (-0.1495, 51.5120), (-0.1255, 51.5120)
    rows = [
        ("g", west, "West Grocer", "grocery_store"),
        ("p", east, "East Pharmacy", "pharmacy"),
        ("c1", east, "East Cafe", "cafe"),
        ("c2", east, "East Coffee", "coffee_shop"),
        ("c3", west, "West Tea", "tea_room"),
        ("r1", east, "East Thai", "thai_restaurant"),
        ("r2", east, "East Pizza", "pizza_restaurant"),
        ("r3", west, "West Thai", "thai_restaurant"),
    ]
    overture_places = pd.DataFrame(
        {
            "id": [r[0] for r in rows],
            "lng": [r[1][0] for r in rows],
            "lat": [r[1][1] for r in rows],
            "name": [r[2] for r in rows],
            "category": [r[3] for r in rows],
        }
    )
    path = tmp_path / "overture-places.parquet"
    overture_places.to_parquet(path)
    osm_places = pd.DataFrame(
        {
            "lng": [west[0], east[0]],
            "lat": [west[1], east[1]],
            "name": ["West Gym", "East Library"],
            "brand": [None, None],
            "cuisine": [None, None],
            "amenity": [None, "library"],
            "shop": [None, None],
            "leisure": ["fitness_centre", None],
            "religion": [None, None],
        }
    )
    worship = pd.DataFrame(
        {
            "lng": [east[0]] * 10,
            "lat": [east[1]] * 10,
            "name": [None] * 10,
            "brand": [None] * 10,
            "cuisine": [None] * 10,
            "amenity": ["place_of_worship"] * 10,
            "shop": [None] * 10,
            "leisure": [None] * 10,
            "religion": ["hindu"] * 10,
        }
    )
    return path, pd.concat([osm_places, worship], ignore_index=True)


def synthetic_ratings(tmp_path: Path) -> Path:
    """Ten rated food businesses in the west of AREA, all rated 2, and ten in the east, all 5."""
    rows = [
        {
            "name": f"{side} {i}",
            "type": "Cafe",
            "lng": lng + 0.0002 * i,
            "lat": 51.5120,
            "authority": "Westminster",
            "rating": rating,
        }
        for side, lng, rating in (("West", -0.1495, "2"), ("East", -0.1255, "5"))
        for i in range(10)
    ]
    path = tmp_path / "fsa.parquet"
    pd.DataFrame(rows).to_parquet(path)
    return path


def synthetic_boroughs(tmp_path: Path) -> Path:
    """Two boroughs that split AREA at -0.1375: Camden in the west, Westminster in the east."""

    def square(west, east):
        ring = [[west, 51.49], [east, 51.49], [east, 51.53], [west, 51.53], [west, 51.49]]
        return {"type": "Polygon", "coordinates": [ring]}

    features = [
        {
            "type": "Feature",
            "properties": {"LAD25CD": code, "LAD25NM": name},
            "geometry": square(west, east),
        }
        for code, name, west, east in (
            ("E09000007", "Camden", -0.17, -0.1375),
            ("E09000033", "Westminster", -0.1375, -0.10),
        )
    ]
    path = tmp_path / "boroughs.geojson"
    collection = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(collection), encoding="utf-8")
    return path


def synthetic_homes() -> pd.DataFrame:
    """Homes by output area, for the two output areas of AREA (see `synthetic_output_areas`):
    the west one with gigabit broadband for all, the east one for none."""
    return pd.DataFrame(
        {"homes": [100.0, 100.0], "gigabit_homes": [100.0, 0.0]}, index=["W1", "E1"]
    )


def synthetic_ethnic_groups() -> pd.DataFrame:
    """Residents by ethnic group for the two output areas of AREA: the west one of a single
    group, the east one split evenly over four."""
    return pd.DataFrame(
        {"a": [100.0, 25.0], "b": [0.0, 25.0], "c": [0.0, 25.0], "d": [0.0, 25.0]},
        index=["W1", "E1"],
    )


def synthetic_religions() -> pd.DataFrame:
    """Residents by religion for the two output areas of AREA: the west one all Hindu, the east
    one half Christian and half without religion."""
    return pd.DataFrame(
        {"Hindu": [100.0, 0.0], "Christian": [0.0, 50.0], "No religion": [0.0, 50.0]},
        index=["W1", "E1"],
    )


def use_synthetic_data(monkeypatch, tmp_path):
    boundary, grid = synthetic_boundary(tmp_path), synthetic_grid(tmp_path)
    areas, people = synthetic_output_areas(tmp_path), synthetic_residents(tmp_path)
    crimes = synthetic_crimes(tmp_path)
    monkeypatch.setattr(build_module.ons_regions, "fetch", lambda name, data_dir: boundary)
    monkeypatch.setattr(build_module.ptal, "fetch", lambda data_dir: grid)
    monkeypatch.setattr(build_module.output_areas, "fetch", lambda data_dir, bounds: areas)
    monkeypatch.setattr(build_module.census_residents, "fetch", lambda data_dir: people)
    monkeypatch.setattr(build_module.police_uk, "fetch", lambda data_dir: crimes)
    streets, stations = synthetic_streets(tmp_path), synthetic_stations(tmp_path)
    monkeypatch.setattr(build_module.openstreetmap, "fetch", lambda data_dir, region: streets)
    monkeypatch.setattr(build_module.naptan, "fetch", lambda data_dir: stations)
    schools = synthetic_schools(tmp_path)
    monkeypatch.setattr(build_module.gias, "fetch", lambda data_dir: schools)
    tiles = {
        kind: [synthetic_noise_tile(tmp_path, kind, level)]
        for kind, level in (("road", 65.0), ("rail", 50.0), ("aircraft", 60.0))
    }
    monkeypatch.setattr(build_module.defra_noise, "fetch", lambda data_dir, kind, b: tiles[kind])
    overture_path, osm_places = synthetic_places(tmp_path)
    monkeypatch.setattr(build_module.overture, "fetch", lambda data_dir, region, box: overture_path)
    monkeypatch.setattr(build_module.openstreetmap, "places", lambda data_dir, region: osm_places)
    ratings = synthetic_ratings(tmp_path)
    monkeypatch.setattr(build_module.fsa, "fetch", lambda data_dir, region: ratings)
    boroughs = synthetic_boroughs(tmp_path)
    monkeypatch.setattr(
        build_module.ons_local_authorities, "fetch", lambda data_dir, region: boroughs
    )
    monkeypatch.setattr(build_module.ons_rents, "fetch", lambda data_dir: tmp_path / "rents")
    monkeypatch.setattr(
        build_module.ons_rents,
        "read_rents",
        lambda path: {"E09000007": 2900.0, "E09000033": 3100.0},
    )
    monkeypatch.setattr(build_module.mhclg_council_tax, "fetch", lambda data_dir: tmp_path / "tax")
    monkeypatch.setattr(
        build_module.mhclg_council_tax,
        "read_band_d",
        lambda path: {"E09000007": 2207.55, "E09000033": 1056.0},
    )
    monkeypatch.setattr(
        build_module.ofcom, "fetch", lambda data_dir: (tmp_path / "f", tmp_path / "m")
    )
    monkeypatch.setattr(build_module.ofcom, "read_fixed", lambda path: synthetic_homes())
    monkeypatch.setattr(
        build_module.ofcom,
        "read_five_g",
        lambda path: {"E09000007": 40.0, "E09000033": 90.0},
    )
    monkeypatch.setattr(
        build_module.census_ethnic_group, "fetch", lambda data_dir: tmp_path / "ethnic"
    )
    monkeypatch.setattr(
        build_module.census_ethnic_group, "read_groups", lambda path: synthetic_ethnic_groups()
    )
    monkeypatch.setattr(
        build_module.census_religion, "fetch", lambda data_dir: tmp_path / "religion"
    )
    monkeypatch.setattr(
        build_module.census_religion, "read_groups", lambda path: synthetic_religions()
    )
    air = synthetic_air(tmp_path)
    monkeypatch.setattr(build_module.laei, "fetch", lambda data_dir: air)
    park = synthetic_greenspace(tmp_path)
    monkeypatch.setattr(build_module.os_open_greenspace, "fetch", lambda data_dir: park)
    gp_files, postcodes = synthetic_gp_practices(tmp_path), synthetic_postcodes(tmp_path)
    monkeypatch.setattr(build_module.nhs_ods, "fetch", lambda data_dir: gp_files)
    monkeypatch.setattr(build_module.code_point, "fetch", lambda data_dir: postcodes)
    sales, certificates = synthetic_sales()
    monkeypatch.setattr(build_module.hm_land_registry, "fetch", lambda data_dir, years: [])
    monkeypatch.setattr(build_module.hm_land_registry, "read_sales", lambda paths, months: sales)
    monkeypatch.setattr(
        build_module.epc, "certificates", lambda data_dir, region, codes: certificates
    )
    monkeypatch.setattr(build_module.tfl_lines, "fetch", lambda data_dir: tmp_path / "lines")
    monkeypatch.setattr(build_module.tfl_lines, "read_stops", lambda path: synthetic_line_stops())
    monkeypatch.setattr(
        build_module.nhs_gp, "fetch", lambda data_dir: (tmp_path / "p", tmp_path / "w")
    )
    monkeypatch.setattr(
        build_module.nhs_gp, "read_practices", lambda patients, workforce: synthetic_gp_lists()
    )
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


def test_the_bundle_holds_the_walk_to_the_nearest_station(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    minutes = table["station_proximity"]
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    assert minutes.notna().all()
    # The station is at the west end: the walk gets longer eastwards, up to about 20 minutes.
    assert minutes[lng < -0.145].median() < minutes[lng > -0.130].median()
    assert 10 < minutes.max() < 40
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "station-proximity" in {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_walk_to_the_nearest_primary_and_secondary_school(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    west, east = table[lng < -0.145], table[lng > -0.130]
    # The primary school is in the west and the secondary school in the east.
    assert west["primary_schools"].median() < east["primary_schools"].median()
    assert east["secondary_schools"].median() < west["secondary_schools"].median()
    assert table[["primary_schools", "secondary_schools"]].notna().all().all()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {i["id"] for i in manifest["indicators"]}
    assert {"primary-schools", "secondary-schools"} <= ids


def test_the_bundle_holds_the_walk_to_the_nearest_gp_practice(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    # The only practice is in the east, so the walk gets longer westwards.
    assert table["gp_walk"].notna().all()
    assert table[lng > -0.130]["gp_walk"].median() < table[lng < -0.145]["gp_walk"].median()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "gp-walk" in {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_walk_to_the_nearest_green_space(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    # The only way into a park is at the west end, so the walk gets longer eastwards.
    assert table["walk_to_green_space"].notna().all()
    walks = table["walk_to_green_space"]
    assert walks[lng < -0.145].median() < walks[lng > -0.130].median()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "walk-to-green-space" in {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_mean_nitrogen_dioxide_and_fine_particles_of_each_cell(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    assert table["no2"].notna().all() and table["pm25"].notna().all()
    assert table[lng > -0.130]["no2"].median() > table[lng < -0.145]["no2"].median()
    assert table["pm25"].round(6).eq(9.5).all()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert {"no2", "pm25"} <= {i["id"] for i in manifest["indicators"]}


def test_a_commercial_build_leaves_out_the_indicators_whose_dataset_has_no_commercial_licence(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data", commercial=True)
    table = pq.read_table(bundle / "cells.parquet")
    assert "no2" not in table.column_names and "pm25" not in table.column_names
    assert (
        "buying_cost" not in table.column_names
    )  # the addresses' licence is not for commercial use
    assert "gp_walk" in table.column_names  # the cleared ones stay
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "laei" not in {d["id"] for d in manifest["datasets"]}
    assert not {"epc-domestic", "hm-land-registry-price-paid"} & {
        d["id"] for d in manifest["datasets"]
    }


def test_the_command_has_a_commercial_option(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    args = ["build", "london", "--commercial", "--data-dir", str(tmp_path / "data")]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output


def test_the_bundle_holds_the_noise_of_roads_railways_and_aircraft(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    east, west = table[lng > -0.130], table[lng < -0.145]
    for column, level in (("road_noise", 65.0), ("rail_noise", 50.0), ("aircraft_noise", 60.0)):
        assert table[column].notna().all()
        assert west[column].median() == pytest.approx(45.0, abs=1.0)
        assert east[column].median() == pytest.approx(level, abs=1.0)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {i["id"] for i in manifest["indicators"]}
    assert {"road-noise", "rail-noise", "aircraft-noise"} <= ids


def test_the_bundle_holds_the_walks_to_a_grocery_a_pharmacy_a_gym_and_a_library(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    west, east = lng < -0.145, lng > -0.130
    for column, nearer_in_the_west in (
        ("groceries", True),
        ("gyms", True),
        ("pharmacies", False),
        ("libraries", False),
    ):
        walks = table[column]
        assert walks.notna().all()
        near, far = (west, east) if nearer_in_the_west else (east, west)
        assert walks[near].median() < walks[far].median()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert {"groceries", "pharmacies", "gyms", "libraries"} <= {
        i["id"] for i in manifest["indicators"]
    }


def test_the_bundle_holds_the_counts_cuisines_and_hygiene_near_each_cell(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    west, east = table[lng < -0.145], table[lng > -0.130]
    # Two cafés and two restaurants of two cuisines in the east; one of each, of one cuisine, west.
    assert east["cafes"].median() == 2 and west["cafes"].median() == 1
    assert east["restaurant_choice"].median() == 2 and west["restaurant_choice"].median() == 1
    assert east["cuisine_variety"].median() == 2 and west["cuisine_variety"].median() == 1
    assert east["food_hygiene"].median() == 100 and west["food_hygiene"].median() == 0
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {i["id"] for i in manifest["indicators"]}
    assert {"cafes", "restaurant-choice", "cuisine-variety", "food-hygiene"} <= ids


def test_the_bundle_gives_each_cell_the_rent_and_council_tax_of_its_borough(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    assert table["renting_cost"].notna().all() and table["council_tax"].notna().all()
    assert set(table[lng < -0.14]["renting_cost"]) == {2900.0}  # Camden
    assert set(table[lng > -0.135]["renting_cost"]) == {3100.0}  # Westminster
    assert set(table[lng < -0.14]["council_tax"]) == {2207.55}
    assert set(table[lng > -0.135]["council_tax"]) == {1056.0}
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert {"renting-cost", "council-tax"} <= {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_gigabit_share_of_homes_and_the_5g_of_the_borough(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    west, east = table[lng < -0.145], table[lng > -0.130]
    assert west["gigabit_broadband"].median() == pytest.approx(100.0)
    assert east["gigabit_broadband"].median() == pytest.approx(0.0)
    assert set(west["5g_coverage"]) == {40.0}  # Camden
    assert set(east["5g_coverage"]) == {90.0}  # Westminster
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert {"gigabit-broadband", "5g-coverage"} <= {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_diversity_of_each_cells_residents(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    assert table[lng < -0.145]["diversity"].median() == pytest.approx(0.0)
    assert table[lng > -0.130]["diversity"].median() == pytest.approx(0.75)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "diversity" in {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_patients_per_gp_of_the_practices_within_a_walk(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    assert set(table["gp_list_size"].dropna()) == {3000.0}  # 6,000 patients over 2 GPs
    assert table[lng > -0.130]["gp_list_size"].notna().all()  # next to the practice
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "gp-list-size" in {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_the_rail_lines_and_bus_routes_within_a_walk(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    east = table[lng > -0.130]
    assert east["rail_lines_nearby"].max() == 2 and east["bus_routes_nearby"].max() == 3
    assert (east["rail_lines_nearby"] > 0).mean() > 0.5  # a 12-minute walk reaches the stop
    assert (east["bus_routes_nearby"] > 0).any()  # and an 8-minute walk, from the nearer cells
    assert table["rail_lines_nearby"].max() == 2 and table["bus_routes_nearby"].max() == 3
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert {"rail-lines-nearby", "bus-routes-nearby"} <= {i["id"] for i in manifest["indicators"]}


def test_the_bundle_holds_a_column_for_each_option_of_the_choice_indicators(monkeypatch, tmp_path):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    west, east = table[lng < -0.145], table[lng > -0.130]
    assert west["your_community__religion_hindu"].median() == pytest.approx(100.0)
    assert east["your_community__religion_christian"].median() == pytest.approx(50.0)
    assert east["your_community__ethnic_d"].median() == pytest.approx(25.0)  # a quarter of four
    assert east["faith__hindu"].median() < west["faith__hindu"].median()  # the places are east
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    community = next(i for i in manifest["indicators"] if i["id"] == "your-community")
    ids = [o["id"] for o in community["options"]]
    assert "religion-hindu" in ids and "religion-not-answered" not in ids
    faith = next(i for i in manifest["indicators"] if i["id"] == "faith")
    assert [o["id"] for o in faith["options"]] == ["hindu"]


def test_the_bundle_holds_the_price_per_square_metre_of_the_homes_sold_nearby(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    assert set(table["buying_cost"].dropna()) == {10000.0}  # 600,000 over 60 m²
    assert table[lng > -0.130]["buying_cost"].notna().any()  # near the sales
    assert table[lng < -0.145]["buying_cost"].isna().all()  # beyond two steps of them
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert "buying-cost" in {i["id"] for i in manifest["indicators"]}
