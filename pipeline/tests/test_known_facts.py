"""Facts about London that the built data must agree with.

These read the real bundle that `just data london` builds, so they are skipped where there is none,
as in CI. Run `just data london` and then `just check` to run them.
"""

import json

import h3
import pandas as pd
import pytest

from atlas.indicators.crime import CATEGORIES
from atlas.paths import data_dir

LONDON = data_dir() / "published" / "london"
pytestmark = pytest.mark.skipif(
    not (LONDON / "latest.json").exists(), reason="no built London bundle: run `just data london`"
)


def cell_at(lat: float, lng: float) -> str:
    return h3.latlng_to_cell(lat, lng, 9)


@pytest.fixture(scope="module")
def bundle() -> pd.DataFrame:
    version = json.loads((LONDON / "latest.json").read_text(encoding="utf-8"))["version"]
    return pd.read_parquet(LONDON / version / "cells.parquet").set_index("cell")


SOHO = cell_at(51.5136, -0.1337)
WIMBLEDON_VILLAGE = cell_at(51.4214, -0.2056)
BANK = cell_at(51.5133, -0.0890)


@pytest.mark.parametrize(
    "column",
    [
        "burglary",
        "violence_and_sexual_offences",
        "robbery_and_theft_from_the_person",
        "anti_social_behaviour",
    ],
)
def test_soho_has_more_crime_per_resident_than_wimbledon_village(bundle, column):
    assert bundle.loc[SOHO, column] > 3 * bundle.loc[WIMBLEDON_VILLAGE, column]


def test_every_cell_has_a_rate_for_each_crime_indicator(bundle):
    columns = [name.replace("-", "_") for name in CATEGORIES]
    assert len(columns) == 5
    assert bundle[columns].notna().all().all()


def test_rates_are_per_1000_residents_so_they_are_of_a_plausible_size(bundle):
    # London records about 1 burglary per 200 residents a year: a median near 5 per 1,000.
    assert 2 < bundle["burglary"].median() < 12
    assert 10 < bundle["violence_and_sexual_offences"].median() < 60


def test_the_city_of_london_tops_the_rates_because_of_its_workers_not_residents(bundle):
    """Spike S2's known limit: workers and visitors are in the counts, but not in the residents."""
    assert bundle.loc[BANK, "burglary"] > bundle["burglary"].quantile(0.99)


HACKNEY_MARSHES = cell_at(51.5530, -0.0290)  # the Lea valley floodplain
CRYSTAL_PALACE_HILL = cell_at(51.4190, -0.0750)


def test_flood_shares_are_percentages_of_the_area_and_mostly_zero(bundle):
    for column in ("river_and_sea_flooding", "surface_water_flooding"):
        assert bundle[column].notna().all()
        assert bundle[column].between(0, 100).all()
        assert bundle[column].median() == 0  # most of London is not at risk of 1 in 100


def test_the_lea_valley_floodplain_is_more_at_risk_from_rivers_than_a_hilltop(bundle):
    assert bundle.loc[HACKNEY_MARSHES, "river_and_sea_flooding"] > 20
    assert bundle.loc[CRYSTAL_PALACE_HILL, "river_and_sea_flooding"] == 0


CHINGFORD = cell_at(51.6330, -0.0100)


def test_every_cell_has_a_walk_to_a_station_and_the_centre_is_better_served(bundle):
    minutes = bundle["station_proximity"]
    assert minutes.notna().all()
    assert minutes.min() >= 0
    assert minutes.loc[BANK] < 6 < minutes.loc[CHINGFORD]
    assert minutes.loc[SOHO] < 8


def test_most_of_london_is_within_a_30_minute_walk_of_a_station(bundle):
    minutes = bundle["station_proximity"]
    assert 8 < minutes.median() < 25
    assert (minutes <= 30).mean() > 0.75


def test_primary_schools_are_nearer_than_secondary_schools_and_every_cell_has_both(bundle):
    primary, secondary = bundle["primary_schools"], bundle["secondary_schools"]
    assert primary.notna().all() and secondary.notna().all()
    assert primary.median() < secondary.median()  # there are far more primary schools
    assert 4 < primary.median() < 20
    assert 8 < secondary.median() < 30


def test_every_cell_has_a_walk_to_a_gp_practice_and_most_are_within_15_minutes(bundle):
    minutes = bundle["gp_walk"]
    assert minutes.notna().all()
    assert 5 < minutes.median() < 20
    assert (minutes <= 15).mean() > 0.5
    assert minutes[SOHO] < 5


