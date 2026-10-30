"""Animal friendliness: the walk to the nearest vet (`vets`) and the nearest pet shop (`pet-shops`),
from Overture's places. See the indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

from atlas.families import Context, Family

VETS = {"veterinarian", "veterinary_care"}
PET_SHOPS = {"pet_store", "aquatic_pet_store"}


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    return {
        "vets": ctx.walk_to_nearest(ctx.places_of(VETS)),
        "pet-shops": ctx.walk_to_nearest(ctx.places_of(PET_SHOPS)),
    }


FAMILY = Family("pets", columns)
