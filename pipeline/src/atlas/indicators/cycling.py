"""Cycling: the length of cycle track near a cell. A track is a cycleway of its own or a track
beside a road, kept apart from motor traffic; a painted lane is not one.
"""

import numpy as np
from scipy.spatial import KDTree

from atlas.spatial.grid import cell_centres_bng


def track_km(segments: np.ndarray, cells: list[str], radius: float) -> np.ndarray:
    """For each cell, the kilometres of track whose segments have their middle within `radius`
    metres of the cell's centre, in a straight line. `segments` holds rows of (x0, y0, x1, y1) in
    metres of British National Grid."""
    if len(segments) == 0:
        return np.zeros(len(cells))
    middles = (segments[:, :2] + segments[:, 2:]) / 2
    lengths = np.hypot(segments[:, 2] - segments[:, 0], segments[:, 3] - segments[:, 1])
    found = KDTree(middles).query_ball_point(cell_centres_bng(cells), r=radius)
    return np.array([lengths[list(near)].sum() / 1000.0 for near in found])
