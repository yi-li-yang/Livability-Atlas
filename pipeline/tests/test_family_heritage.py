import math

import h3
import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer
from shapely.geometry import Polygon, box

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import planning_data
from atlas.families import Context, discover
from atlas.families import heritage as family
from atlas.indicators.coverage import share_inside
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
LAT, LNG = h3.cell_to_latlng(CELL)
BOX = (LNG - 0.05, LAT - 0.05, LNG + 0.05, LAT + 0.05)
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)


def listed_csv(tmp_path, rows: list[str]):
    path = tmp_path / "listed-building.csv"
    path.write_text(
        "dataset,end-date,entity,name,point,listed-building-grade\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    return path


class TestListedBuildings:
    def test_it_keeps_the_buildings_in_the_box_that_are_still_listed(self, tmp_path):
        path = listed_csv(
            tmp_path,
            [
                f"listed-building,,1,A,POINT ({LNG} {LAT}),II",
                f"listed-building,2020-01-01,2,Delisted,POINT ({LNG} {LAT}),II",
                "listed-building,,3,Far,POINT (-2.2 51.2),I",
                "listed-building,,4,No point,,II",
            ],
        )
        found = planning_data.read_listed_buildings(path, BOX)
        assert len(found) == 1
        assert found["lng"].iloc[0] == pytest.approx(LNG) and found["lat"].iloc[0] == pytest.approx(
            LAT
        )


class TestConservationAreas:
    def test_it_keeps_the_areas_whose_point_is_in_the_box_as_polygons(self, tmp_path):
        ring = f"{LNG} {LAT},{LNG + 0.001} {LAT},{LNG + 0.001} {LAT + 0.001},{LNG} {LAT}"
        wkt = f"MULTIPOLYGON ((({ring})))"
        path = tmp_path / "conservation-area.csv"
        path.write_text(
            "dataset,end-date,geometry,point\n"
            f'conservation-area,,"{wkt}",POINT ({LNG} {LAT})\n'
            f'conservation-area,,"{wkt}",POINT (-2.2 51.2)\n'
            f"conservation-area,,,POINT ({LNG} {LAT})\n",
            encoding="utf-8",
        )
        areas = planning_data.read_areas(path, BOX)
        assert len(areas) == 1 and areas.crs == "EPSG:4326"


def test_an_outline_of_several_megabytes_is_read(tmp_path):
    turn = [2 * math.pi * i / 90000 for i in range(90000)]
    points = [f"{LNG + 0.001 * math.cos(t):.9f} {LAT + 0.001 * math.sin(t):.9f}" for t in turn]
    wkt = f"MULTIPOLYGON ((({','.join(points)},{points[0]})))"
    assert len(wkt) > 2_000_000
    path = tmp_path / "ancient-woodland.csv"
    row = f'ancient-woodland,,"{wkt}",POINT ({LNG} {LAT})'
    path.write_text("dataset,end-date,geometry,point\n" + row + "\n" + row + "\n", encoding="utf-8")
    assert len(planning_data.read_areas(path, BOX)) == 2


def test_the_files_are_fetched_once_to_the_planning_folder(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(planning_data, "download", lambda url, target: asked.append((url, target)))
    path = planning_data.fetch(tmp_path, "listed-building")
    assert path == tmp_path / "raw" / "planning" / "listed-building.csv"
    assert asked[0][0] == "https://files.planning.data.gov.uk/dataset/listed-building.csv"


class TestShareInside:
    def cell_outline(self):
        boundary = h3.cell_to_boundary(CELL)
        xs, ys = TO_BNG.transform([lng for _, lng in boundary], [lat for lat, _ in boundary])
        return Polygon(zip(xs, ys, strict=True))

    def test_it_is_the_percent_of_each_cell_inside_the_polygons(self):
        outline = self.cell_outline()
        x0, y0, x1, y1 = outline.bounds
        half = box(x0 - 10, y0 - 10, (x0 + x1) / 2, y1 + 10)
        share = share_inside([half], [CELL])
        assert 35 < share[CELL] < 65

    def test_a_cell_outside_every_polygon_has_0(self):
        far = box(0, 0, 10, 10)
        assert share_inside([far], [CELL])[CELL] == 0.0

    def test_no_polygons_gives_0(self):
        assert share_inside([], [CELL])[CELL] == 0.0


def test_the_family_counts_listed_buildings_within_a_walk_and_the_conservation_share(
    tmp_path, monkeypatch
):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]

    class Network:
        def groups_within(self, groups, origins, minutes):
            self.minutes = minutes
            return [[np.arange(len(g)) for _ in origins] for g in groups]

    network = Network()
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), network)  # type: ignore[arg-type]
    monkeypatch.setattr(planning_data, "fetch", lambda data_dir, dataset: tmp_path / dataset)
    monkeypatch.setattr(
        planning_data,
        "read_listed_buildings",
        lambda path, box: pd.DataFrame({"lng": [LNG] * 3, "lat": [LAT] * 3}),
    )
    monkeypatch.setattr(planning_data, "read_areas", lambda path, box: _empty())
    out = family.columns(ctx)
    assert out["local-character"] == [3] and out["conservation-areas"] == [0.0]
    assert network.minutes == family.WALK_MINUTES  # type: ignore[attr-defined]


def _empty():
    import geopandas as gpd

    return gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:4326")


def test_the_family_is_found_and_its_indicators_are_in_the_catalogue():
    assert "heritage" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert {"local-character", "conservation-areas"} <= ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
