"""Facts about London that the built data must agree with: the QA report's known-fact assertions
and relations (docs/methodology/validation.md).

A fact is a statement that anyone can check against a map or a news story, and it fails the build
when the data contradict it. A relation names two columns from independent datasets that should
rise and fall together. Thresholds come from the sources in the comments, or are set well short of
what the data show, so that only a broken input trips them.
"""

import numpy as np
from numpy.typing import NDArray

from atlas.qa.cells import Cells
from atlas.qa.facts import Facts, expect
from atlas.qa.format import number, share
from atlas.qa.relations import Relation

# Named places, as latitude and longitude. Each is the cell that contains the point.
PLACES = {
    "Soho": (51.5136, -0.1337),
    "Wimbledon village": (51.4214, -0.2056),
    "Bank": (51.5133, -0.0890),
    "Hackney Marshes": (51.5530, -0.0290),  # the Lea valley floodplain
    "Crystal Palace hill": (51.4190, -0.0750),
    "Chingford": (51.6330, -0.0100),
    "Hyde Park": (51.5073, -0.1657),
    "Richmond Park": (51.4440, -0.2740),
    "Richmond Park (west)": (51.4440, -0.2750),
    "Marylebone Road": (51.5232, -0.1560),
    "Waterloo": (51.5033, -0.1145),
    "Heathrow approach": (51.4850, -0.4150),
    "East Ham": (51.5390, 0.0550),
    "Biggin Hill": (51.3080, 0.0330),
    "Southall": (51.5113, -0.3784),
    "Knightsbridge": (51.5010, -0.1600),
    "Barking": (51.5397, 0.0810),
    "Croydon": (51.3762, -0.0982),
    "Canary Wharf": (51.5054, -0.0235),
    "Hampstead": (51.5560, -0.1780),
    "Brixton": (51.4613, -0.1156),
}

FACTS = Facts()

CRIMES = (
    "burglary",
    "violence_and_sexual_offences",
    "robbery_and_theft_from_the_person",
    "anti_social_behaviour",
)
ALL_CRIMES = (*CRIMES, "vehicle_crime")
FLOODS = ("river_and_sea_flooding", "surface_water_flooding")
NOISES = ("road_noise", "rail_noise", "aircraft_noise")
AMENITIES = ("groceries", "pharmacies", "gyms", "libraries")
FOOD = ("cafes", "restaurant_choice", "cuisine_variety")


def present(cells: Cells, column: str) -> NDArray[np.float64]:
    """The values of a column, without the cells that have none."""
    values = cells.numbers(column)
    return values[~np.isnan(values)]


def median(cells: Cells, column: str) -> float:
    return float(np.median(present(cells, column)))


def covered(cells: Cells, column: str) -> float:
    """The share of cells that have a value in a column."""
    return float(cells.valued(column).mean())


def distinct(cells: Cells, column: str) -> int:
    return len(np.unique(present(cells, column)))


def everywhere(cells: Cells, *columns: str) -> None:
    """Every cell has a value in each of these columns."""
    lacking = [c for c in columns if not cells.valued(c).all()]
    expect(not lacking, f"some cells have no value in {', '.join(lacking)}")


# --- Safety ---


@FACTS.add(
    "Soho has more than three times Wimbledon village's rate of each of four crimes", needs=CRIMES
)
def soho_crime(cells: Cells) -> str:
    ratios = {c: cells.at("Soho", c) / cells.at("Wimbledon village", c) for c in CRIMES}
    lowest = min(ratios, key=lambda c: ratios[c])
    expect(ratios[lowest] > 3, f"{lowest}: Soho's rate is only {ratios[lowest]:.1f} times")
    return f"Soho's rates are {min(ratios.values()):.1f} to {max(ratios.values()):.1f} times"


@FACTS.add("Every cell has a rate for each of the five crimes", needs=ALL_CRIMES)
def crime_everywhere(cells: Cells) -> str:
    everywhere(cells, *ALL_CRIMES)
    return f"{cells.count:,} cells"


