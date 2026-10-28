import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.indicators import places

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
LNG, LAT = -0.1337, 51.5136


def overture(*rows: tuple) -> pd.DataFrame:
    """Overture places as (name, category, lng offset in m, lat offset in m)."""
    return pd.DataFrame(
        [
            {
                "id": str(i),
                "name": name,
                "category": category,
                "lng": LNG + dx / 70000,
                "lat": LAT + dy / 111000,
            }
            for i, (name, category, dx, dy) in enumerate(rows)
        ]
    )


def osm(*rows: tuple) -> pd.DataFrame:
    """OpenStreetMap places as (name, tag key, tag value, lng offset in m, lat offset in m)."""
    frame = pd.DataFrame(
        [
            {
                "lng": LNG + dx / 70000,
                "lat": LAT + dy / 111000,
                "name": name,
                "brand": None,
                "cuisine": None,
                "amenity": None,
                "shop": None,
                "leisure": None,
            }
            | {key: value}
            for name, key, value, dx, dy in rows
        ]
    )
    return frame


class TestKinds:
    @pytest.mark.parametrize(
        "category, kind",
        [
            ("supermarket", "grocery"),
            ("grocery_store", "grocery"),
            ("convenience_store", "grocery"),
            ("greengrocer", "grocery"),
            ("asian_grocery_store", "grocery"),
            ("pharmacy", "pharmacy"),
            ("drugstore", "pharmacy"),
            ("gym", "gym"),
            ("boxing_gym", "gym"),
            ("library", "library"),
            ("cafe", "cafe"),
            ("coffee_shop", "cafe"),
            ("tea_room", "cafe"),
            ("restaurant", "restaurant"),
            ("fast_food_restaurant", "restaurant"),
            ("indian_restaurant", "restaurant"),
        ],
    )
    def test_an_overture_category_is_a_kind_of_place(self, category, kind):
        found = places.pool(overture(("Name", category, 0, 0)), osm().iloc[0:0])
        assert list(found) == [kind]

    @pytest.mark.parametrize(
        "category",
        [
            "fitness_trainer",  # a person, not a place to walk to
            "yoga_studio",
            "sport_or_fitness_facility",  # courts and pools as much as gyms
            "internet_cafe",
            "coffee_and_tea_supplies",
            "bakery",
            "butcher_shop",
            "fitness_equipment_wholesaler",
            "library_science_school",
        ],
    )
    def test_other_categories_are_not_counted(self, category):
        assert places.pool(overture(("Name", category, 0, 0)), osm().iloc[0:0]) == {}

    @pytest.mark.parametrize(
        "key, value, kind",
        [
            ("shop", "supermarket", "grocery"),
            ("shop", "convenience", "grocery"),
            ("shop", "greengrocer", "grocery"),
            ("amenity", "pharmacy", "pharmacy"),
            ("leisure", "fitness_centre", "gym"),
            ("amenity", "library", "library"),
            ("amenity", "cafe", "cafe"),
            ("amenity", "restaurant", "restaurant"),
            ("amenity", "fast_food", "restaurant"),
        ],
    )
    def test_an_openstreetmap_tag_is_a_kind_of_place(self, key, value, kind):
        found = places.pool(overture().iloc[0:0], osm(("Name", key, value, 0, 0)))
        assert list(found) == [kind]


class TestPool:
    def test_a_place_both_sources_list_counts_once(self):
        found = places.pool(
            overture(("Soho Coffee", "cafe", 0, 0)),
            osm(("Soho Coffee Co", "amenity", "cafe", 20, 10)),
        )
        assert len(found["cafe"]) == 1

    def test_places_with_different_names_close_together_both_count(self):
        found = places.pool(
            overture(("Soho Coffee", "cafe", 0, 0)),
            osm(("Bean There", "amenity", "cafe", 20, 10)),
        )
        assert len(found["cafe"]) == 2

    def test_the_same_name_far_apart_counts_twice(self):
        found = places.pool(
            overture(("Soho Coffee", "cafe", 0, 0)),
            osm(("Soho Coffee", "amenity", "cafe", 400, 0)),
        )
        assert len(found["cafe"]) == 2

    def test_places_of_another_kind_do_not_hide_each_other(self):
        found = places.pool(
            overture(("Corner", "pharmacy", 0, 0)),
            osm(("Corner", "shop", "convenience", 5, 0)),
        )
        assert len(found["pharmacy"]) == 1 and len(found["grocery"]) == 1

    def test_places_are_in_metres_of_british_national_grid(self):
        found = places.pool(overture(("Soho Coffee", "cafe", 0, 0)), osm().iloc[0:0])
        x, y = TO_BNG.transform(LNG, LAT)
        assert found["cafe"][["Easting", "Northing"]].iloc[0].tolist() == pytest.approx(
            [x, y], abs=1.0
        )

    def test_a_place_without_a_name_is_kept_when_nothing_close_has_one(self):
        found = places.pool(
            overture((None, "cafe", 0, 0)), osm(("Bean", "amenity", "cafe", 500, 0))
        )
        assert len(found["cafe"]) == 2


class TestCuisine:
    def test_overtures_category_names_the_cuisine(self):
        found = places.pool(
            overture(
                ("A", "indian_restaurant", 0, 0),
                ("B", "thai_restaurant", 100, 0),
                ("C", "restaurant", 200, 0),
                ("D", "fast_food_restaurant", 300, 0),
            ),
            osm().iloc[0:0],
        )
        cuisine = found["restaurant"]["cuisine"]
        assert cuisine.iloc[:2].tolist() == ["indian", "thai"]
        assert cuisine.iloc[2:].isna().all()  # a cuisine that is not named is missing

    def test_openstreetmaps_tag_fills_the_gap_and_the_first_cuisine_counts(self):
        row = osm(("Pad", "amenity", "restaurant", 0, 0))
        row["cuisine"] = "Thai; noodle"
        found = places.pool(overture().iloc[0:0], row)
        assert found["restaurant"]["cuisine"].tolist() == ["thai"]

    def test_a_pooled_place_keeps_overtures_cuisine_and_borrows_openstreetmaps_if_it_has_none(self):
        row = osm(("Pad Thai House", "amenity", "restaurant", 10, 0))
        row["cuisine"] = "thai"
        found = places.pool(overture(("Pad Thai House", "restaurant", 0, 0)), row)
        assert found["restaurant"]["cuisine"].tolist() == ["thai"]
        assert np.size(found["restaurant"]) > 0