def test_parks_are_near_in_the_middle_of_hyde_park_and_far_in_the_city(bundle):
    minutes = bundle["walk_to_green_space"]
    assert minutes.notna().all()
    assert minutes[cell_at(51.5073, -0.1657)] < 7  # Hyde Park
    assert minutes[BANK] > 10  # the City has only small gardens
    assert 4 < minutes.median() < 15


def test_the_air_is_dirtier_in_the_west_end_than_in_richmond_park(bundle):
    no2, pm25 = bundle["no2"], bundle["pm25"]
    assert no2.notna().all() and pm25.notna().all()
    richmond_park = cell_at(51.4440, -0.2740)
    assert no2[SOHO] > no2[richmond_park] + 5
    assert pm25[SOHO] > pm25[richmond_park]
    assert 10 < no2.median() < 35 and 5 < pm25.median() < 15  # µg/m³, as in 2022


def test_noise_is_loud_beside_main_roads_railways_and_under_the_flight_path(bundle):
    road, rail, aircraft = bundle["road_noise"], bundle["rail_noise"], bundle["aircraft_noise"]
    assert road.notna().all() and rail.notna().all() and aircraft.notna().all()
    assert road[cell_at(51.5232, -0.1560)] > 62  # Marylebone Road
    assert road[cell_at(51.4440, -0.2740)] < 45  # Richmond Park
    assert rail[cell_at(51.5033, -0.1145)] > 58  # Waterloo
    assert aircraft[cell_at(51.4850, -0.4150)] > 50  # under Heathrow's approach
    assert aircraft.median() == 40  # most of London is beyond the airports' maps


def test_central_london_is_near_everything_and_the_edge_is_not(bundle):
    names = ["groceries", "pharmacies", "gyms", "libraries"]
    assert bundle[names].notna().all().all()
    assert (bundle.loc[SOHO, names] < 6).all()
    richmond_park = cell_at(51.4440, -0.2740)
    assert (bundle.loc[richmond_park, names] > 15).all()
    assert (
        bundle["groceries"].median() < bundle["pharmacies"].median() < bundle["libraries"].median()
    )


def test_the_food_scene_is_dense_in_soho_and_thin_in_chingford(bundle):
    soho, chingford = bundle.loc[SOHO], bundle.loc[cell_at(51.6330, -0.0100)]
    for column in ("cafes", "restaurant_choice", "cuisine_variety"):
        assert bundle[column].notna().all()
        assert soho[column] > 10 * chingford[column] or soho[column] > 50
    assert soho["restaurant_choice"] > 500
    assert 70 < bundle["food_hygiene"].median() < 95  # the share rated 4 or 5, S8 found 87
    assert bundle["food_hygiene"].notna().mean() > 0.6  # cells with 5 or more rated businesses


def test_housing_costs_follow_the_borough(bundle):
    rent, tax = bundle["renting_cost"], bundle["council_tax"]
    assert tax.notna().all()
    assert rent.notna().mean() > 0.99  # only the City of London has no ONS rent
    wimbledon = cell_at(51.4214, -0.2056)
    assert rent[SOHO] > rent[wimbledon] + 500  # Westminster rents are the dearest
    assert tax[SOHO] < 1200 < tax[wimbledon]  # Westminster sets London's lowest Band D
    assert bundle["renting_cost"].nunique() <= 33 and tax.nunique() <= 33  # one value a borough


def test_most_london_homes_can_get_gigabit_and_5g(bundle):
    gigabit, five_g = bundle["gigabit_broadband"], bundle["5g_coverage"]
    assert gigabit.notna().all() and five_g.notna().all()
    assert gigabit.between(0, 100).all() and five_g.between(0, 100).all()
    assert 85 < gigabit.median() <= 100  # Ofcom reports about nine in ten homes
    assert five_g.median() > 85
    assert five_g.nunique() <= 33  # one value for each borough


def test_diversity_is_high_in_east_london_and_low_on_the_green_edge(bundle):
    diversity = bundle["diversity"]
    assert diversity.notna().all() and diversity.between(0, 1).all()
    east_ham, biggin_hill = cell_at(51.5390, 0.0550), cell_at(51.3080, 0.0330)
    assert diversity[east_ham] > 0.75  # Newham is among England's most mixed boroughs
    assert diversity[biggin_hill] < 0.4  # mostly one group