@FACTS.add(
    "A year's burglaries are a few for every 1,000 residents, and violence a few tens",
    needs=("burglary", "violence_and_sexual_offences"),
)
def crime_scale(cells: Cells) -> str:
    # London records about 1 burglary for every 200 residents a year: a median near 5 per 1,000.
    burglary, violence = median(cells, "burglary"), median(cells, "violence_and_sexual_offences")
    expect(2 < burglary < 12, f"median burglary rate {burglary:.1f} per 1,000")
    expect(10 < violence < 60, f"median violence rate {violence:.1f} per 1,000")
    return f"medians {burglary:.1f} and {violence:.1f} per 1,000 residents"


@FACTS.add(
    "The City of London is among the highest for burglary, because its workers and visitors are "
    "counted and its few residents are not",
    needs=("burglary",),
)
def city_of_london_crime(cells: Cells) -> str:
    """Spike S2's known limit."""
    bank = cells.at("Bank", "burglary")
    top = float(np.quantile(present(cells, "burglary"), 0.99))
    expect(bank > top, f"Bank {bank:.1f} against {top:.1f} at the 99th percentile")
    return f"Bank {bank:.1f}, above the 99th percentile {top:.1f}"


# --- Natural hazards ---


@FACTS.add("Flood risk is a share of the area, and nil for most of London", needs=FLOODS)
def flood_shares(cells: Cells) -> str:
    everywhere(cells, *FLOODS)
    for column in FLOODS:
        values = present(cells, column)
        expect(bool(((values >= 0) & (values <= 100)).all()), f"{column} is outside 0 to 100")
        expect(float(np.median(values)) == 0, f"{column} has a median of {np.median(values):.1f}")
    return "every cell has both, from 0 to 100, with a median of 0"


@FACTS.add(
    "The Lea valley floodplain is at more risk from rivers than a hilltop",
    needs=("river_and_sea_flooding",),
)
def lea_valley(cells: Cells) -> str:
    marshes = cells.at("Hackney Marshes", "river_and_sea_flooding")
    hill = cells.at("Crystal Palace hill", "river_and_sea_flooding")
    expect(marshes > 20, f"Hackney Marshes {marshes:.0f}% of the area")
    expect(hill == 0, f"Crystal Palace hill {hill:.0f}% of the area")
    return f"Hackney Marshes {marshes:.0f}% of the area, Crystal Palace hill {hill:.0f}%"


# --- Transport ---


@FACTS.add(
    "Every cell has a walk to a station, and the centre is better served than the edge",
    needs=("station_proximity",),
)
def station_walk(cells: Cells) -> str:
    everywhere(cells, "station_proximity")
    walk = {p: cells.at(p, "station_proximity") for p in ("Bank", "Soho", "Chingford")}
    expect(float(present(cells, "station_proximity").min()) >= 0, "a walk is below zero")
    expect(walk["Bank"] < 6 < walk["Chingford"], f"walks {walk}")
    expect(walk["Soho"] < 8, f"Soho is {walk['Soho']:.1f} minutes from a station")
    return ", ".join(f"{p} {number(m)} minutes" for p, m in walk.items())


@FACTS.add("Most of London is within a 30-minute walk of a station", needs=("station_proximity",))
def station_walk_scale(cells: Cells) -> str:
    walks = present(cells, "station_proximity")
    middle, near = float(np.median(walks)), float((walks <= 30).mean())
    expect(8 < middle < 25, f"the median walk is {middle:.1f} minutes")
    expect(near > 0.75, f"{share(near)} of cells are within 30 minutes")
    return f"median {middle:.1f} minutes, {share(near)} within 30"


@FACTS.add(
    "Primary schools are nearer than secondary schools, and every cell has both",
    needs=("primary_schools", "secondary_schools"),
)
def school_walks(cells: Cells) -> str:
    everywhere(cells, "primary_schools", "secondary_schools")
    primary, secondary = median(cells, "primary_schools"), median(cells, "secondary_schools")
    expect(primary < secondary, "there are far more primary schools")
    expect(4 < primary < 20, f"median primary walk {primary:.1f} minutes")
    expect(8 < secondary < 30, f"median secondary walk {secondary:.1f} minutes")
    return f"median walks {primary:.1f} and {secondary:.1f} minutes"


