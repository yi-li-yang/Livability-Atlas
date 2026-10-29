from pathlib import Path

import numpy as np
import pytest

from atlas.spatial import walking
from atlas.spatial.walking import SPEED, Network, is_walkable

# A street of six nodes 80 m apart, running east along y = 0, so each step is one minute on foot.
LINE = [(i, 80.0 * i, 0.0) for i in range(6)]


def street(*ways):
    return Network.from_ways(list(ways))


class TestWalkable:
    @pytest.mark.parametrize(
        "tags",
        [
            {"highway": "residential"},
            {"highway": "footway"},
            {"highway": "primary"},
            {"highway": "steps"},
            {"highway": "service", "access": "yes"},
            {"highway": "service", "access": "private", "foot": "yes"},
            {"highway": "path", "foot": "designated"},
        ],
    )
    def test_streets_and_paths_that_people_may_walk_are_walkable(self, tags):
        assert is_walkable(tags)

    @pytest.mark.parametrize(
        "tags",
        [
            {"highway": "motorway"},
            {"highway": "motorway_link"},
            {"highway": "proposed"},
            {"highway": "construction"},
            {"highway": "residential", "foot": "no"},
            {"highway": "service", "access": "private"},
            {"highway": "service", "access": "no"},
            {"highway": "corridor"},
            {"building": "yes"},
            {},
        ],
    )
    def test_what_is_closed_to_walkers_or_not_a_way_is_not(self, tags):
        assert not is_walkable(tags)


def test_the_speed_is_4_8_km_an_hour_which_is_80_metres_a_minute():
    assert SPEED == 80


class TestMinutes:
    def test_the_minutes_to_the_nearest_place_follow_the_street(self):
        net = street(LINE)
        minutes = net.minutes_to_nearest(
            places=np.array([[400.0, 0.0]]),  # the last node
            origins=np.array([[0.0, 0.0], [160.0, 0.0], [400.0, 0.0]]),
        )
        assert minutes == pytest.approx([5.0, 3.0, 0.0], abs=1e-6)

    def test_with_several_places_each_origin_takes_the_nearer(self):
        net = street(LINE)
        minutes = net.minutes_to_nearest(
            places=np.array([[0.0, 0.0], [400.0, 0.0]]),
            origins=np.array([[160.0, 0.0], [240.0, 0.0]]),
        )
        assert minutes == pytest.approx([2.0, 2.0])  # 160 m to the west end, 160 m to the east

    def test_a_walk_off_the_street_is_added_in_a_straight_line(self):
        net = street(LINE)
        # The place is 40 m off the end of the street, the origin 80 m off its start.
        minutes = net.minutes_to_nearest(
            places=np.array([[400.0, 40.0]]), origins=np.array([[0.0, 80.0]])
        )
        assert minutes == pytest.approx([(80 + 400 + 40) / SPEED])

    def test_the_route_goes_round_when_the_straight_way_is_closed(self):
        # A square, with one side missing: from (0, 0) to (0, 80) the walk is the long way round.
        ways = [
            [(0, 0.0, 0.0), (1, 80.0, 0.0), (2, 80.0, 80.0), (3, 0.0, 80.0)],
        ]
        minutes = street(*ways).minutes_to_nearest(
            places=np.array([[0.0, 80.0]]), origins=np.array([[0.0, 0.0]])
        )
        assert minutes == pytest.approx([3.0])  # 240 m, not the straight 80 m

    def test_ways_that_share_a_node_are_one_network(self):
        crossing = [(2, 160.0, 0.0), (20, 160.0, 80.0), (21, 160.0, 160.0)]
        minutes = street(LINE, crossing).minutes_to_nearest(
            places=np.array([[160.0, 160.0]]), origins=np.array([[0.0, 0.0]])
        )
        assert minutes == pytest.approx([(160 + 160) / SPEED])

    def test_a_doubled_street_counts_once(self):
        # The same two nodes joined by two ways must not add their lengths together.
        minutes = street(LINE, LINE).minutes_to_nearest(
            places=np.array([[400.0, 0.0]]), origins=np.array([[0.0, 0.0]])
        )
        assert minutes == pytest.approx([5.0])


OSM = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6" generator="test">
  <node id="1" lat="51.5000" lon="-0.1000"/>
  <node id="2" lat="51.5000" lon="-0.0990"/>
  <node id="3" lat="51.5000" lon="-0.0980"/>
  <node id="4" lat="51.5010" lon="-0.0980"/>
  <way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><tag k="highway" v="residential"/></way>
  <way id="11"><nd ref="3"/><nd ref="4"/><tag k="highway" v="footway"/></way>
  <way id="12"><nd ref="1"/><nd ref="4"/><tag k="highway" v="motorway"/></way>
  <way id="13"><nd ref="2"/><nd ref="4"/><tag k="building" v="yes"/></way>
