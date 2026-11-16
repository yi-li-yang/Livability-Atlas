import h3
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin

from atlas.catalogue.load import load_catalogue
from atlas.datasets.world import worldcover
from atlas.families import Context, discover
from atlas.families import land_cover as family
from atlas.indicators.pooling import mean_over_disk
from atlas.paths import CATALOGUE_DIR

CELL = h3.latlng_to_cell(51.5136, -0.1337, 9)
LAT, LNG = h3.cell_to_latlng(CELL)
PIXEL = 0.0001  # degrees: about 11 m by 7 m


def write_tile(path, left_class: int, right_class: int):
    """A small tile around CELL: its west half is one class and its east half another."""
    width = height = 400  # 0.04 degrees square
    data = np.full((height, width), left_class, dtype=np.uint8)
    data[:, width // 2 :] = right_class
    transform = from_origin(LNG - 0.02, LAT + 0.02, PIXEL, PIXEL)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
    ) as file:
        file.write(data, 1)
    return path


class TestTileNames:
    def test_a_3_degree_tile_is_named_for_its_south_west_corner(self):
        assert worldcover.tile_names((-0.51, 51.28, 0.33, 51.69)) == ["N51W003", "N51E000"]

    def test_a_box_inside_one_tile_names_one(self):
        assert worldcover.tile_names((-2.0, 52.0, -1.0, 53.0)) == ["N51W003"]

    def test_southern_and_western_corners_round_down(self):
        assert worldcover.tile_names((-3.5, -0.5, -3.4, -0.4)) == ["S03W006"]


def test_the_tiles_are_fetched_once_each(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(worldcover, "download", lambda url, target: asked.append(url))
    paths = worldcover.fetch(tmp_path, (-0.51, 51.28, 0.33, 51.69))
    assert [p.name for p in paths] == [
        "ESA_WorldCover_10m_2021_v200_N51W003_Map.tif",
        "ESA_WorldCover_10m_2021_v200_N51E000_Map.tif",
    ]
    assert asked[0].endswith("v200/2021/map/ESA_WorldCover_10m_2021_v200_N51W003_Map.tif")


class TestClassShares:
    def test_a_cell_gets_the_share_of_its_pixels_in_each_class(self, tmp_path):
        tile = write_tile(tmp_path / "t.tif", 10, 80)  # tree to the west of the cell, water east
        shares = worldcover.class_shares([tile], [CELL], {"tree": 10, "water": 80}, stride=1)
        row = shares.loc[CELL]
        assert row["tree"] + row["water"] == pytest.approx(100.0)
        assert 0 <= row["tree"] <= 100

    def test_a_cell_entirely_in_one_class_has_100_percent_of_it(self, tmp_path):
        tile = write_tile(tmp_path / "t.tif", 10, 10)
        shares = worldcover.class_shares([tile], [CELL], {"tree": 10, "water": 80}, stride=1)
        assert shares.loc[CELL, "tree"] == pytest.approx(100.0)
        assert shares.loc[CELL, "water"] == 0.0

    def test_a_cell_outside_the_tiles_has_no_value(self, tmp_path):
        tile = write_tile(tmp_path / "t.tif", 10, 10)
        far = h3.latlng_to_cell(52.5, 0.5, 9)
        shares = worldcover.class_shares([tile], [CELL, far], {"tree": 10}, stride=1)
        assert np.isnan(shares.loc[far, "tree"]) and shares.loc[CELL, "tree"] == 100.0

    def test_sampling_every_few_pixels_gives_about_the_same_share(self, tmp_path):
        tile = write_tile(tmp_path / "t.tif", 10, 80)
        full = worldcover.class_shares([tile], [CELL], {"tree": 10}, stride=1).loc[CELL, "tree"]
        thin = worldcover.class_shares([tile], [CELL], {"tree": 10}, stride=4).loc[CELL, "tree"]
        assert thin == pytest.approx(full, abs=8.0)


class TestMeanOverDisk:
    def test_it_is_the_mean_of_the_cells_around_one_that_the_region_has(self):
        ring = h3.grid_ring(CELL, 1)
        values = pd.Series({CELL: 10.0, ring[0]: 20.0, ring[1]: 30.0})
        mean = mean_over_disk(values, [CELL], steps=1)
        assert mean[CELL] == pytest.approx(20.0)

    def test_a_missing_value_is_not_counted(self):
        ring = h3.grid_ring(CELL, 1)
        values = pd.Series({CELL: 10.0, ring[0]: float("nan")})
        assert mean_over_disk(values, [CELL], steps=1)[CELL] == pytest.approx(10.0)

    def test_no_value_around_gives_none(self):
        values = pd.Series({CELL: float("nan")})
        assert np.isnan(mean_over_disk(values, [CELL], steps=1)[CELL])


def test_the_family_takes_the_tree_share_and_the_water_around_a_cell(tmp_path, monkeypatch):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    ctx = Context("london", region, [CELL], tmp_path, pd.DataFrame(), None)  # type: ignore[arg-type]
    monkeypatch.setattr(worldcover, "fetch", lambda data_dir, box: [tmp_path / "t.tif"])
    monkeypatch.setattr(
        worldcover,
        "class_shares",
        lambda paths, cells, classes, stride=3: pd.DataFrame(
            {"tree": [30.0], "water": [5.0]}, index=cells
        ),
    )
    out = family.columns(ctx)
    assert out == {"tree-canopy": [30.0], "water-nearby": [5.0]}


def test_the_family_is_found_and_its_indicators_are_in_the_catalogue():
    assert "land_cover" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert {"tree-canopy", "water-nearby"} <= ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
