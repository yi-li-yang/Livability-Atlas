"""Urban form and change: the new homes completed within 1 km of a cell in five financial years
(`regeneration`), from the GLA's Planning London Datahub (`planning_datahub`). See the indicator's
method in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

from atlas.datasets.cities.london import planning_datahub
from atlas.families import Context, Family
from atlas.indicators import regeneration

RADIUS = 1000.0  # metres, in a straight line


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    schemes = planning_datahub.read_completions(planning_datahub.fetch(ctx.data_dir))
    built = schemes.loc[schemes["gained"] > 0]
    homes = regeneration.sum_within(
        built[["x", "y"]].to_numpy(dtype=float),
        built["gained"].to_numpy(dtype=float),
        ctx.cells,
        RADIUS,
    )
    return {"regeneration": [float(v) for v in homes]}


# The Datahub is London's, and its licence is not stated (D07): a commercial build leaves it out.
FAMILY = Family(
    "regeneration",
    columns,
    regions=("london",),
    built_from={"regeneration": ("gla-planning-london-datahub",)},
)