</osm>
"""


def test_the_network_is_read_from_an_osm_file_keeping_only_walkable_ways(tmp_path: Path):
    path = tmp_path / "tiny.osm"
    path.write_text(OSM, encoding="utf-8")
    ways = walking.read_ways(path)
    assert ways.count == 2  # the motorway and the building are left out
    assert [ways.refs[ways.way == i].tolist() for i in range(2)] == [[1, 2, 3], [3, 4]]
    network = Network.from_ways(ways)
    assert len(network.refs) == 4
    # The walk from node 1 to node 4 is along the two walkable ways, not the motorway.
    here, there = network.xy[0], network.xy[3]
    minutes = network.minutes_to_nearest(places=there[None, :], origins=here[None, :])
    length = (
        np.hypot(*(network.xy[1] - network.xy[0]))
        + np.hypot(*(network.xy[2] - network.xy[1]))
        + np.hypot(*(network.xy[3] - network.xy[2]))
    )
    assert minutes[0] == pytest.approx(length / SPEED, rel=1e-6)


class TestSeparateFragments:
    """A small piece of street that joins nothing is no use for getting anywhere."""

    ISLAND = [(10, 0.0, 30.0), (11, 80.0, 30.0)]  # beside the start of the main street, cut off

    def test_a_walk_starts_from_the_main_network_not_from_a_nearer_fragment(self):
        net = street(LINE, self.ISLAND)
        minutes = net.minutes_to_nearest(
            places=np.array([[400.0, 0.0]]), origins=np.array([[0.0, 28.0]])
        )
        # The fragment is 2 m away and the main street 28 m, but only the main street goes anywhere.
        assert minutes == pytest.approx([(28 + 400) / SPEED])

    def test_a_place_on_a_fragment_is_taken_to_the_main_network(self):
        net = street(LINE, self.ISLAND)
        minutes = net.minutes_to_nearest(
            places=np.array([[40.0, 30.0]]), origins=np.array([[400.0, 0.0]])
        )
        assert np.isfinite(minutes[0])


class TestPlacesWithin:
    """`LINE` is a street from (0, 0) to (400, 0) with a node every 80 m."""

    def test_the_places_within_the_walk_are_found_by_following_the_street(self):
        net = street(LINE)
        places = np.array([[0.0, 0.0], [160.0, 0.0], [400.0, 0.0]])
        found = net.places_within(places, origins=np.array([[80.0, 0.0]]), minutes=2.0)
        assert found[0].tolist() == [0, 1]  # 80 m and 80 m away; the third is 320 m away

    def test_a_walk_of_exactly_the_limit_counts(self):
        net = street(LINE)
        found = net.places_within(np.array([[160.0, 0.0]]), np.array([[0.0, 0.0]]), minutes=2.0)
        assert found[0].tolist() == [0]

    def test_the_straight_stretch_off_the_street_counts_towards_the_limit(self):
        net = street(LINE)
        places = np.array([[160.0, 40.0]])  # 40 m off the street
        near = net.places_within(places, np.array([[0.0, 0.0]]), minutes=2.5)  # 200 m: 160 + 40
        far = net.places_within(places, np.array([[0.0, 0.0]]), minutes=2.4)  # 192 m
        assert near[0].tolist() == [0] and far[0].tolist() == []

    def test_a_place_close_in_a_straight_line_but_far_round_by_the_street_is_out_of_reach(self):
        # A U of street: 100 m across in a straight line, 580 m (7.25 minutes) round the U.
        u = [(0, 0.0, 0.0), (1, 240.0, 0.0), (2, 240.0, 100.0), (3, 0.0, 100.0)]
        net = street(u)
        place, origin = np.array([[0.0, 100.0]]), np.array([[0.0, 0.0]])
        assert net.places_within(place, origin, minutes=7.0)[0].tolist() == []
        assert net.places_within(place, origin, minutes=7.5)[0].tolist() == [0]

    def test_every_origin_gets_its_own_answer_and_origins_may_share_a_node(self):
        net = street(LINE)
        places = np.array([[0.0, 0.0], [400.0, 0.0]])
        origins = np.array([[10.0, 0.0], [20.0, 0.0], [390.0, 0.0]])
        found = net.places_within(places, origins, minutes=1.0)
        assert [f.tolist() for f in found] == [[0], [0], [1]]

    def test_several_groups_of_places_are_answered_together_as_they_would_be_apart(self):
        net = street(LINE)
        a = np.array([[0.0, 0.0], [160.0, 0.0]])
        b = np.array([[240.0, 0.0], [400.0, 0.0], [80.0, 30.0]])
        origins = np.array([[80.0, 0.0], [320.0, 0.0]])
        together = net.groups_within([a, b], origins, minutes=2.0)
        for group, places in enumerate((a, b)):
            apart = net.places_within(places, origins, minutes=2.0)
            assert [t.tolist() for t in together[group]] == [x.tolist() for x in apart]

    def test_the_straight_stretch_from_an_origin_off_the_street_counts_too(self):
        net = street(LINE)
        place = np.array([[160.0, 0.0]])
        origin = np.array([[0.0, 40.0]])  # 40 m off the street: 200 m in all
        assert net.places_within(place, origin, minutes=2.5)[0].tolist() == [0]
        assert net.places_within(place, origin, minutes=2.4)[0].tolist() == []
