from pathlib import Path

import h3
import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from atlas.datasets.countries.gb import defra_noise
from atlas.indicators import noise

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)


def tile(path: Path, west: float, north: float, levels: np.ndarray, nodata: float) -> Path:
    """A GeoTIFF of 10 m pixels with its top-left corner at (west, north)."""
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=levels.shape[0],
        width=levels.shape[1],
        count=1,
        dtype=levels.dtype,
        crs="EPSG:27700",
        transform=from_origin(west, north, 10, 10),
        nodata=nodata,
    ) as file:
        file.write(levels, 1)
    return path


class TestReadLevels:
    def test_places_each_tile_by_its_corner_and_reads_the_level_of_a_place(self, tmp_path):
        a = tile(tmp_path / "a.tif", 1000, 2000, np.full((3, 3), 55.0, "float32"), -96.0)
        b = tile(tmp_path / "b.tif", 1030, 2000, np.full((3, 3), 62.5, "float32"), -96.0)
        levels = defra_noise.read_levels([a, b])
        got = levels.at(np.array([1005.0, 1035.0]), np.array([1995.0, 1995.0]))
        assert got.tolist() == [55.0, 62.5]

    def test_a_level_below_the_cut_off_or_missing_counts_as_40_decibels(self, tmp_path):
        row = np.array([[0.0, 35.0, -96.0, 71.0]], dtype="float32")
        path = tile(tmp_path / "a.tif", 1000, 2000, row, -96.0)
        got = defra_noise.read_levels([path]).at(
            np.array([1005.0, 1015.0, 1025.0, 1035.0]), np.full(4, 1995.0)
        )
        assert got.tolist() == [40.0, 40.0, 40.0, 71.0]

    def test_the_airport_maps_mark_missing_with_a_huge_number(self, tmp_path):
        row = np.array([[3.4e38, 52.25]], dtype="float64")
        path = tile(tmp_path / "a.tif", 1000, 2000, row, 3.4e38)
        got = defra_noise.read_levels([path]).at(np.array([1005.0, 1015.0]), np.full(2, 1995.0))
        assert got.tolist() == [40.0, 52.25]

    def test_a_place_outside_every_tile_has_no_level(self, tmp_path):
        path = tile(tmp_path / "a.tif", 1000, 2000, np.full((3, 3), 55.0, "float32"), -96.0)
        got = defra_noise.read_levels([path]).at(
            np.array([5.0, 1005.0]), np.array([1995.0, 9000.0])
        )
        assert np.isnan(got).all()


class TestFetch:
    def test_asks_for_the_tiles_that_cover_the_bounds_once_each(self, tmp_path, monkeypatch):
        asked = []

        def fake_get(url, params, timeout):
            asked.append((url, params["coverageId"], params["subset"]))

            class Reply:
                content = b"tiff"

                def raise_for_status(self):
                    return None

            return Reply()

        monkeypatch.setattr(defra_noise.requests, "get", fake_get)
        bounds = (503_500.0, 155_500.0, 513_500.0, 156_000.0)
        paths = defra_noise.fetch(tmp_path, "rail", bounds)
        assert [p.name for p in paths] == [
            "rail-laeq16-503000-155000.tif",
            "rail-laeq16-513000-155000.tif",
        ]
        assert "Rail_Noise_LAeq16hr" in asked[0][1]
        assert asked[0][2] == ["E(503000,513000)", "N(155000,165000)"]
        defra_noise.fetch(tmp_path, "rail", bounds)
        assert len(asked) == 2  # the second call used the files kept

    def test_each_kind_has_its_own_service(self):
        assert set(defra_noise.SOURCES) == {"road", "rail", "aircraft"}


def address_points(cell: str, count: int, offset: float = 0.0) -> np.ndarray:
    lat, lng = h3.cell_to_latlng(cell)
    x, y = TO_BNG.transform(lng, lat)
    return np.array([[x + offset + 5 * i, y] for i in range(count)])


class Flat:
    """A noise map of one level everywhere except at chosen places."""

    def __init__(self, level: float, special: dict[tuple[int, int], float] | None = None):
        self.level, self.special = level, special or {}

    def at(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return np.array(
            [self.special.get((round(a), round(b)), self.level) for a, b in zip(x, y, strict=True)]
        )


class TestMeanLevel:
    def test_a_cell_takes_the_arithmetic_mean_of_the_levels_at_its_addresses(self):
        addresses = address_points(SOHO, 4)
        special = {(round(addresses[0, 0]), round(addresses[0, 1])): 70.0}
        mean = noise.mean_level(Flat(50.0, special), addresses, [SOHO], 9)
        assert mean[SOHO] == pytest.approx((70 + 50 + 50 + 50) / 4)

    def test_a_cell_with_no_address_takes_the_mean_over_its_area(self):
        mean = noise.mean_level(Flat(44.0), np.empty((0, 2)), [SOHO], 9)
        assert mean[SOHO] == pytest.approx(44.0)

    def test_addresses_of_other_cells_do_not_count(self):
        other = h3.latlng_to_cell(51.40, -0.40, 9)
        mean = noise.mean_level(Flat(50.0), address_points(other, 3), [SOHO], 9)
        assert mean[SOHO] == pytest.approx(50.0)  # no address of its own: the area

    def test_a_cell_the_map_does_not_reach_has_no_value(self):
        class Nowhere:
            def at(self, x, y):
                return np.full(len(x), np.nan)

        mean = noise.mean_level(Nowhere(), address_points(SOHO, 3), [SOHO], 9)
        assert np.isnan(mean[SOHO])
