"""Regeneration: how much is being built near a cell, as the new homes completed within a radius."""

import numpy as np
from scipy.spatial import KDTree

from atlas.spatial.grid import cell_centres_bng


def sum_within(
    points: np.ndarray, weights: np.ndarray, cells: list[str], radius: float
) -> np.ndarray:
    """For each cell, the sum of `weights` over the `points` (rows of x, y in metres of British
    National Grid) within `radius` metres of its centre, in a straight line."""
    if len(points) == 0:
        return np.zeros(len(cells))
    found = KDTree(points).query_ball_point(cell_centres_bng(cells), r=radius)
    return np.array([float(weights[list(near)].sum()) for near in found])
