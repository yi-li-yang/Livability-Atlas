"""TfL's bus routes and timetables, read from the kept answers (spike S9)."""

import json

import pytest

from atlas.datasets.cities.london import tfl_api, tfl_buses
from atlas.scoring.travel import straight_metres

# Stops along longitude 0, about 500 m apart.
STEP = 500 / 111_195.08
WHERE = {stop: [51.5 + i * STEP, 0.0] for i, stop in enumerate(["O", "A", "B", "C"])}


def keep(root, lines, sequences, timetables):
    """Writes kept answers in the trimmed format that `tfl_buses` keeps."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "lines.json").write_text(json.dumps(lines), encoding="utf-8")
    for (line, direction), routes in sequences.items():
        path = root / "sequences" / f"{line}-{direction}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        stops = {s: WHERE[s] for route in routes for s in route if s in WHERE}
        path.write_text(json.dumps({"routes": routes, "stops": stops}), encoding="utf-8")
    for (line, origin), (intervals, peak) in timetables.items():
        path = root / "timetables" / f"{line}-{origin}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        answer = {"intervals": intervals, "peak": peak, "stops": {}}
        path.write_text(json.dumps(answer), encoding="utf-8")


def rides(routes: tfl_buses.BusRoutes) -> dict[tuple[str, str, str], float]:
    return {(r.line, r.start, r.end): r.minutes for r in routes.rides}


def test_a_ride_takes_the_difference_of_the_timetable_minutes(tmp_path):
    # The intervals start after the origin, so the first ride runs from the origin.
    keep(
        tmp_path,
        ["1"],
        {("1", "inbound"): [["O", "A", "B", "C"]]},
        {("1", "O"): ([[["A", 2.0], ["B", 2.0], ["C", 5.0]]], 6)},
    )
    got = rides(tfl_buses.read(tmp_path))
    assert got == {("1", "O", "A"): 2.0, ("1", "A", "B"): 0.0, ("1", "B", "C"): 3.0}


def test_minutes_that_go_down_give_a_ride_of_nothing(tmp_path):
    keep(
        tmp_path,
        ["1"],
        {("1", "inbound"): [["O", "A", "B"]]},
        {("1", "O"): ([[["A", 4.0], ["B", 3.0]]], 6)},
    )
    assert rides(tfl_buses.read(tmp_path))[("1", "A", "B")] == 0.0


def test_a_ride_that_no_timetable_times_takes_the_straight_line_at_bus_speed(tmp_path):
    keep(tmp_path, ["1"], {("1", "inbound"): [["O", "A"]]}, {("1", "O"): ([], 6)})
    metres = straight_metres(*WHERE["O"], *WHERE["A"])
    assert rides(tfl_buses.read(tmp_path))[("1", "O", "A")] == pytest.approx(metres / 250)
    assert metres / tfl_buses.BUS_SPEED == pytest.approx(2.0, abs=0.01)


def test_a_line_with_no_morning_departures_is_left_out(tmp_path):
    keep(
        tmp_path,
        ["1", "n1"],
        {("1", "inbound"): [["O", "A"]], ("n1", "inbound"): [["A", "B"]]},
        {("1", "O"): ([[["A", 2.0]]], 6), ("n1", "A"): ([[["B", 2.0]]], 0)},
    )
    routes = tfl_buses.read(tmp_path)
    assert set(routes.headways) == {"1"}
    assert {line for line, _, _ in rides(routes)} == {"1"}


def test_the_headway_comes_from_the_morning_departures_both_ways(tmp_path):
    # 18 departures each way from 07:00 to 10:00 is one every 10 minutes.
    keep(
        tmp_path,
        ["1"],
        {("1", "inbound"): [["O", "A"]], ("1", "outbound"): [["C", "B"]]},
        {("1", "O"): ([[["A", 2.0]]], 18), ("1", "C"): ([[["B", 2.0]]], 18)},
    )
    assert tfl_buses.read(tmp_path).headways == {"1": pytest.approx(10.0)}


def test_a_stop_with_no_position_is_left_out_with_its_untimed_rides(tmp_path):
    keep(tmp_path, ["1"], {("1", "inbound"): [["O", "A", "X"]]}, {("1", "O"): ([], 6)})
    routes = tfl_buses.read(tmp_path)
    assert "X" not in routes.stops
    assert set(rides(routes)) == {("1", "O", "A")}


def test_the_quickest_of_two_timetables_wins_for_a_ride(tmp_path):
    keep(
        tmp_path,
        ["1"],
        {("1", "inbound"): [["O", "A", "B"], ["C", "A", "B"]]},
        {
            ("1", "O"): ([[["A", 2.0], ["B", 5.0]]], 6),
            ("1", "C"): ([[["A", 1.0], ["B", 3.0]]], 6),
        },
    )
    assert rides(tfl_buses.read(tmp_path))[("1", "A", "B")] == 2.0


def test_the_stops_have_their_positions(tmp_path):
    keep(tmp_path, ["1"], {("1", "inbound"): [["O", "A"]]}, {("1", "O"): ([], 6)})
    assert tfl_buses.read(tmp_path).stops == {"O": (51.5, 0.0), "A": (51.5 + STEP, 0.0)}


def test_a_kept_answer_is_not_asked_again(tmp_path, monkeypatch):
    root = tmp_path / "raw" / "tfl" / "buses"
    keep(root, ["1"], {("1", "inbound"): [["O", "A"]]}, {("1", "O"): ([], 6)})
    (root / "sequences" / "1-outbound.json").write_text(
        json.dumps({"routes": [], "stops": {}}), encoding="utf-8"
    )

    def refuse(path: str, missing: bool = False):
        raise AssertionError(f"asked for {path}")

    monkeypatch.setattr(tfl_api, "get", refuse)
    assert set(rides(tfl_buses.fetch(tmp_path))) == {("1", "O", "A")}


def test_a_fetch_keeps_each_answer_trimmed(tmp_path, monkeypatch):
    answers = {
        "Line/Mode/bus": [{"id": "1"}],
        "Line/1/Route/Sequence/inbound": {
            "orderedLineRoutes": [{"naptanIds": ["O", "A"]}],
            "stopPointSequences": [
                {"stopPoint": [{"id": s, "lat": WHERE[s][0], "lon": 0.0} for s in ("O", "A")]}
            ],
        },
        "Line/1/Route/Sequence/outbound": None,
        "Line/1/Timetable/O": {
            "timetable": {
                "routes": [
                    {
                        "stationIntervals": [{"intervals": [{"stopId": "A", "timeToArrival": 3}]}],
                        "schedules": [
                            {
                                "name": "Monday to Friday",
                                "knownJourneys": [{"hour": "8", "minute": "0"}] * 4,
                            }
                        ],
                    }
                ]
            }
        },
    }
    asked = []

    def fake(path: str, missing: bool = False):
        asked.append(path)
        return answers[path]

    monkeypatch.setattr(tfl_api, "get", fake)
    monkeypatch.setattr(tfl_buses, "PAUSE", 0.0)
    routes = tfl_buses.fetch(tmp_path)
    assert rides(routes) == {("1", "O", "A"): 3.0}
    assert routes.headways == {"1": pytest.approx(min(180 / 2, 30.0))}
    kept = json.loads(
        (tmp_path / "raw" / "tfl" / "buses" / "timetables" / "1-O.json").read_text(encoding="utf-8")
    )
    assert kept["intervals"] == [[["A", 3.0]]] and kept["peak"] == 4
    assert len(asked) == 4
    tfl_buses.fetch(tmp_path)
    assert len(asked) == 4  # asked once


def test_the_headway_counts_each_direction_once(tmp_path):
    # A short working from M lists the buses that pass M from O too, so its count is not added:
    # each direction takes its busiest first stop, 24 one way and 18 the other, 21 on average.
    keep(
        tmp_path,
        ["1"],
        {("1", "inbound"): [["O", "A"], ["M", "A"]], ("1", "outbound"): [["C", "B"]]},
        {
            ("1", "O"): ([[["A", 2.0]]], 18),
            ("1", "M"): ([[["A", 1.0]]], 24),
            ("1", "C"): ([[["B", 2.0]]], 18),
        },
    )
    assert tfl_buses.read(tmp_path).headways == {"1": pytest.approx(180 / 21)}


def test_a_line_that_runs_one_way_counts_its_departures_once(tmp_path):
    keep(tmp_path, ["1"], {("1", "inbound"): [["O", "A"]]}, {("1", "O"): ([[["A", 2.0]]], 18)})
    assert tfl_buses.read(tmp_path).headways == {"1": pytest.approx(10.0)}


def test_an_answer_cut_short_is_asked_again(tmp_path, monkeypatch):
    root = tmp_path / "raw" / "tfl" / "buses"
    keep(root, ["1"], {("1", "inbound"): [["O", "A"]]}, {("1", "O"): ([], 6)})
    (root / "sequences" / "1-outbound.json").write_text('{"routes": [', encoding="utf-8")
    asked = []

    def fake(path: str, missing: bool = False):
        asked.append(path)
        return None

    monkeypatch.setattr(tfl_api, "get", fake)
    monkeypatch.setattr(tfl_buses, "PAUSE", 0.0)
    tfl_buses.fetch(tmp_path)
    assert asked == ["Line/1/Route/Sequence/outbound"]
    kept = json.loads((root / "sequences" / "1-outbound.json").read_text(encoding="utf-8"))
    assert kept == {"routes": [], "stops": {}}
    assert not list(root.rglob("*.part"))


def test_a_list_of_no_bus_lines_is_not_kept(tmp_path, monkeypatch):
    # TfL refusing the list once must not leave every later build without buses.
    monkeypatch.setattr(tfl_api, "get", lambda path, missing=False: None)
    monkeypatch.setattr(tfl_buses, "PAUSE", 0.0)
    with pytest.raises(RuntimeError, match="no bus lines"):
        tfl_buses.fetch(tmp_path)
    assert not (tmp_path / "raw" / "tfl" / "buses" / "lines.json").exists()


def test_an_answer_with_missing_fields_is_trimmed_without_them():
    sequence = {
        "orderedLineRoutes": [{"naptanIds": ["O", "A"]}, {"name": "no stops"}],
        "stopPointSequences": [{"stopPoint": [{"id": "O", "lat": 51.5, "lon": 0.0}, {"id": "X"}]}],
    }
    assert tfl_buses.trim_sequence(sequence) == {
        "routes": [["O", "A"]],
        "stops": {"O": [51.5, 0.0]},
    }
    timetable = {
        "timetable": {
            "routes": [
                {
                    "stationIntervals": [
                        {"id": "no intervals"},
                        {"intervals": [{"stopId": "A"}, {"stopId": "B", "timeToArrival": 4}]},
                    ]
                }
            ]
        }
    }
    trimmed = tfl_buses.trim_timetable(timetable)
    assert trimmed["intervals"] == [[], [["B", 4.0]]]
