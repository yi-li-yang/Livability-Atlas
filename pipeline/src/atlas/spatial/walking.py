"""Walking times along streets and paths, from OpenStreetMap.

Spike S6 found that a walk is a median 1.33 times its straight line, and more than 1.5 times for a
quarter of routes, so the nearest-place indicators measure walks along the network. The network is
the ways that OpenStreetMap tags as streets and paths that people may walk. One shortest-path search
from all the places of a kind at once gives the walk to the nearest of them from every node.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import osmium
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import KDTree

SPEED = 80  # metres a minute: 4.8 km/h, the walking speed TfL uses for PTAL

# Highways that nobody may walk, or that are not yet roads.
CLOSED = {
    "motorway",
    "motorway_link",
    "proposed",
    "construction",
    "raceway",
    "bus_guideway",
    "escape",
}
# What OpenStreetMap calls a way inside a building, which is not a street.
INDOOR = {"corridor"}
# An access tag that shuts a way to the public, unless a foot tag opens it again.
SHUT = {"private", "no"}
OPEN_FOR_FOOT = {"yes", "designated", "permissive"}
_TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
_EPSILON = 1e-6  # metres, so that a place on a node still gives an edge of its own


def _shortest(a: np.ndarray, b: np.ndarray, length: np.ndarray):
    """The edges from `a` to `b`, with the shortest of any that join the same pair."""
    order = np.lexsort((length, b, a))  # by a, then b, then length
    a, b, length = a[order], b[order], length[order]
    first = np.ones(len(a), dtype=bool)
    first[1:] = (a[1:] != a[:-1]) | (b[1:] != b[:-1])
    return a[first], b[first], length[first]


def is_walkable(tags: dict[str, str]) -> bool:
    """Whether a way with these tags is a street or path that people may walk."""
    highway = tags.get("highway")
    if highway is None or highway in CLOSED or highway in INDOOR:
        return False
    foot = tags.get("foot")
    if foot == "no":
        return False
    if foot in OPEN_FOR_FOOT:
        return True
    return tags.get("access") not in SHUT


@dataclass
class Ways:
    """The walkable ways, flat: vertex `i` has the node `refs[i]` at (`x[i]`, `y[i]`) in metres of
    British National Grid, and belongs to way `way[i]`. Consecutive vertices of one way are
    joined."""

    refs: np.ndarray
    x: np.ndarray
    y: np.ndarray
    way: np.ndarray

    @property
    def count(self) -> int:
        return int(self.way.max()) + 1 if len(self.way) else 0

    @classmethod
    def from_lists(cls, ways: Sequence[Sequence[tuple[int, float, float]]]) -> "Ways":
        """Ways given as lists of (node ref, x, y), for tests and small networks."""
        flat = [(ref, x, y, i) for i, way in enumerate(ways) for ref, x, y in way]
        refs, x, y, index = (np.array(column) for column in zip(*flat, strict=True))
        return cls(refs.astype(np.int64), x.astype(float), y.astype(float), index.astype(np.int64))


class _Reader(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[int] = []
        self.lng: list[float] = []
        self.lat: list[float] = []
        self.index: list[int] = []
        self.count = 0

    def way(self, w) -> None:
        if "highway" not in w.tags or not is_walkable({t.k: t.v for t in w.tags}):
            return
        nodes = [n for n in w.nodes if n.location.valid()]
        if len(nodes) < 2:
            return
        for n in nodes:
            self.refs.append(n.ref)
            self.lng.append(n.lon)
            self.lat.append(n.lat)
            self.index.append(self.count)
        self.count += 1


def read_ways(path: Path) -> Ways:
    """The walkable ways of an OpenStreetMap file (`.osm.pbf` or `.osm`), in British National Grid.
    A way's nodes that the file does not locate, as at the edge of an extract, are left out."""
    reader = _Reader()
    reader.apply_file(str(path), locations=True)
    x, y = _TO_BNG.transform(np.array(reader.lng), np.array(reader.lat))
    return Ways(
        refs=np.array(reader.refs, dtype=np.int64),
        x=np.asarray(x, dtype=float),
        y=np.asarray(y, dtype=float),
        way=np.array(reader.index, dtype=np.int64),
    )


class Network:
    """A walking network: nodes at points in metres, and the streets between them."""

    def __init__(
        self, refs: np.ndarray, xy: np.ndarray, src: np.ndarray, dst: np.ndarray, length: np.ndarray
    ):
        self.refs = refs
        self.xy = xy
        self._src, self._dst, self._length = src, dst, length
        # Small pieces of street that join nothing, such as a private estate, are no use for getting
        # anywhere, so points snap only to the largest network.
        count = len(refs)
        joined = csr_matrix((np.ones(len(src)), (src, dst)), shape=(count, count))
        _, labels = connected_components(joined, directed=False)
        self._main = np.flatnonzero(labels == np.bincount(labels).argmax())
        self._tree = KDTree(xy[self._main])

    @classmethod
    def from_ways(cls, ways: "Ways | Sequence[Sequence[tuple[int, float, float]]]") -> "Network":
        """The network of ways: nodes shared by ways join them, and two ways between the same pair
        of nodes count as one."""
        flat = ways if isinstance(ways, Ways) else Ways.from_lists(ways)
        refs, first, inverse = np.unique(flat.refs, return_index=True, return_inverse=True)
        xy = np.column_stack([flat.x[first], flat.y[first]])
        joined = flat.way[1:] == flat.way[:-1]
        a, b = inverse[:-1][joined], inverse[1:][joined]
        keep = a != b
        a, b = a[keep], b[keep]
        length = np.hypot(*(xy[a] - xy[b]).T)
        src, dst, shortest = _shortest(
            np.concatenate([a, b]), np.concatenate([b, a]), np.concatenate([length, length])
        )
        return cls(refs, xy, src, dst, shortest)

    def _nearest(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """The distance from each point to the nearest node, and that node's index."""
        gap, node = self._tree.query(points)
        return np.asarray(gap, dtype=float), self._main[np.asarray(node, dtype=np.int64)]

    def minutes_to_nearest(self, places: np.ndarray, origins: np.ndarray) -> np.ndarray:
        """The minutes on foot from each of `origins` to the nearest of `places` (points in metres).

        Each point first walks in a straight line to the nearest node of the network, and the rest
        of the walk follows the streets. An origin that no place can be reached from gets NaN.
        """
        n = len(self.refs)
        place_gap, place_node = self._nearest(places)
        # A virtual node n is joined to the node nearest each place, so that one search finds the
        # shortest walk from any place. Where several places share a node, the nearest one counts.
        join_node, _, join_gap = _shortest(
            place_node, np.zeros(len(place_node), dtype=np.int64), place_gap + _EPSILON
        )
        graph = csr_matrix(
            (
                np.concatenate([self._length, join_gap]),
                (
                    np.concatenate([self._src, np.full(len(join_node), n)]),
                    np.concatenate([self._dst, join_node]),
                ),
            ),
            shape=(n + 1, n + 1),
        )
        distance = dijkstra(graph, directed=True, indices=n)
        origin_gap, origin_node = self._nearest(origins)
        metres = distance[origin_node] + origin_gap
        return np.where(np.isfinite(metres), metres / SPEED, np.nan)