def test_a_gp_serves_a_few_thousand_patients_where_a_practice_is_within_a_walk(bundle):
    ratio = bundle["gp_list_size"]
    assert 0.55 < ratio.notna().mean() < 0.75  # where a practice is within 15 minutes with a GP
    assert 2000 < ratio.median() < 3000  # England's 5th to 95th percentile is 1,357 to 5,559
    assert ratio.quantile(0.05) > 1000 and ratio.quantile(0.95) < 6000
    assert ratio[SOHO] < 2500 < ratio[cell_at(51.5390, 0.0550)]  # East Ham is stretched


def test_lines_and_routes_are_many_in_the_centre_and_none_in_the_park(bundle):
    rail, bus = bundle["rail_lines_nearby"], bundle["bus_routes_nearby"]
    assert rail.notna().all() and bus.notna().all()
    assert rail[BANK] >= 10  # Tube, DLR, Elizabeth line and rail at Bank and Monument
    assert bus[SOHO] > 30 and rail[SOHO] >= 4
    richmond_park = cell_at(51.4440, -0.2750)
    assert rail[richmond_park] == 0 and bus[richmond_park] == 0
    assert rail.median() < 2 and 2 <= bus.median() <= 5


def test_faith_and_community_options_follow_where_people_and_places_are(bundle):
    southall, soho = cell_at(51.5113, -0.3784), SOHO
    east_ham = cell_at(51.5390, 0.0550)
    assert bundle["faith__sikh"][southall] < 10  # Southall's gurdwaras
    assert bundle["faith__sikh"][soho] > 30
    assert bundle["faith__hindu"][east_ham] < bundle["faith__hindu"].median()
    assert bundle["your_community__ethnic_indian"][southall] > 40  # % of residents
    assert bundle["your_community__ethnic_indian"][soho] < 5
    assert bundle["your_community__religion_muslim"][east_ham] > 30
    options = [c for c in bundle.columns if c.startswith("your_community__")]
    assert len(options) == 42 and "faith__multifaith" not in bundle.columns
    for kind in ("ethnic", "born", "age"):  # each table's groups cover nearly everyone
        shares = bundle[[c for c in options if c.startswith(f"your_community__{kind}_")]].sum(
            axis=1
        )
        assert shares.between(90, 100.1).all(), kind  # British Overseas births (< 8%) are left out
        assert shares.median() > 99.9, kind
    assert bundle["your_community__born_united_kingdom"][SOHO] < 50  # a city of newcomers
    assert bundle["your_community__born_united_kingdom"].median() > 55
    assert bundle["your_community__age_children_under_15"].median() > 12


def test_a_square_metre_costs_most_in_the_west_end_and_least_in_the_outer_east(bundle):
    price = bundle["buying_cost"]
    assert 0.75 < price.notna().mean() < 0.95  # cells with 20 or more sales around them
    assert 5000 < price.median() < 8000  # pounds a square metre
    assert price[SOHO] > 10000 and price[cell_at(51.5010, -0.1600)] > 15000  # Knightsbridge
    assert price[cell_at(51.5397, 0.0810)] < 6000  # Barking
    assert price[cell_at(51.3762, -0.0982)] < 6000  # Croydon
    assert (
        price[cell_at(51.4440, -0.2750)] != price[cell_at(51.4440, -0.2750)]
    )  # no sales in the park


def test_an_ae_department_is_a_few_kilometres_from_anywhere_in_london(bundle):
    km = bundle["ae_distance"]
    assert km.notna().all() and (km > 0).all()
    assert 2.5 < km.median() < 5.0 and km.max() < 20
    assert km[SOHO] < 2.0  # University College Hospital and St Thomas' are near
    assert km[cell_at(51.4214, -0.2056)] < 3.0  # Wimbledon village, St George's
    assert km[cell_at(51.3080, 0.0330)] > 5.0  # Biggin Hill, on the green edge


def test_nearly_all_of_londons_schools_meet_the_standard_but_not_everywhere(bundle):
    share = bundle["school_inspections"]
    assert 0.70 < share.notna().mean() < 0.95  # cells with 3 or more judged schools in reach
    assert share.dropna().between(0, 100).all()
    assert share.median() >= 95 and share.quantile(0.05) > 60
    assert share.min() < 80  # some neighbourhoods have no good school nearby


def test_the_fare_zone_follows_the_distance_from_the_centre(bundle):
    zone = bundle["travel_cost"]
    assert zone.notna().all() and set(zone) <= {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
    assert zone[SOHO] == "1" and zone[BANK] == "1"
    assert zone[WIMBLEDON_VILLAGE] == "3"  # Wimbledon station
    assert zone[cell_at(51.6330, -0.0100)] == "5"  # Chingford
    assert zone[cell_at(51.3762, -0.0982)] == "5"  # East Croydon
