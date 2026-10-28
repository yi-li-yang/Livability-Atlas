import json
import math
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from atlas.paths import REPO_ROOT
from atlas.scoring.engine import curve_score, score_cell

FIXTURES = sorted((REPO_ROOT / "shared" / "fixtures" / "scoring").glob("*.json"))
TOLERANCE = 1e-9


def load(path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def same(actual: Any, expected: Any, where: str) -> None:
    if expected is None or actual is None:
        assert actual is expected, where
    elif isinstance(expected, bool | str):
        assert actual == expected, where
    elif isinstance(expected, int | float):
        assert math.isclose(actual, expected, abs_tol=TOLERANCE), f"{where}: {actual} != {expected}"
    elif isinstance(expected, dict):
        assert set(actual) == set(expected), f"{where}: {sorted(actual)} != {sorted(expected)}"
        for key in expected:
            same(actual[key], expected[key], f"{where}.{key}")
    else:
        raise AssertionError(f"{where}: unexpected {expected!r}")


def test_there_are_golden_cases():
    assert len(FIXTURES) >= 12


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_the_scorer_reproduces_each_golden_case(path):
    case = load(path)
    same(score_cell(case), case["expected"], case["id"])


def children(node: dict[str, Any]) -> list[dict[str, Any]]:
    return node.get("children", [])


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_each_golden_case_adds_up_by_itself(path):
    """The expected numbers are written by hand, so check them against the method's identities."""
    case = load(path)
    nodes = case["expected"]["nodes"]
    root = nodes["root"]
    if case["expected"]["score"] is not None:
        assert math.isclose(case["expected"]["score"], 100 * root["score"], abs_tol=TOLERANCE)
        assert math.isclose(root["contribution"], case["expected"]["score"], abs_tol=TOLERANCE)

    def walk(node: dict[str, Any]) -> None:
        if not children(node):
            return
        mine = nodes[node["id"]]
        shares = [nodes[c["id"]]["share"] for c in children(node)]
        assert math.isclose(sum(shares), mine["share"], abs_tol=TOLERANCE) or mine["share"] == 0
        active = [
            nodes[c["id"]] for c in children(node) if nodes[c["id"]]["effective_share"] is not None
        ]
        if active and mine["contribution"] is not None:
            assert math.isclose(
                sum(a["effective_share"] for a in active),
                mine["effective_share"],
                abs_tol=TOLERANCE,
            )
            assert math.isclose(
                sum(a["contribution"] for a in active), mine["contribution"], abs_tol=TOLERANCE
            )
        for child in children(node):
            walk(child)

    walk(case["tree"])


def test_a_ramp_is_flat_beyond_its_thresholds():
    ramp = {"shape": "ramp", "t0": 25, "t1": 5}
    assert curve_score(ramp, 9) == pytest.approx(0.8)
    assert curve_score(ramp, 100) == 0
    assert curve_score(ramp, -3) == 1


def test_a_lookup_does_not_score_an_unlisted_category():
    assert curve_score({"shape": "lookup", "scores": {"low": 1}}, "high") is None


# --- Properties of the method, on random trees ---

weights = st.integers(min_value=0, max_value=5)
values = st.one_of(st.none(), st.floats(min_value=0, max_value=1))


@st.composite
def trees(draw, depth: int = 0, prefix: str = "n") -> dict[str, Any]:
    if depth >= 2 or draw(st.booleans()):
        return {
            "id": prefix,
            "weight": draw(weights),
            "curve": {"shape": "ramp", "t0": 0, "t1": 1},
            "value": draw(values),
        }
    count = draw(st.integers(min_value=1, max_value=3))
    return {
        "id": prefix,
        "weight": draw(weights),
        "children": [draw(trees(depth=depth + 1, prefix=f"{prefix}.{i}")) for i in range(count)],
    }


def as_case(tree: dict[str, Any]) -> dict[str, Any]:
    tree = {**tree, "id": "root", "weight": 1}
    if "children" not in tree:
        tree = {"id": "root", "weight": 1, "children": [{**tree, "id": "only"}]}
    return {"tree": tree, "hard_limits": []}


@settings(max_examples=200, deadline=None)
@given(trees())
def test_contributions_add_up_to_the_livability_score(tree):
    result = score_cell(as_case(tree))
    if result["score"] is None:
        assert result["nodes"]["root"]["contribution"] is None
        return
    assert 0 <= result["score"] <= 100
    assert math.isclose(result["nodes"]["root"]["contribution"], result["score"], abs_tol=TOLERANCE)

    def check(node: dict[str, Any]) -> None:
        kids = children(node)
        mine = result["nodes"][node["id"]]
        if not kids or mine["contribution"] is None:
            return
        counted = [result["nodes"][c["id"]]["contribution"] for c in kids]
        total = sum(c for c in counted if c is not None)
        assert math.isclose(total, mine["contribution"], abs_tol=1e-7)
        for kid in kids:
            check(kid)

    check(as_case(tree)["tree"])


@settings(max_examples=200, deadline=None)
@given(trees())
def test_coverage_is_a_share_and_scores_stay_between_0_and_1(tree):
    result = score_cell(as_case(tree))
    assert -TOLERANCE <= result["coverage"] <= 1 + TOLERANCE
    for node in result["nodes"].values():
        assert node["score"] is None or -TOLERANCE <= node["score"] <= 1 + TOLERANCE


@settings(max_examples=200, deadline=None)
@given(trees(), st.integers(min_value=2, max_value=5))
def test_scaling_every_weight_changes_nothing(tree, factor):
    def scale(node: dict[str, Any]) -> dict[str, Any]:
        scaled = {**node, "weight": node["weight"] * factor}
        if "children" in node:
            scaled["children"] = [scale(c) for c in node["children"]]
        return scaled

    case = as_case(tree)
    a = score_cell(case)
    b = score_cell({**case, "tree": {**scale(case["tree"]), "weight": 1}})
    assert (a["score"] is None) == (b["score"] is None)
    if a["score"] is not None:
        assert math.isclose(a["score"], b["score"], abs_tol=1e-7)
        assert math.isclose(a["coverage"], b["coverage"], abs_tol=1e-7)