@FACTS.add(
    "Every cell has a walk to a GP practice, and most are within 15 minutes",
    needs=("gp_walk",),
)
def gp_walk(cells: Cells) -> str:
    everywhere(cells, "gp_walk")
    walks = present(cells, "gp_walk")
    middle, near = float(np.median(walks)), float((walks <= 15).mean())
    expect(5 < middle < 20, f"the median walk is {middle:.1f} minutes")
    expect(near > 0.5, f"{share(near)} of cells are within 15 minutes")
    expect(cells.at("Soho", "gp_walk") < 5, "Soho is not within 5 minutes of a practice")
    return f"median {middle:.1f} minutes, {share(near)} within 15"


@FACTS.add(
    "Rail and bus services are many in the centre and none in the park",
    needs=("rail_lines_nearby", "bus_routes_nearby"),
)
def lines_and_routes(cells: Cells) -> str:
    everywhere(cells, "rail_lines_nearby", "bus_routes_nearby")
    rail, bus = "rail_lines_nearby", "bus_routes_nearby"
    expect(cells.at("Bank", rail) >= 10, f"Bank has {cells.at('Bank', rail):.0f} rail lines")
    expect(cells.at("Soho", bus) > 30, f"Soho has {cells.at('Soho', bus):.0f} bus routes")
    expect(cells.at("Soho", rail) >= 4, f"Soho has {cells.at('Soho', rail):.0f} rail lines")
    park = (cells.at("Richmond Park (west)", rail), cells.at("Richmond Park (west)", bus))
    expect(park == (0, 0), f"Richmond Park has {park[0]:.0f} rail lines and {park[1]:.0f} routes")
    expect(median(cells, rail) < 2, f"median rail lines {median(cells, rail):.0f}")
    expect(2 <= median(cells, bus) <= 5, f"median bus routes {median(cells, bus):.0f}")
    return (
        f"Bank {cells.at('Bank', rail):.0f} rail lines, Soho {cells.at('Soho', bus):.0f} routes, "
        "none in Richmond Park"
    )


@FACTS.add("The fare zone follows the distance from the centre", needs=("travel_cost",))
def fare_zones(cells: Cells) -> str:
    zones = cells.text("travel_cost")
    expect(all(z is not None for z in zones), "some cells have no fare zone")
    expect(set(zones) <= {str(n) for n in range(1, 10)}, f"zones {sorted(set(zones), key=str)}")
    expected = {
        "Soho": "1",
        "Bank": "1",
        "Wimbledon village": "3",  # Wimbledon station
        "Chingford": "5",
        "Croydon": "5",  # East Croydon
    }
    found = {place: cells.text_at(place, "travel_cost") for place in expected}
    expect(found == expected, f"zones {found}")
    return ", ".join(f"{p} {z}" for p, z in found.items())


@FACTS.add(
    "Travel to the four job centres is short in the centre and long at the edge",
    needs=("travel_time_to_places",),
)
def travel_time(cells: Cells) -> str:
    column = "travel_time_to_places"
    minutes = present(cells, column)
    reach = covered(cells, column)
    expect(0.85 < reach < 0.97, f"{share(reach)} of cells are within a 40-minute walk of a station")
    expect(55 < float(np.median(minutes)) < 72, f"the median is {np.median(minutes):.0f} minutes")
    expect(float(minutes.min()) > 15, f"the shortest is {minutes.min():.0f} minutes")
    at = {p: cells.at(p, column) for p in ("Bank", "Soho", "Canary Wharf", "East Ham", "Chingford")}
    expect(at["Bank"] < 30 and at["Soho"] < 35 and at["Canary Wharf"] < 35, f"centre {at}")
    expect(at["Chingford"] > 55, f"Chingford is {at['Chingford']:.0f} minutes")
    expect(at["East Ham"] < at["Chingford"], f"East Ham {at['East Ham']:.0f} minutes")
    return ", ".join(f"{p} {number(m)}" for p, m in at.items()) + " minutes"


# --- Environment ---


@FACTS.add(
    "The park is near in Hyde Park and far in the City",
    needs=("walk_to_green_space",),
)
def parks(cells: Cells) -> str:
    column = "walk_to_green_space"
    everywhere(cells, column)
    park, city, middle = (
        cells.at("Hyde Park", column),
        cells.at("Bank", column),
        median(cells, column),
    )
    expect(park < 7, f"Hyde Park is {park:.1f} minutes from a park")
    expect(city > 10, f"the City is {city:.1f} minutes from a park")  # only small gardens
    expect(4 < middle < 15, f"the median walk is {middle:.1f} minutes")
    return f"Hyde Park {park:.1f}, the City {city:.1f}, median {middle:.1f} minutes"


