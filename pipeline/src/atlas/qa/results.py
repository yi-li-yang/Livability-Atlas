"""The result of one check of the QA report."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal

# A warning is shown and does not stop publishing; a failure does. A check is skipped when the
# bundle lacks an indicator that it reads (a commercial build leaves some out).
Status = Literal["pass", "warn", "fail", "skipped"]

SHOWN = 5  # how many offenders a detail names before it counts the rest


@dataclass(frozen=True)
class Result:
    group: str  # the kind of check: "The bundle", "Datasets", "Values", "Relations", "Known facts"
    name: str  # what it checks, as a sentence that is true when it passes
    status: Status
    detail: str = ""
    why: str = ""  # why the check should hold, where that is worth saying (a relation's reason)


def some(items: Sequence[str]) -> str:
    """Names the first few of a list and counts the rest."""
    shown = ", ".join(items[:SHOWN])
    return shown if len(items) <= SHOWN else f"{shown} and {len(items) - SHOWN} more"


def failures(results: Iterable[Result]) -> list[Result]:
    return [r for r in results if r.status == "fail"]


def worth_a_look(results: Iterable[Result]) -> list[Result]:
    return [r for r in results if r.status in ("fail", "warn")]
