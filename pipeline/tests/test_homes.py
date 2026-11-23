import h3

from atlas.indicators import homes

CENTRE = h3.latlng_to_cell(51.5133, -0.0886, 9)
NEXT = h3.grid_ring(CENTRE, 1)[0]
FAR = h3.grid_ring(CENTRE, 5)[0]


def test_each_cell_counts_the_homes_placed_in_it():
    placed = [CENTRE] * 12 + [NEXT] * 3 + [FAR]
    assert homes.count_by_cell(placed, [CENTRE, NEXT, h3.grid_ring(CENTRE, 2)[0]]) == [12, 3, 0]


def test_a_home_outside_the_cells_is_not_counted():
    assert homes.count_by_cell([FAR, FAR], [CENTRE]) == [0]


def test_a_cell_is_a_place_where_people_live_from_the_minimum_number_of_homes():
    assert not homes.lived_in(homes.MINIMUM_HOMES - 1)
    assert homes.lived_in(homes.MINIMUM_HOMES)