@FACTS.add("The air is dirtier in the West End than in Richmond Park", needs=("no2", "pm25"))
def air(cells: Cells) -> str:
    everywhere(cells, "no2", "pm25")
    no2 = cells.at("Soho", "no2"), cells.at("Richmond Park", "no2")
    pm25 = cells.at("Soho", "pm25"), cells.at("Richmond Park", "pm25")
    expect(no2[0] > no2[1] + 5, f"NO₂ in Soho {no2[0]:.1f}, in the park {no2[1]:.1f}")
    expect(pm25[0] > pm25[1], f"PM2.5 in Soho {pm25[0]:.1f}, in the park {pm25[1]:.1f}")
    # The 2022 model: µg/m³.
    expect(10 < median(cells, "no2") < 35, f"median NO₂ {median(cells, 'no2'):.1f}")
    expect(5 < median(cells, "pm25") < 15, f"median PM2.5 {median(cells, 'pm25'):.1f}")
    return (
        f"NO₂ {no2[0]:.1f} in Soho and {no2[1]:.1f} in the park; "
        f"PM2.5 {pm25[0]:.1f} and {pm25[1]:.1f}"
    )


@FACTS.add(
    "Noise is loud beside main roads and railways and under the flight path",
    needs=NOISES,
)
def noise(cells: Cells) -> str:
    everywhere(cells, *NOISES)
    road = cells.at("Marylebone Road", "road_noise")
    quiet = cells.at("Richmond Park", "road_noise")
    rail = cells.at("Waterloo", "rail_noise")
    air = cells.at("Heathrow approach", "aircraft_noise")
    expect(road > 62, f"Marylebone Road {road:.0f} dB")
    expect(quiet < 45, f"Richmond Park {quiet:.0f} dB")
    expect(rail > 58, f"Waterloo {rail:.0f} dB")
    expect(air > 50, f"under Heathrow's approach {air:.0f} dB")
    expect(median(cells, "aircraft_noise") == 40, "most of London is beyond the airports' maps")
    return f"Marylebone Road {road:.0f}, Waterloo {rail:.0f}, Heathrow approach {air:.0f} dB"


# --- Daily amenities ---


@FACTS.add(
    "Central London is near everything and the edge is not",
    needs=AMENITIES,
)
def near_everything(cells: Cells) -> str:
    everywhere(cells, *AMENITIES)
    soho = [cells.at("Soho", c) for c in AMENITIES]
    park = [cells.at("Richmond Park", c) for c in AMENITIES]
    expect(all(m < 6 for m in soho), f"Soho's walks are {soho}")
    expect(all(m > 15 for m in park), f"Richmond Park's walks are {park}")
    order = [median(cells, c) for c in ("groceries", "pharmacies", "libraries")]
    expect(order == sorted(order), f"median walks to groceries, pharmacies, libraries: {order}")
    return f"Soho within {max(soho):.1f} minutes of all four, Richmond Park beyond {min(park):.0f}"


@FACTS.add(
    "The food scene is dense in Soho and thin in Chingford, and most food businesses are "
    "rated 4 or 5",
    needs=(*FOOD, "food_hygiene"),
)
def food(cells: Cells) -> str:
    everywhere(cells, *FOOD)
    for column in FOOD:
        soho, chingford = cells.at("Soho", column), cells.at("Chingford", column)
        expect(
            soho > 10 * chingford or soho > 50,
            f"{column}: Soho {soho:.0f}, Chingford {chingford:.0f}",
        )
    expect(cells.at("Soho", "restaurant_choice") > 500, "Soho has fewer than 500 restaurants")
    rated = median(cells, "food_hygiene")
    expect(70 < rated < 95, f"the median share rated 4 or 5 is {rated:.0f}%")  # S8 found 87
    reach = covered(cells, "food_hygiene")
    expect(reach > 0.6, f"{share(reach)} of cells have 5 or more rated businesses")
    soho = cells.at("Soho", "restaurant_choice")
    return f"Soho has {soho:,.0f} restaurants; {rated:.0f}% of businesses are rated 4 or 5"


# --- Housing and cost ---


