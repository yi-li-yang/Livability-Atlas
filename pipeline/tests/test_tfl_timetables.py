"""Reading TfL's route sequences, timetables and National Rail journeys into rides."""

import pytest

from atlas.datasets.cities.london import tfl_timetables as t
from atlas.indicators.station_matrix import Ride


def interval(stop, minutes):
    return {"stopId": stop, "timeToArrival": minutes}


TIMETABLE = {
    "timetable": {
        "routes": [
            {
                "stationIntervals": [
                    {"id": "0", "intervals": [interval("B", 2.0), interval("C", 5.0)]},
                    {"id": "1", "intervals": [interval("B", 2.0), interval("D", 6.0)]},
                ],
                "schedules": [
                    {
                        "name": "Monday - Thursday",
                        "knownJourneys": [
                            {"hour": "6", "minute": "50"},
                            {"hour": "7", "minute": "0"},
                            {"hour": "8", "minute": "30"},
                            {"hour": "9", "minute": "59"},
                            {"hour": "10", "minute": "0"},
                        ],
                    },
                    {"name": "Saturday", "knownJourneys": [{"hour": "8", "minute": "0"}]},
                ],
            }
        ]
    }
}


def test_a_timetable_gives_the_rides_between_next_stops():
    assert t.timetable_rides(TIMETABLE, "red", "A") == [
        Ride("red", "A", "B", 2.0),
        Ride("red", "B", "C", 3.0),
        Ride("red", "A", "B", 2.0),
        Ride("red", "B", "D", 4.0),
    ]


def test_a_ride_of_no_minutes_counts_half_a_minute():
    answer = {
        "timetable": {"routes": [{"stationIntervals": [{"intervals": [interval("B", 0.0)]}]}]}
    }
    assert t.timetable_rides(answer, "red", "A") == [Ride("red", "A", "B", 0.5)]


def test_an_empty_or_missing_answer_gives_no_rides():
    assert t.timetable_rides(None, "red", "A") == []
    assert t.timetable_rides({"disambiguation": {}}, "red", "A") == []


def test_the_peak_departures_are_monday_to_thursday_from_seven_to_ten():
    assert t.peak_departures(TIMETABLE) == 3


def test_the_headway_is_the_peak_hours_over_the_trains_each_way():
    assert t.headway(72) == 180 / 36  # 36 trains each way in 3 hours: every 5 minutes
    assert t.headway(1000) == t.HEADWAY_LIMITS[0]
    assert t.headway(0) == t.HEADWAY_LIMITS[1]


def test_a_route_sequence_gives_each_routes_stops_in_order():
    sequence = {"orderedLineRoutes": [{"naptanIds": ["A", "B"]}, {"naptanIds": ["A", "C"]}]}
    assert t.route_stops(sequence) == [["A", "B"], ["A", "C"]]
    assert t.route_stops(None) == []


def test_next_stop_pairs_keep_only_the_stops_inside():
    routes = [["A", "B", "C", "X"], ["C", "B"]]
    assert t.next_stop_pairs(routes, {"A", "B", "C"}) == {("A", "B"), ("B", "C"), ("C", "B")}


def test_a_national_rail_ride_is_the_quickest_journey_of_one_train():
    answer = {
        "journeys": [
            {"legs": [{"duration": 9, "mode": {"id": "national-rail"}}]},
            {"legs": [{"duration": 7, "mode": {"id": "national-rail"}}]},
            {"legs": [{"duration": 3, "mode": {"id": "walking"}}]},
            {
                "legs": [
                    {"duration": 2, "mode": {"id": "national-rail"}},
                    {"duration": 2, "mode": {"id": "national-rail"}},
                ]
            },
        ]
    }
    assert t.rail_minutes(answer) == 7.0
    assert t.rail_minutes({"journeys": []}) is None
    assert t.rail_minutes(None) is None


def test_a_pair_without_minutes_is_timed_by_its_straight_line_at_the_modes_speed():
    where = {"A": (51.0, 0.0), "B": (51.01, 0.0)}  # 1,111.95 m apart
    rides = t.timed_rides("red", {("A", "B"), ("B", "A")}, {("A", "B"): 3.0}, where, 550.0)
    assert rides[0] == Ride("red", "A", "B", 3.0)
    assert rides[1].start == "B"
    assert abs(rides[1].minutes - 1111.9508023353292 / 550.0) < 1e-9


def test_the_weekday_schedule_is_monday_or_else_not_the_weekend():
    def answer(*names):
        schedules = [{"name": n, "knownJourneys": [{"hour": "8"}]} for n in names]
        return {"timetable": {"routes": [{"schedules": schedules}]}}

    assert t.peak_departures(answer("Saturday", "Mondays to Fridays")) == 1
    assert t.peak_departures(answer("Sunday", "Weekdays")) == 1
    assert t.peak_departures(answer("Sunday", "Saturdays and Public Holidays")) == 0


def test_a_line_with_no_weekday_departures_takes_its_modes_usual_headway():
    assert t.headway(0, 6.0) == 6.0


def test_a_fetch_whose_answers_are_mostly_empty_stops_and_says_to_move_the_day():
    t.check_answered(845, 85)  # about one pair in ten has no single train
    t.check_answered(4, 4)  # too few to tell
    with pytest.raises(RuntimeError, match="DATE"):
        t.check_answered(845, 845)
