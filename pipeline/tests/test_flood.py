import h3
import numpy as np
import pytest
from pyproj import Transformer

from atlas.datasets.countries.gb import ea_flood_risk as ea
from atlas.indicators import flood

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
A = h3.latlng_to_cell(51.5136, -0.1337, 9)  # Soho

HIGH = (85, 91, 157, 255)
MEDIUM = (154, 159, 222, 255)
LOW = (195, 224, 255, 255)
VERY_LOW = (200, 247, 255, 255)
CLEAR = (255, 255, 255, 0)
OUTLINE = (176, 179, 180, 255)


def image(*rows):
    return np.array(rows, dtype=np.uint8)


class TestClassify:
    def test_each_band_of_the_legend_has_its_class(self):
        pixels = image([HIGH, MEDIUM, LOW, VERY_LOW, CLEAR])
        assert ea.classify(pixels).tolist() == [[ea.HIGH, ea.MEDIUM, ea.LOW, ea.VERY_LOW, ea.NONE]]

    def test_a_pixel_with_no_polygon_is_outside_every_band(self):
        assert ea.classify(image([(10, 20, 30, 0)]))[0, 0] == ea.NONE

    def test_outlines_and_partly_transparent_edges_are_unknown(self):
        pixels = image([OUTLINE, (154, 159, 222, 128), (0, 0, 0, 255), (150, 160, 220, 255)])
        assert (ea.classify(pixels) == ea.UNKNOWN).all()

    def test_a_colour_within_a_few_levels_of_a_band_still_counts(self):
        assert ea.classify(image([(86, 90, 158, 255)]))[0, 0] == ea.HIGH


class TestTiles:
    def test_the_tiles_cover_the_bounds_and_nothing_is_left_out(self):
        tiles = list(ea.tiles((500_000, 150_000, 525_000, 160_000), resolution=10, size=1000))
        assert len({(t.x, t.y) for t in tiles}) == len(tiles)
        assert min(t.x for t in tiles) <= 500_000 and max(t.x + 10_000 for t in tiles) >= 525_000
        assert min(t.y for t in tiles) <= 150_000 and max(t.y + 10_000 for t in tiles) >= 160_000
        assert len(tiles) == 3 * 1

    def test_the_mosaic_shape_follows_the_bounds(self):
        rows, cols = ea.shape((500_000, 150_000, 505_000, 152_000), resolution=10)
        assert (rows, cols) == (200, 500)


def mosaic_with(cell: str, share_at_risk: float):
    """A mosaic that is medium risk across a fraction of the cell's width from the west."""
    lat, lng = h3.cell_to_latlng(cell)
    x, y = TO_BNG.transform(lng, lat)
    bounds = (x - 600, y - 600, x + 600, y + 600)
    rows, cols = ea.shape(bounds, resolution=10)
    classes = np.full((rows, cols), ea.VERY_LOW, dtype=np.uint8)
    west = x - 175  # the cell is about 350 m across
    cut = west + share_at_risk * 350
    xs = bounds[0] + (np.arange(cols) + 0.5) * 10
    classes[:, xs < cut] = ea.MEDIUM
    return ea.Mosaic(classes=classes, x=bounds[0], y=bounds[3], resolution=10)


class TestShareAtRisk:
    def test_a_cell_wholly_in_the_safe_bands_has_a_share_of_zero(self):
        result = flood.share_at_risk(mosaic_with(A, 0.0), [A], resolution=9)
        assert result[A] == pytest.approx(0, abs=1)

    def test_a_cell_wholly_in_medium_or_high_has_a_share_of_100(self):
        result = flood.share_at_risk(mosaic_with(A, 2.0), [A], resolution=9)
        assert result[A] == pytest.approx(100, abs=1)

    def test_a_cell_partly_at_risk_has_the_share_of_its_area(self):
        # Hexagons are not the same width everywhere, so allow a few points either way.
        result = flood.share_at_risk(mosaic_with(A, 0.5), [A], resolution=9)
        assert result[A] == pytest.approx(50, abs=8)

    def test_high_counts_like_medium_and_low_does_not(self):
        mosaic = mosaic_with(A, 2.0)
        mosaic.classes[:] = ea.HIGH
        assert flood.share_at_risk(mosaic, [A], 9)[A] == pytest.approx(100, abs=1)
        mosaic.classes[:] = ea.LOW
        assert flood.share_at_risk(mosaic, [A], 9)[A] == pytest.approx(0, abs=1)

    def test_pixels_with_no_class_are_left_out_of_the_share(self):
        mosaic = mosaic_with(A, 2.0)  # all medium
        mosaic.classes[:, ::2] = ea.UNKNOWN  # half the pixels are outlines
        assert flood.share_at_risk(mosaic, [A], 9)[A] == pytest.approx(100, abs=1)

    def test_a_cell_with_nothing_to_read_has_no_value(self):
        mosaic = mosaic_with(A, 0.0)
        mosaic.classes[:] = ea.UNKNOWN
        assert np.isnan(flood.share_at_risk(mosaic, [A], 9)[A])

    def test_a_cell_outside_the_mosaic_has_no_value(self):
        far = h3.latlng_to_cell(51.9, -0.9, 9)
        assert np.isnan(flood.share_at_risk(mosaic_with(A, 0.5), [far], 9)[far])