@FACTS.add("Rent and council tax follow the borough", needs=("renting_cost", "council_tax"))
def borough_costs(cells: Cells) -> str:
    everywhere(cells, "council_tax")
    reach = covered(cells, "renting_cost")
    expect(reach > 0.99, f"{share(reach)} of cells have a rent")  # the City has no ONS rent
    rent = {p: cells.at(p, "renting_cost") for p in ("Soho", "Wimbledon village")}
    tax = {p: cells.at(p, "council_tax") for p in ("Soho", "Wimbledon village")}
    expect(
        rent["Soho"] > rent["Wimbledon village"] + 500, f"rents {rent}"
    )  # Westminster is dearest
    expect(tax["Soho"] < 1200 < tax["Wimbledon village"], f"council tax {tax}")  # and taxes least
    expect(distinct(cells, "renting_cost") <= 33, "rent has more than one value for a borough")
    expect(
        distinct(cells, "council_tax") <= 33, "council tax has more than one value for a borough"
    )
    return (
        f"rent £{rent['Soho']:,.0f} in Soho, £{rent['Wimbledon village']:,.0f} in Wimbledon village"
    )


@FACTS.add(
    "A square metre costs most in the West End and least in the outer east",
    needs=("buying_cost",),
)
def price_per_square_metre(cells: Cells) -> str:
    column = "buying_cost"
    reach = covered(cells, column)
    expect(0.75 < reach < 0.95, f"{share(reach)} of cells have 20 or more sales around them")
    middle = median(cells, column)
    expect(5000 < middle < 8000, f"the median is £{middle:,.0f}")
    price = {p: cells.at(p, column) for p in ("Soho", "Knightsbridge", "Barking", "Croydon")}
    expect(price["Soho"] > 10000 and price["Knightsbridge"] > 15000, f"West End {price}")
    expect(price["Barking"] < 6000 and price["Croydon"] < 6000, f"outer east {price}")
    expect(bool(np.isnan(cells.at("Richmond Park (west)", column))), "the park has sales")
    return ", ".join(f"{p} £{v:,.0f}" for p, v in price.items()) + " a m²"


# --- Digital connectivity ---


@FACTS.add(
    "Most London homes can get gigabit broadband and 5G", needs=("gigabit_broadband", "5g_coverage")
)
def connectivity(cells: Cells) -> str:
    everywhere(cells, "gigabit_broadband", "5g_coverage")
    for column in ("gigabit_broadband", "5g_coverage"):
        values = present(cells, column)
        expect(bool(((values >= 0) & (values <= 100)).all()), f"{column} is outside 0 to 100")
    gigabit, five_g = median(cells, "gigabit_broadband"), median(cells, "5g_coverage")
    expect(
        85 < gigabit <= 100, f"median gigabit coverage {gigabit:.0f}%"
    )  # Ofcom: about nine in ten
    expect(five_g > 85, f"median 5G coverage {five_g:.0f}%")
    expect(distinct(cells, "5g_coverage") <= 33, "5G has more than one value for a borough")
    return f"medians {gigabit:.0f}% and {five_g:.0f}%"


# --- Health care ---


@FACTS.add(
    "A GP serves a few thousand patients where a practice is within a walk",
    needs=("gp_list_size",),
)
def patients_per_gp(cells: Cells) -> str:
    column = "gp_list_size"
    reach, middle = covered(cells, column), median(cells, column)
    values = present(cells, column)
    expect(0.55 < reach < 0.75, f"{share(reach)} of cells have a practice with a GP in reach")
    expect(2000 < middle < 3000, f"the median is {middle:,.0f} patients")  # England: 1,357 to 5,559
    low, high = float(np.quantile(values, 0.05)), float(np.quantile(values, 0.95))
    expect(low > 1000 and high < 6000, f"the 5th to 95th percentile is {low:,.0f} to {high:,.0f}")
    soho, east_ham = cells.at("Soho", column), cells.at("East Ham", column)
    expect(
        soho < 2500 < east_ham, f"Soho {soho:,.0f}, East Ham {east_ham:,.0f}"
    )  # East Ham is stretched
    return f"median {middle:,.0f}; Soho {soho:,.0f}, East Ham {east_ham:,.0f}"


