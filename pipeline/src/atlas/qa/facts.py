"""Known-fact assertions: facts about a region that anyone can verify, checked on its bundle.

A fact is a function of the bundle's cells. It reads values at named places, says what it found by
returning it, and raises through `expect` when the data contradict it. A region lists its facts in
`datasets/cities/<region>/facts.py`.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from atlas.qa.cells import Cells, OutsideBundle
from atlas.qa.results import Result, some

GROUP = "Known facts"

Run = Callable[[Cells], str]


class Failed(Exception):
    """A known fact does not hold in the data."""


def expect(holds: bool, found: str) -> None:
    """Raises, with what was found, unless the fact holds."""
    if not holds:
        raise Failed(found)


@dataclass(frozen=True)
class Fact:
    id: str  # the name of its function
    statement: str  # the fact, as a sentence that is true when it holds
    needs: tuple[str, ...]  # the columns it reads: it is skipped where the bundle lacks one
    run: Run


class Facts:
    """A region's facts, registered with a decorator."""

    def __init__(self) -> None:
        self.all: list[Fact] = []

    def add(self, statement: str, *, needs: Sequence[str] = ()) -> Callable[[Run], Run]:
        def register(run: Run) -> Run:
            if any(fact.id == run.__name__ for fact in self.all):
                raise ValueError(f"two facts are called {run.__name__}")
            self.all.append(Fact(run.__name__, statement, tuple(needs), run))
            return run

        return register


def fact_checks(cells: Cells, facts: Sequence[Fact]) -> list[Result]:
    return [_check(cells, fact) for fact in facts]


def _check(cells: Cells, fact: Fact) -> Result:
    missing = [column for column in fact.needs if not cells.has(column)]
    if missing:
        return Result(GROUP, fact.statement, "skipped", f"the bundle lacks {some(missing)}")
    try:
        found = fact.run(cells)
    except Failed as failure:
        return Result(GROUP, fact.statement, "fail", str(failure))
    except OutsideBundle as outside:
        return Result(GROUP, fact.statement, "skipped", outside.args[0])
    except Exception as error:  # a fact that breaks is a failing check, not a crash of the report
        message = error.args[0] if isinstance(error, KeyError) else str(error)
        return Result(GROUP, fact.statement, "fail", f"could not be checked: {message}")
    return Result(GROUP, fact.statement, "pass", found)
