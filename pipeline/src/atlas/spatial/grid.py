"""The hex grid of a region (D04): H3 cells, chosen by their centres."""

import json
from pathlib import Path

import h3
from pyproj import Transformer
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.geometry.base import BaseGeometry


def region_cells(boundary: BaseGeometry, resolution: int) -> list[str]:
    """The H3 cells of `resolution` whose centres lie inside `boundary`, sorted.

    The boundary is in longitude and latitude (WGS 84). A cell that straddles the edge belongs
    to the region if its centre does, so a cell is in exactly one region.
    """
    if not 0 <= resolution <= 15:
        raise ValueError(f"H3 has no resolution {resolution}")
    polygons = list(boundary.geoms) if isinstance(boundary, MultiPolygon) else [boundary]
    cells: set[str] = set()
    for polygon in polygons:
        if not isinstance(polygon, Polygon):
            continue
        outer = [(lat, lng) for lng, lat in polygon.exterior.coords]
        holes = [[(lat, lng) for lng, lat in ring.coords] for ring in polygon.interiors]
        cells |= set(h3.h3shape_to_cells(h3.LatLngPoly(outer, *holes), resolution))
    return sorted(cells)


def boundary_from_geojson(path: Path, name_field: str, name: str) -> BaseGeometry:
    """The geometry of the feature whose `name_field` is `name`, from a GeoJSON file in WGS 84."""
    collection = json.loads(path.read_text(encoding="utf-8"))
    for feature in collection["features"]:
        if feature["properties"].get(name_field) == name:
            return shape(feature["geometry"])
    raise KeyError(f"{path.name} has no feature with {name_field} = {name!r}")


def bounds_bng(cells: list[str], margin: float = 0.0) -> tuple[float, float, float, float]:
    """The box around `cells`, widened by `margin` metres, in British National Grid:
    x min, y min, x max, y max. For asking a service for what lies within a region."""
    points = [h3.cell_to_latlng(c) for c in cells]
    to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    xs, ys = to_bng.transform([p[1] for p in points], [p[0] for p in points])
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