@FACTS.add("An A&E department is a few kilometres from anywhere in London", needs=("ae_distance",))
def accident_and_emergency(cells: Cells) -> str:
    column = "ae_distance"
    everywhere(cells, column)
    km = present(cells, column)
    middle = float(np.median(km))
    expect(bool((km > 0).all()), "a department is at no distance")
    expect(2.5 < middle < 5.0, f"the median is {middle:.1f} km")
    expect(float(km.max()) < 20, f"the furthest is {km.max():.1f} km")
    expect(cells.at("Soho", column) < 2.0, f"Soho is {cells.at('Soho', column):.1f} km away")
    expect(cells.at("Wimbledon village", column) < 3.0, "Wimbledon village is 3 km or more away")
    expect(
        cells.at("Biggin Hill", column) > 5.0, "Biggin Hill is 5 km or less away"
    )  # the green edge
    soho, edge = cells.at("Soho", column), cells.at("Biggin Hill", column)
    return f"median {middle:.1f} km, Soho {soho:.1f}, Biggin Hill {edge:.1f}"


# --- Education ---


@FACTS.add(
    "Nearly all of London's schools meet the standard, but not everywhere",
    needs=("school_inspections",),
)
def school_inspections(cells: Cells) -> str:
    column = "school_inspections"
    reach, values = covered(cells, column), present(cells, column)
    expect(0.70 < reach < 0.95, f"{share(reach)} of cells have 3 or more judged schools in reach")
    expect(bool(((values >= 0) & (values <= 100)).all()), "a share is outside 0 to 100")
    middle, low = float(np.median(values)), float(np.quantile(values, 0.05))
    expect(middle >= 95 and low > 60, f"median {middle:.0f}%, 5th percentile {low:.0f}%")
    expect(float(values.min()) < 80, "every neighbourhood has a good school nearby")
    return f"median {middle:.0f}%, 5th percentile {low:.0f}%, lowest {values.min():.0f}%"


# --- Community and people ---


@FACTS.add(
    "Diversity is high in east London and low on the green edge",
    needs=("diversity",),
)
def diversity(cells: Cells) -> str:
    everywhere(cells, "diversity")
    values = present(cells, "diversity")
    expect(bool(((values >= 0) & (values <= 1)).all()), "an index is outside 0 to 1")
    east_ham, biggin_hill = cells.at("East Ham", "diversity"), cells.at("Biggin Hill", "diversity")
    expect(east_ham > 0.75, f"East Ham {east_ham:.2f}")  # Newham is among England's most mixed
    expect(biggin_hill < 0.4, f"Biggin Hill {biggin_hill:.2f}")  # mostly one group
    return f"East Ham {east_ham:.2f}, Biggin Hill {biggin_hill:.2f}"


@FACTS.add(
    "Faith and community options follow where people and places are",
    needs=(
        "faith__sikh",
        "faith__hindu",
        "your_community__ethnic_indian",
        "your_community__religion_muslim",
        "your_community__born_united_kingdom",
        "your_community__age_children_under_15",
    ),
)
def faith_and_community(cells: Cells) -> str:
    sikh, hindu = "faith__sikh", "faith__hindu"
    expect(
        cells.at("Southall", sikh) < 10,
        f"Southall is {cells.at('Southall', sikh):.0f} minutes from a gurdwara",
    )
    expect(
        cells.at("Soho", sikh) > 30, f"Soho is {cells.at('Soho', sikh):.0f} minutes from a gurdwara"
    )
    expect(cells.at("East Ham", hindu) < median(cells, hindu), "East Ham is far from a mandir")
    indian, muslim = "your_community__ethnic_indian", "your_community__religion_muslim"
    expect(
        cells.at("Southall", indian) > 40, f"Southall is {cells.at('Southall', indian):.0f}% Indian"
    )
    expect(cells.at("Soho", indian) < 5, f"Soho is {cells.at('Soho', indian):.0f}% Indian")
    expect(
        cells.at("East Ham", muslim) > 30, f"East Ham is {cells.at('East Ham', muslim):.0f}% Muslim"
    )
    options = [c for c in cells.columns if c.startswith("your_community__")]
    expect(len(options) == 42, f"{len(options)} options of Your community")
    faiths = {c.partition("__")[2] for c in cells.columns if c.startswith("faith__")}
    expect("multifaith" not in faiths, "multifaith is offered")
    for kind in ("ethnic", "born", "age"):  # each table's groups cover nearly everyone
        group = [c for c in options if c.startswith(f"your_community__{kind}_")]
        total = np.sum([cells.numbers(c) for c in group], axis=0)
        expect(
            bool(((total >= 90) & (total <= 100.1)).all()),
            f"the {kind} groups do not add up to 100%",
        )
        # British Overseas births (under 8%) are left out of the places of birth.
        expect(
            float(np.median(total)) > 99.9,
            f"the {kind} groups add up to {np.median(total):.1f}% at the median",
        )
    born = "your_community__born_united_kingdom"
    expect(
        cells.at("Soho", born) < 50, f"Soho is {cells.at('Soho', born):.0f}% born in the UK"
    )  # newcomers
    expect(
        median(cells, born) > 55, f"the median cell is {median(cells, born):.0f}% born in the UK"
    )
    expect(median(cells, "your_community__age_children_under_15") > 12, "few children")
    return "Southall is Indian and has a gurdwara; East Ham is Muslim; the groups add up to 100%"


