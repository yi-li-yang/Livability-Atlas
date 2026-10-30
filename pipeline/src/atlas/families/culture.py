"""Culture and leisure: the cultural venues within a 15-minute walk (`cultural-venues-nearby`) and
the pubs, bars and clubs within a 10-minute walk (`nightlife`), from Overture's places. See the
indicators' methods in the catalogue.
"""

from collections.abc import Sequence
from typing import Any

from atlas.families import Context, Family

CULTURE_MINUTES = 15
NIGHTLIFE_MINUTES = 10
CULTURE = {
    "art_gallery",
    "museum",
    "theatre_venue",
    "performing_arts_venue",
    "music_venue",
    "movie_theater",
    "cultural_center",
    "opera_and_ballet",
    "jazz_and_blues_venue",
    "comedy_club",
    "dinner_theater",
    "planetarium",
}
NIGHTLIFE = {
    "pub",
    "gastropub",
    "irish_pub",
    "bar",
    "cocktail_bar",
    "wine_bar",
    "beer_bar",
    "sports_bar",
    "hookah_bar",
    "hotel_bar",
    "dive_bar",
    "champagne_bar",
    "whiskey_bar",
    "cigar_bar",
    "piano_bar",
    "sake_bar",
    "tiki_bar",
    "lounge",
    "dance_club",
    "nightlife_venue",
    "karaoke_venue",
    "gay_bar",
    "beer_garden",
}


def columns(ctx: Context) -> dict[str, Sequence[Any]]:
    venues = ctx.places_of(CULTURE, suffixes=("_museum",))
    return {
        "cultural-venues-nearby": ctx.count_within(venues, CULTURE_MINUTES),
        "nightlife": ctx.count_within(ctx.places_of(NIGHTLIFE), NIGHTLIFE_MINUTES),
    }


FAMILY = Family("culture", columns)
