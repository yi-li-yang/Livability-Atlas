import json

import h3
import pytest
from shapely.geometry import Point, Polygon, box, shape

from atlas.spatial.grid import boundary_from_geojson, region_cells

SQUARE = box(-0.10, 51.50, -0.09, 51.51)  # about 0.7 km by 1.1 km


def test_a_region_is_covered_by_the_cells_whose_centres_lie_inside_it():
    cells = region_cells(SQUARE, 9)
    assert 5 <= len(cells) <= 14
    for cell in cells:
        lat, lng = h3.cell_to_latlng(cell)
        assert SQUARE.contains(Point(lng, lat))
        assert h3.get_resolution(cell) == 9


def test_the_cells_come_sorted_and_without_duplicates():
    cells = region_cells(SQUARE, 9)
    assert cells == sorted(set(cells))


def test_a_hole_in_a_region_has_no_cells():
    outer = [(-0.12, 51.49), (-0.08, 51.49), (-0.08, 51.52), (-0.12, 51.52)]
    hole = [(-0.105, 51.499), (-0.095, 51.499), (-0.095, 51.511), (-0.105, 51.511)]
    donut = Polygon(outer, [hole])
    cells = region_cells(donut, 9)
    assert cells
    for cell in cells:
        lat, lng = h3.cell_to_latlng(cell)
        assert not Polygon(hole).contains(Point(lng, lat))


def test_a_region_in_pieces_is_covered_in_each():
    far = box(0.20, 51.50, 0.21, 51.51)
    both = region_cells(SQUARE.union(far), 9)
    assert set(region_cells(SQUARE, 9)) | set(region_cells(far, 9)) == set(both)


def test_a_coarser_grid_has_fewer_cells():
    big = box(-0.20, 51.40, 0.0, 51.55)
    assert len(region_cells(big, 8)) < len(region_cells(big, 9))


def test_a_resolution_h3_does_not_have_is_an_error():
    with pytest.raises(ValueError):
        region_cells(SQUARE, 16)


def geojson(*features):
    return json.dumps({"type": "FeatureCollection", "features": list(features)})


def feature(name, geometry):
    return {
        "type": "Feature",
        "properties": {"RGN25NM": name},
        "geometry": json.loads(json.dumps(geometry.__geo_interface__)),
    }


def test_a_boundary_is_read_by_the_name_of_its_area(tmp_path):
    path = tmp_path / "regions.geojson"
    path.write_text(
        geojson(feature("London", SQUARE), feature("Wales", box(-3, 52, -2.9, 52.1))),
        encoding="utf-8",
    )
    boundary = boundary_from_geojson(path, "RGN25NM", "London")
    assert shape(boundary.__geo_interface__).equals(SQUARE)


def test_a_boundary_that_is_not_there_is_an_error(tmp_path):
    path = tmp_path / "regions.geojson"
    path.write_text(geojson(feature("Wales", SQUARE)), encoding="utf-8")
    with pytest.raises(KeyError):
        boundary_from_geojson(path, "RGN25NM", "London")
