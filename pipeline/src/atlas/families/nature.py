"""Animal friendliness: the nature sites around a cell (`nature-sites`).

The share of the land within 800 m of a cell that lies in a local nature reserve, a national
nature reserve, a site of special scientific interest or ancient woodland, from
planning.data.gov.uk. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

from atlas.datasets.countries.gb import planning_data
from atlas.families import Context, Family
from atlas.indicators.coverage import share_inside
from atlas.spatial.grid import lonlat_box

DATASETS = [
    "local-nature-reserve",
    "national-nature-reserve",
    "site-of-special-scientific-interest",
    "ancient-woodland",
]
REACH = 800.0  # metres: a 10-minute walk at 4.8 km/h


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    box = lonlat_box(ctx.cells, margin=0.05)
    outlines = []
    for dataset in DATASETS:
        areas = planning_data.read_areas(planning_data.fetch(ctx.data_dir, dataset), box)
        if len(areas):
            outlines.extend(areas.to_crs("EPSG:27700").geometry)
    share = share_inside(outlines, ctx.cells, buffer=REACH)
    return {"nature-sites": [float(v) for v in share]}


FAMILY = Family("nature", columns)
