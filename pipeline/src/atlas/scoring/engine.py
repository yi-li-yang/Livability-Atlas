"""The reference scorer for one hex cell, as docs/methodology/scoring.md defines it.

It takes a case in the format of `shared/fixtures/scoring/` and returns the case's `expected`
block. The TypeScript engine of the web app must reproduce the same fixtures. Nodes are plain
dictionaries, so that this scorer and the fixtures share one format.
"""

import math
from typing import Any

LOW_COVERAGE = 0.7  # data coverage below this share of the total weight is flagged
WEAK_FLOOR = 0.05  # "no weak spots": a score below this counts as this in the geometric mean

Node = dict[str, Any]


def _clip(x: float) -> float:
    return min(1.0, max(0.0, x))


def _ramp(curve: dict[str, Any], value: float) -> float:
    """A ramp's score: linear between t0 and t1, or on ln(value + offset) with `log`. On a log
    scale a value at or below -offset has no logarithm, and scores as the low end of the values."""
    t0, t1 = curve["t0"], curve["t1"]
    if not curve.get("log"):
        return _clip((value - t0) / (t1 - t0))
    offset = curve.get("offset") or 0
    if value + offset <= 0:
        return 0.0 if t0 < t1 else 1.0
    return _clip(
        (math.log(value + offset) - math.log(t0 + offset))
        / (math.log(t1 + offset) - math.log(t0 + offset))
    )


def curve_score(curve: dict[str, Any], value: Any) -> float | None:
    """The score of a raw value from 0 (worst) to 1 (best), or None if the curve cannot score it."""
    shape = curve["shape"]
    if shape == "ramp":
        return _ramp(curve, value)
    if shape == "ideal-range":
        rising = _clip((value - curve["l0"]) / (curve["l1"] - curve["l0"]))
        falling = _clip((value - curve["u0"]) / (curve["u1"] - curve["u0"]))
        return min(rising, falling)
    if shape == "lookup":
        return curve["scores"].get(str(value))
    raise ValueError(f"unknown curve shape {shape!r}")


def with_band(curve: dict[str, Any], band: list[float] | None) -> dict[str, Any]:
    """An ideal range with the user's band [lo, hi] in place of l1 and u1 (a user-range indicator).

    The slopes keep the widths of the catalogue's curve, so l0 and u0 move with the band. Any other
    curve, or no band, is returned as it is.
    """
    if band is None or curve["shape"] != "ideal-range":
        return curve
    lo, hi = band
    return {
        **curve,
        "l0": lo - (curve["l1"] - curve["l0"]),
        "l1": lo,
        "u1": hi,
        "u0": hi + (curve["u0"] - curve["u1"]),
    }


def _children(node: Node) -> list[Node]:
    return node.get("children", [])


def _weight(node: Node) -> float:
    """A composite factor whose children all weigh 0 counts as weight 0."""
    kids = _children(node)
    if kids and all(_weight(child) == 0 for child in kids):
        return 0
    return node["weight"]


def _own_score(leaf: Node) -> float | None:
    if leaf.get("value") is None:
        return None
    curve = with_band(leaf["curve"], leaf.get("band"))
    score = curve_score(curve, leaf["value"])
    if score is None:
        return None
    return 1 - score if leaf.get("flipped") else score


def _combine(active: list[tuple[float, float]], balanced: bool) -> float | None:
    """The weighted mean of the active children's scores: arithmetic, or, with `balanced` ("no
    weak spots"), geometric, where a score below `WEAK_FLOOR` counts as the floor."""
    total = sum(w for w, _ in active)
    if total <= 0:
        return None
    if balanced:
        return math.exp(sum(w * math.log(max(s, WEAK_FLOOR)) for w, s in active) / total)
    return sum(w * s for w, s in active) / total


def _score(node: Node, scores: dict[str, float | None], balanced: bool = False) -> float | None:
    kids = _children(node)
    if not kids:
        scores[node["id"]] = _own_score(node)
        return scores[node["id"]]
    results = [(_weight(child), _score(child, scores, balanced)) for child in kids]
    active = [(w, s) for w, s in results if w > 0 and s is not None]
    scores[node["id"]] = _combine(active, balanced)
    return scores[node["id"]]


def _shares(node: Node, share: float, out: dict[str, float]) -> None:
    out[node["id"]] = share
    kids = _children(node)
    total = sum(_weight(child) for child in kids)
    for child in kids:
        _shares(child, share * _weight(child) / total if total > 0 else 0.0, out)


def _effective(
    node: Node, share: float | None, scores: dict[str, float | None], out: dict[str, float | None]
) -> None:
    out[node["id"]] = share
    kids = _children(node)
    active = [c for c in kids if _weight(c) > 0 and scores[c["id"]] is not None]
    total = sum(_weight(c) for c in active)
    for child in kids:
        if share is not None and child in active:
            _effective(child, share * _weight(child) / total, scores, out)
        else:
            _effective(child, None, scores, out)


def _leaves(node: Node) -> list[Node]:
    kids = _children(node)
    return [node] if not kids else [leaf for child in kids for leaf in _leaves(child)]


def _check(limit: dict[str, Any], leaves: dict[str, Node]) -> str:
    value = leaves[limit["indicator"]].get("value")
    if value is None:
        return "could_not_check"
    if "max" in limit:
        return "pass" if value <= limit["max"] else "fail"
    if "min" in limit:
        return "pass" if value >= limit["min"] else "fail"
    if "not_in" in limit:
        return "pass" if value not in limit["not_in"] else "fail"
    return "pass" if value in limit["in"] else "fail"


def score_cell(case: dict[str, Any]) -> dict[str, Any]:
    """Scores one hex cell: the livability score, coverage, hard limits and every node.

    A case with `"mode": "balanced"` ("no weak spots") combines the scores of a factor's children
    by their weighted geometric mean instead of the arithmetic mean. Contributions are then null,
    since a geometric mean has none that add up.
    """
    tree = case["tree"]
    balanced = case.get("mode") == "balanced"
    scores: dict[str, float | None] = {}
    _score(tree, scores, balanced)
    shares: dict[str, float] = {}
    _shares(tree, 1.0, shares)
    effective: dict[str, float | None] = {}
    _effective(tree, 1.0, scores, effective)

    leaves = _leaves(tree)
    coverage = sum(shares[leaf["id"]] for leaf in leaves if scores[leaf["id"]] is not None)
    by_id = {leaf["id"]: leaf for leaf in leaves}
    limits = {limit["id"]: _check(limit, by_id) for limit in case.get("hard_limits", [])}

    nodes: dict[str, dict[str, Any]] = {}
    for node_id, score in scores.items():
        e = effective[node_id]
        nodes[node_id] = {
            "score": score,
            "share": shares[node_id],
            "effective_share": e,
            "contribution": (None if balanced or e is None or score is None else 100 * e * score),
        }
    root = scores[tree["id"]]
    return {
        "score": None if root is None else 100 * root,
        "coverage": coverage,
        "low_coverage": coverage < LOW_COVERAGE,
        "excluded": "fail" in limits.values(),
        "limits": limits,
        "nodes": nodes,
    }
