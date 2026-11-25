import numpy as np
import pytest

from atlas.indicators.reach import within_minutes
from atlas.indicators.station_matrix import UNREACHABLE

# Four cells on a line (metres east of the first), two stations. Walking is 80 m a minute with a
# street factor of 1, so a straight 800 m is 10 minutes on foot.
SPEED = 80.0
X = np.array([0.0, 400.0, 20_000.0, 40_000.0])
Y = np.zeros(4)


def matrix(minutes: int) -> np.ndarray:
    m = np.array([[0, minutes], [UNREACHABLE, 0]], dtype=np.uint16)
    return m


def run(values, links, ride: int, *, minutes: float = 45, reach: float = 40) -> np.ndarray:
    return within_minutes(
        np.asarray(values, dtype=np.float64),
        X,
        Y,
        np.asarray(links, dtype=np.float64).reshape(-1, 3),
        matrix(ride),
        minutes=minutes,
        reach_minutes=reach,
        walk_metres_a_minute=SPEED,
        street_factor=1.0,
        chunk=3,
    )


def test_a_cell_counts_itself_and_what_is_within_a_walk() -> None:
    # No stations: cells 0 and 1 are 5 minutes apart on foot; the others are hours away.
    out = run([1, 10, 100, 1000], [], ride=10)
    assert out.tolist() == [11, 11, 100, 1000]


def test_a_ride_reaches_a_far_cell_within_the_time() -> None:
    # Cell 0 walks 5 minutes to station 0, rides 20 to station 1, and walks 10 to cell 2: 35.
    links = [(0, 0, 5), (2, 1, 10)]
    out = run([1, 10, 100, 1000], links, ride=20)
    assert out[0] == 1 + 10 + 100
    # The matrix is one way here: station 1 cannot reach station 0, so cell 2 reaches no one.
    assert out[2] == 100


def test_a_journey_over_the_time_does_not_count() -> None:
    links = [(0, 0, 5), (2, 1, 10)]
    out = run([1, 10, 100, 1000], links, ride=31)  # 5 + 31 + 10 = 46 minutes
    assert out[0] == 11


def test_an_unreachable_ride_and_a_missing_value_count_nothing() -> None:
    links = [(0, 0, 5), (2, 1, 10)]
    m = run([1, np.nan, 100, 1000], links, ride=UNREACHABLE)
    assert m.tolist() == [1, 1, 100, 1000]


def test_the_walk_beyond_reach_does_not_count_on_its_own() -> None:
    # Cells 0 and 1 are 5 minutes apart; with a reach of 4 minutes neither walks to the other.
    out = run([1, 10, 100, 1000], [], ride=10, reach=4)
    assert out.tolist() == [1, 10, 100, 1000]


def test_the_result_does_not_depend_on_the_chunk() -> None:
    links = [(0, 0, 5), (1, 0, 3), (2, 1, 10), (3, 1, 2)]
    values = np.array([1.0, 10, 100, 1000])
    args = (values, X, Y, np.array(links, dtype=np.float64), matrix(20))
    kw = dict(minutes=45, reach_minutes=40, walk_metres_a_minute=SPEED, street_factor=1.0)
    a = within_minutes(*args, **kw, chunk=1)
    b = within_minutes(*args, **kw, chunk=4)
    assert a.tolist() == b.tolist() == [1111, 1111, 1100, 1100]


def test_links_must_name_known_cells_and_stations() -> None:
    with pytest.raises(ValueError, match="station"):
        run([1, 10, 100, 1000], [(0, 5, 1)], ride=10)
