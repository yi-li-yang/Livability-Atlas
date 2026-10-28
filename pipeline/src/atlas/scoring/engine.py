"""The reference scorer for one hex cell, as docs/methodology/scoring.md defines it.

It takes a case in the format of `shared/fixtures/scoring/` and returns the case's `expected`
block. The TypeScript engine of the web app must reproduce the same fixtures. Nodes are plain
dictionaries, so that this scorer and the fixtures share one format.
"""

from typing import Any

LOW_COVERAGE = 0.7  # data coverage below this share of the total weight is flagged

Node = dict[str, Any]


def _clip(x: float) -> float:
    return min(1.0, max(0.0, x))


def curve_score(
    curve: dict[str, Any], value: Any, region_values: list[float] | None = None
) -> float | None:
    """The score of a raw value from 0 (worst) to 1 (best), or None if the curve cannot score it."""
    shape = curve["shape"]
    if shape == "ramp":
        return _clip((value - curve["t0"]) / (curve["t1"] - curve["t0"]))
    if shape == "ideal-range":
        rising = _clip((value - curve["l0"]) / (curve["l1"] - curve["l0"]))
        falling = _clip((value - curve["u0"]) / (curve["u1"] - curve["u0"]))
        return min(rising, falling)
    if shape == "lookup":
        return curve["scores"].get(str(value))
    if shape == "percentile":
        if not region_values:
            return None
        if len(region_values) == 1:
            return 0.5
        worse = sum(
            1 for v in region_values if (v > value if curve["better"] == "lower" else v < value)
        )
        ties = sum(1 for v in region_values if v == value)
        return (worse + 0.5 * (ties - 1)) / (len(region_values) - 1)
    raise ValueError(f"unknown curve shape {shape!r}")


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
    score = curve_score(leaf["curve"], leaf["value"], leaf.get("region_values"))
    if score is None:
        return None
    return 1 - score if leaf.get("flipped") else score


def _score(node: Node, scores: dict[str, float | None]) -> float | None:
    kids = _children(node)
    if not kids:
        scores[node["id"]] = _own_score(node)
        return scores[node["id"]]
    results = [(_weight(child), _score(child, scores)) for child in kids]
    active = [(w, s) for w, s in results if w > 0 and s is not None]
    total = sum(w for w, _ in active)
    scores[node["id"]] = sum(w * s for w, s in active) / total if total > 0 else None
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
    """Scores one hex cell: the livability score, coverage, hard limits and every node."""
    tree = case["tree"]
    scores: dict[str, float | None] = {}
    _score(tree, scores)
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
            "contribution": None if e is None or score is None else 100 * e * score,
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
