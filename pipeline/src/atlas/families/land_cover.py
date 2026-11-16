"""Environment: the tree cover around a cell (`tree-canopy`) and the water within a walk
(`water-nearby`), from ESA WorldCover's 10 m land cover map. See the indicators' methods in the
catalogue.
"""

from collections.abc import Sequence
from typing import Any, cast

import pandas as pd

from atlas.datasets.world import worldcover
from atlas.families import Context, Family
from atlas.indicators.pooling import mean_over_disk
from atlas.spatial.grid import lonlat_box

CLASSES = {"tree": 10, "water": 80}  # WorldCover's codes: tree cover and permanent water bodies
CANOPY_STEPS = 1  # the cell and its neighbours: about 500 m across
WATER_STEPS = 3  # three cells out: about 900 m from the cell's centre


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    paths = worldcover.fetch(ctx.data_dir, lonlat_box(ctx.cells, margin=0.02))
    shares = worldcover.class_shares(paths, ctx.cells, CLASSES)
    tree = mean_over_disk(cast(pd.Series, shares["tree"]), ctx.cells, CANOPY_STEPS)
    water = mean_over_disk(cast(pd.Series, shares["water"]), ctx.cells, WATER_STEPS)
    return {
        "tree-canopy": [None if pd.isna(v) else float(v) for v in tree],
        "water-nearby": [None if pd.isna(v) else float(v) for v in water],
    }


FAMILY = Family("land_cover", columns)
