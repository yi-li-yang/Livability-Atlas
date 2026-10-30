import h3
import numpy as np
import pandas as pd
import pytest

from atlas.catalogue.load import load_catalogue
from atlas.families import Context, community_life, culture, discover, pets, work
from atlas.indicators import places
from atlas.paths import CATALOGUE_DIR

CENTRE = h3.latlng_to_cell(51.5136, -0.1337, 9)
NEIGHBOUR = h3.grid_ring(CENTRE, 1)[0]
LAT, LNG = h3.cell_to_latlng(CENTRE)


class FakeNetwork:
    """Every place is 7 minutes away, and every place is within reach of every origin."""

    def minutes_to_nearest(self, places, origins):
        return np.full(len(origins), 7.0 if len(places) else np.nan)

    asked: list[float]

    def groups_within(self, groups, origins, minutes):
        self.asked = [*getattr(self, "asked", []), minutes]
        return [[np.arange(len(g)) for _ in origins] for g in groups]


def overture(*categories: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [str(i) for i in range(len(categories))],
            "lng": [LNG] * len(categories),
            "lat": [LAT] * len(categories),
            "name": ["x"] * len(categories),
            "category": list(categories),
        }
    )


def context(tmp_path, found: pd.DataFrame, cells=None) -> Context:
    cells = cells or [CENTRE, NEIGHBOUR]
    ctx = Context("london", None, cells, tmp_path, pd.DataFrame(), FakeNetwork())  # type: ignore[arg-type]
    ctx.__dict__["overture"] = found  # stands in for the cached property
    return ctx


class TestLocated:
    def test_it_keeps_the_categories_named_and_those_with_a_suffix_and_puts_them_in_metres(self):
        found = overture("pub", "museum", "art_museum", "bakery", "carpet_store")
        kept = places.located(found, {"pub", "museum"}, suffixes=("_museum",))
        assert len(kept) == 3
        assert list(kept.columns) == ["Easting", "Northing", "name"]
        assert 529000 < kept["Easting"].iloc[0] < 530000  # Soho, in British National Grid

    def test_a_category_that_only_ends_alike_is_not_taken_by_name(self):
        assert places.located(overture("carpet_store"), {"pet_store"}).empty


class TestContext:
    def test_it_gives_the_places_of_some_categories(self, tmp_path):
        ctx = context(tmp_path, overture("pet_store", "pub"))
        assert len(ctx.places_of({"pet_store"})) == 1

    def test_the_walk_to_the_nearest_is_none_where_there_is_no_place(self, tmp_path):
        ctx = context(tmp_path, overture("pub"))
        assert ctx.walk_to_nearest(ctx.places_of({"vet"})) == [None, None]
        assert ctx.walk_to_nearest(ctx.places_of({"pub"})) == [7.0, 7.0]

    def test_the_count_within_a_walk_is_0_where_there_is_no_place(self, tmp_path):
        ctx = context(tmp_path, overture("pub", "pub", "bar"))
        assert ctx.count_within(ctx.places_of({"pub", "bar"}), 15) == [3, 3]
        assert ctx.count_within(ctx.places_of({"vet"}), 15) == [0, 0]
        assert ctx.network.asked == [15]  # type: ignore[attr-defined]


class TestTheFamilies:
    def test_vets_and_pet_shops_are_walks_to_the_nearest(self, tmp_path):
        ctx = context(tmp_path, overture("veterinarian", "pet_store", "aquatic_pet_store"))
        out = pets.columns(ctx)
        assert out == {"vets": [7.0, 7.0], "pet-shops": [7.0, 7.0]}

    def test_a_city_without_vets_has_no_walk_to_one(self, tmp_path):
        out = pets.columns(context(tmp_path, overture("pet_store")))
        assert out["vets"] == [None, None]

    def test_culture_counts_museums_of_any_kind_theatres_and_galleries_within_15_minutes(
        self, tmp_path
    ):
        found = overture("art_gallery", "history_museum", "theatre_venue", "pub", "pet_store")
        ctx = context(tmp_path, found)
        assert culture.columns(ctx)["cultural-venues-nearby"] == [3, 3]
        assert culture.CULTURE_MINUTES in ctx.network.asked  # type: ignore[attr-defined]

    def test_nightlife_counts_pubs_bars_and_clubs_within_10_minutes(self, tmp_path):
        found = overture("pub", "cocktail_bar", "dance_club", "art_gallery")
        ctx = context(tmp_path, found)
        assert culture.columns(ctx)["nightlife"] == [3, 3]
        assert culture.NIGHTLIFE_MINUTES in ctx.network.asked  # type: ignore[attr-defined]

    def test_community_spaces_are_a_walk_and_lgbtq_venues_a_count(self, tmp_path):
        found = overture("community_center", "gay_bar", "gay_and_lesbian_services_organization")
        ctx = context(tmp_path, found)
        out = community_life.columns(ctx)
        assert out["community-spaces"] == [7.0, 7.0]
        assert out["lgbtq-friendly-venues"] == [2, 2]
        assert ctx.network.asked == [community_life.LGBTQ_MINUTES]  # type: ignore[attr-defined]

    def test_coworking_counts_spaces_within_15_minutes(self, tmp_path):
        ctx = context(tmp_path, overture("coworking_space", "shared_office_space", "pub"))
        ctx.__dict__["workers"] = pd.Series(0.0, index=ctx.cells)
        assert work.columns(ctx)["coworking"] == [2, 2]


class TestJobDensity:
    def test_it_is_the_jobs_a_square_kilometre_over_a_cell_and_the_cells_around_it(self):
        ring = h3.grid_disk(CENTRE, 2)
        workers = pd.Series(100.0, index=ring)
        density = work.jobs_per_km2(workers, [CENTRE], steps=2)
        assert density[CENTRE] == pytest.approx(100.0 / h3.cell_area(CENTRE, "km^2"), rel=0.01)

    def test_a_cell_at_the_edge_counts_only_the_cells_the_region_has(self):
        workers = pd.Series({CENTRE: 100.0, NEIGHBOUR: 300.0})
        density = work.jobs_per_km2(workers, [CENTRE, NEIGHBOUR], steps=2)
        assert density[CENTRE] == pytest.approx(200.0 / h3.cell_area(CENTRE, "km^2"), rel=0.01)

    def test_a_cell_with_no_jobs_around_has_a_density_of_0(self):
        density = work.jobs_per_km2(pd.Series({CENTRE: 0.0}), [CENTRE], steps=2)
        assert density[CENTRE] == 0.0


def test_the_families_are_found_and_their_indicators_are_in_the_catalogue():
    assert {"pets", "culture", "community_life", "work"} <= {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    wanted = {"vets", "pet-shops", "cultural-venues-nearby", "nightlife", "community-spaces"}
    assert wanted | {"lgbtq-friendly-venues", "coworking", "job-density"} <= ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
