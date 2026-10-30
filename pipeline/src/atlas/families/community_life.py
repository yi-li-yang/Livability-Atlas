"""Community and people: the walk to the nearest community centre (`community-spaces`) and the
LGBTQ+ venues within a 30-minute walk (`lgbtq-friendly-venues`), from Overture's places. See the
indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

from atlas.families import Context, Family

LGBTQ_MINUTES = 30
COMMUNITY_SPACES = {"community_center"}
LGBTQ_VENUES = {"gay_bar", "gay_and_lesbian_services_organization"}


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    return {
        "community-spaces": ctx.walk_to_nearest(ctx.places_of(COMMUNITY_SPACES)),
        "lgbtq-friendly-venues": ctx.count_within(ctx.places_of(LGBTQ_VENUES), LGBTQ_MINUTES),
    }


FAMILY = Family("community_life", columns)
