"""What the QA report knows about one region: its named places, known facts and relations.

They live with the region's datasets, in `datasets/cities/<region>/facts.py`, which defines
`PLACES` (name to latitude and longitude), `FACTS` (a `Facts`) and `RELATIONS`. A region without
that file has none, and its report says so.
"""

from dataclasses import dataclass
from importlib import import_module

from atlas.qa.facts import Fact
from atlas.qa.relations import Relation


@dataclass(frozen=True)
class Regional:
    places: dict[str, tuple[float, float]]
    facts: list[Fact]
    relations: list[Relation]


def regional(region_id: str) -> Regional:
    module = f"atlas.datasets.cities.{region_id.replace('-', '_')}.facts"
    try:
        found = import_module(module)
    except ModuleNotFoundError as error:
        # The region's folder or its facts file is missing, which is fine. Any other missing
        # module, such as an import inside the file, is a real error.
        missing = error.name or ""
        if missing != module and not module.startswith(missing + "."):
            raise
        return Regional({}, [], [])
    return Regional(dict(found.PLACES), list(found.FACTS.all), list(found.RELATIONS))