# --- Neighbourhoods ---


@FACTS.add(
    "Every cell is in a named neighbourhood, and the names are the ones people use",
    needs=("neighbourhood",),
)
def neighbourhood_names(cells: Cells) -> str:
    listing = cells.manifest.neighbourhoods
    expect(listing is not None and 950 < len(listing) < 1100, "London has about a thousand MSOAs")
    expect(bool(cells.table["neighbourhood"].null_count == 0), "some cells have no neighbourhood")
    soho, hampstead = cells.neighbourhood_at("Soho"), cells.neighbourhood_at("Hampstead")
    canary, brixton = cells.neighbourhood_at("Canary Wharf"), cells.neighbourhood_at("Brixton")
    expect(soho is not None and "Soho" in soho[0], f"Soho is in {soho}")
    expect(
        hampstead is not None and hampstead[0] == "Hampstead Town", f"Hampstead is in {hampstead}"
    )
    expect(canary is not None and canary[0] == "Canary Wharf", f"Canary Wharf is in {canary}")
    expect(brixton is not None and brixton[1] == "Lambeth", f"Brixton is in {brixton}")
    return f"Soho is in {soho[0] if soho else None}, Brixton in {brixton[1] if brixton else None}"


# --- Relations ---

RELATIONS = [
    Relation(
        "station_proximity",
        "service_level",
        -1,
        0.5,
        "PTAL counts the stations within a walk, so a shorter walk goes with a higher band",
    ),
    Relation(
        "station_proximity",
        "rail_lines_nearby",
        -1,
        0.5,
        "the nearer a station, the more lines are within a walk",
    ),
    Relation(
        "service_level",
        "bus_routes_nearby",
        1,
        0.5,
        "PTAL counts bus services as well as trains",
    ),
    Relation(
        "no2",
        "road_noise",
        1,
        0.3,
        "the air model (LAEI) and the noise maps (Defra) both follow road traffic",
    ),
    Relation(
        "buying_cost",
        "renting_cost",
        1,
        0.4,
        "places that are dear to buy in are dear to rent in (Land Registry and EPC, against ONS)",
    ),
    Relation(
        "travel_time_to_places",
        "service_level",
        -1,
        0.4,
        "journey times (TfL's Journey Planner) are shorter where PTAL is high",
    ),
    Relation(
        "ae_distance",
        "travel_time_to_places",
        1,
        0.3,
        "hospitals and the four job centres are both in the centre",
    ),
    Relation(
        "cafes",
        "station_proximity",
        -1,
        0.4,
        "cafés (Overture and OpenStreetMap) cluster at stations",
    ),
    Relation(
        "gp_walk",
        "pharmacies",
        1,
        0.5,
        "practices (NHS) and pharmacies (Overture and OpenStreetMap) are both in town centres",
    ),
    Relation(
        "diversity",
        "your_community__born_united_kingdom",
        -1,
        0.6,
        "two census tables: the more mixed an area's ethnic groups, the fewer residents born here",
    ),
    Relation(
        "faith__muslim",
        "your_community__religion_muslim",
        -1,
        0.3,
        "mosques (OpenStreetMap) are near where the census finds Muslim residents",
    ),
    Relation(
        "faith__jewish",
        "your_community__religion_jewish",
        -1,
        0.3,
        "synagogues (OpenStreetMap) are near where the census finds Jewish residents",
    ),
]
