import json
from pathlib import Path

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon

from atlas.datasets.countries.gb import hoc_msoa_names, ons_msoa
from atlas.spatial import neighbourhoods
from atlas.spatial.grid import cell_centres_bng


def boundaries(tmp_path: Path, rows: list[tuple[str, list]]) -> Path:
    path = tmp_path / "msoa.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"MSOA21CD": code, "other": 1},
                        "geometry": {"type": "Polygon", "coordinates": [ring]},
                    }
                    for code, ring in rows
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


class TestBoundaries:
    def test_msoas_are_read_in_british_national_grid_with_only_their_code(self, tmp_path):
        ring = [
            [530000, 180000],
            [530100, 180000],
            [530100, 180100],
            [530000, 180100],
            [530000, 180000],
        ]
        path = boundaries(tmp_path, [("E02000001", ring)])
        areas = ons_msoa.read_boundaries(path)
        assert list(areas.columns) == ["MSOA21CD", "geometry"]
        assert areas.crs is not None and areas.crs.to_epsg() == 27700

    def test_the_boundaries_are_fetched_from_the_ons_service(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            ons_msoa,
            "fetch_features",
            lambda data_dir, name, service, field, bounds: asked.append((name, field)) or tmp_path,
        )
        ons_msoa.fetch(tmp_path, (0.0, 0.0, 1.0, 1.0))
        assert asked == [("msoa", "MSOA21CD")]


class TestNames:
    def csv(self, tmp_path: Path) -> Path:
        path = tmp_path / "MSOA-Names-Latest2.csv"
        path.write_text(
            "﻿msoa21cd,msoa21nm,msoa21nmw,msoa21hclnm,msoa21hclnmw,localauthorityname,type\n"
            "E02000001,City of London 001,City of London 001,City of London,,City of London,x\n"
            "E02000576,Westminster 013,Westminster 013,,,Westminster,x\n"
            "E02000577,Westminster 014,Westminster 014,Soho,,Westminster,x\n",
            encoding="utf-8",
        )
        return path

    def test_each_msoa_has_the_house_of_commons_librarys_name_and_its_borough(self, tmp_path):
        names = hoc_msoa_names.read_names(self.csv(tmp_path))
        assert names.loc["E02000577", "name"] == "Soho"
        assert names.loc["E02000577", "area"] == "Westminster"

    def test_an_msoa_without_a_friendly_name_keeps_the_ons_name(self, tmp_path):
        names = hoc_msoa_names.read_names(self.csv(tmp_path))
        assert names.loc["E02000576", "name"] == "Westminster 013"

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(
            hoc_msoa_names, "download", lambda url, target: asked.append(target.name)
        )
        assert hoc_msoa_names.fetch(tmp_path).name == "MSOA-Names-Latest2.csv"
        assert asked == ["MSOA-Names-Latest2.csv"]


def square_around(cell: str, half: float) -> Polygon:
    x, y = cell_centres_bng([cell])[0]
    return Polygon(
        [(x - half, y - half), (x + half, y - half), (x + half, y + half), (x - half, y + half)]
    )


class TestNeighbourhoodOf:
    soho = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def areas(self, shapes: dict[str, Polygon]) -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {"MSOA21CD": list(shapes)}, geometry=list(shapes.values()), crs="EPSG:27700"
        )

    def test_a_cell_takes_the_msoa_that_holds_its_centre(self):
        near = h3.grid_ring(self.soho, 4)[0]
        areas = self.areas({"A": square_around(self.soho, 300), "B": square_around(near, 300)})
        found = neighbourhoods.neighbourhood_of(areas, [self.soho, near])
        assert found == ["A", "B"]

    def test_a_cell_just_outside_every_msoa_takes_the_nearest_within_reach(self):
        areas = self.areas({"A": square_around(self.soho, 100)})
        neighbour = h3.grid_ring(self.soho, 1)[0]  # about 175 m from the middle of A
        assert neighbourhoods.neighbourhood_of(areas, [neighbour], reach=500.0) == ["A"]

    def test_a_cell_far_from_every_msoa_has_none(self):
        areas = self.areas({"A": square_around(self.soho, 100)})
        far = h3.latlng_to_cell(51.40, -0.40, 9)
        assert neighbourhoods.neighbourhood_of(areas, [far], reach=500.0) == [None]


class TestListed:
    def test_the_msoas_in_use_are_listed_once_in_order_and_each_cell_points_at_its_one(self):
        names = pd.DataFrame(
            {"name": ["Soho", "Fitzrovia", "Unused"], "area": ["Westminster", "Camden", "X"]},
            index=["B", "A", "C"],
        )
        listed, pointers = neighbourhoods.listed(["A", "B", None, "A"], names)
        assert listed == [("Fitzrovia", "Camden"), ("Soho", "Westminster")]
        assert pointers == [0, 1, None, 0]

    def test_an_msoa_with_no_name_is_called_by_its_code(self):
        names = pd.DataFrame({"name": ["Soho"], "area": ["Westminster"]}, index=["B"])
        listed, pointers = neighbourhoods.listed(["Z9"], names)
        assert listed == [("Z9", "")] and pointers == [0]
