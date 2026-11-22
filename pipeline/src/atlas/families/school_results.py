"""Education: how well the secondary schools nearby do at GCSE (`school-league-tables`).

The mean Attainment 8 score of the state-funded secondary schools within 3 km in a straight line,
each weighted by its pupils. See the indicator's method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.spatial import KDTree

from atlas.datasets.countries.gb import dfe_ks4, gias
from atlas.families import Context, Family
from atlas.spatial.grid import cell_centres_bng

REACH = 3000.0  # metres: about how far a secondary pupil travels in London, in a straight line
MINIMUM = 3  # schools with results that a mean needs in reach


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    register = gias.read_schools(gias.fetch(ctx.data_dir))
    results = dfe_ks4.read_attainment(dfe_ks4.fetch(ctx.data_dir))
    secondary = register.loc[register["secondary"].to_numpy()]
    scored = secondary.loc[secondary["URN"].isin(results.index)]
    score = results.loc[scored["URN"], "attainment8"].to_numpy(dtype=float)
    pupils = results.loc[scored["URN"], "pupils"].to_numpy(dtype=float)
    weight = np.where(
        np.isnan(pupils), np.nanmean(pupils) if np.isfinite(pupils).any() else 1.0, pupils
    )
    places = np.column_stack([scored["Easting"].to_numpy(), scored["Northing"].to_numpy()])
    reach = KDTree(places).query_ball_point(cell_centres_bng(ctx.cells), REACH)
    values: list[float | None] = []
    for found in reach:
        if len(found) >= MINIMUM:
            values.append(float(np.average(score[found], weights=weight[found])))
        else:
            values.append(None)
    return {"school-league-tables": values}


FAMILY = Family("school_results", columns)
