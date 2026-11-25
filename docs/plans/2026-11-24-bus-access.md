# Buses to and from the stations: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The travel estimate takes a bus to and from the stations where that is quicker than the walk, for the default places and for a user's own places.

**Architecture:** A new dataset module reads TfL's bus routes and timetables. A new indicator module turns them into each cell's minutes to each station, on foot or on foot and by bus. `_travel` in `build.py` computes those minutes once and gives them to both the default places (`transport.travel_minutes`) and the cell-station links (`station_matrix.cell_stations`), whose file keeps its shape. In the browser, and in its Python reference, the last leg from a station to a place is the quicker of the straight-line walk and the links of the place's own cell, read backwards.

**Tech stack:** Python 3.13 (numpy, scipy `csgraph.dijkstra`, pandas, h3), TypeScript (Vitest, h3-js).

**Spec:** [spike S9](../spikes/S9-buses.md), its "What was done" and "Decisions".

## Global constraints

- The constants of S9: a walk to a stop of at most 10 minutes; a walk from a stop to a station of at most 6 minutes (straight line × 1.33 at 80 m a minute); boarding a bus costs half the line's headway plus 0.5 minutes; getting off costs nothing; a ride that no timetable times takes the straight line at 250 m a minute; the way to a station is at most 40 minutes; each cell keeps its 8 quickest stations.
- A bus line with no weekday departures from 07:00 to 10:00 is left out. The headway of the others comes from those departures, counted both ways, with `tfl_timetables.headway` (limits 1.5 to 30 minutes).
- The bus answers stay in S9's trimmed format under `data/raw/tfl/buses/` (`lines.json`, `sequences/{line}-{direction}.json`, `timetables/{line}-{origin}.json`), so the 2,710 answers that S9 kept are used and not asked again.
- The bundle stays deterministic: building twice gives the same version.
- A user's places stay in the browser (D08).
- British English in docs and text; Conventional Commits; no dates or durations in plans.

## Review focus

1. A user's place outside the region's cells (a postcode just over the boundary) keeps the straight-line walk and gives no error. Task 4 tests it.
2. A bundle built before this change has links on foot only. The browser's new last leg reads them as walks from the place's cell, which is still right, so no format change and no version check. Task 4 tests the region estimate on links on foot.
3. A timetable whose minutes go down from one stop to the next gives a ride of 0 minutes, never a negative one. Task 1 tests it.
4. A bus stop that no answer places (no latitude and longitude) is left out of the walks, and its untimed rides with it, with no error. Task 1 tests it.
5. A cell inside the place's own cell: the direct walk wins, as now. The golden case `walk-is-quicker` already covers it.

---

### Task 1: The bus data

**Files:**
- Create: `pipeline/src/atlas/datasets/cities/london/tfl_buses.py`
- Create: `pipeline/tests/test_tfl_buses.py`
- Modify: `catalogue/datasets.yaml` (one more line in `tfl-unified-api`'s `tells`: "The bus routes: each route's stops in order, the minutes between them and the weekday-morning departures")

**Interfaces:**
- Consumes: `tfl_api.get(path, missing=True)`; `tfl_timetables.PEAK`, `tfl_timetables.DIRECTIONS`, `tfl_timetables._weekday`, `tfl_timetables.headway`; `station_matrix.Ride`; `scoring.travel.straight_metres`.
- Produces:
  - `BUS_SPEED = 250.0`, `BUS_HEADWAY = 12.0` (a fallback for `headway`, never reached since lines with no departures are left out).
  - `trim_sequence(answer: Any) -> dict[str, Any]` and `trim_timetable(answer: Any) -> dict[str, Any]`, moved from the spike unchanged.
  - `@dataclass(frozen=True) class BusRoutes: stops: dict[str, tuple[float, float]]` (latitude, longitude), `rides: list[Ride]`, `headways: dict[str, float]`.
  - `fetch(data_dir: Path) -> BusRoutes`: fetches what is not kept (one request at a time, 0.4 s apart), then reads the kept answers.
  - `read(root: Path) -> BusRoutes`: the kept answers alone, so tests need no network.

- [ ] **Step 1: Write the failing tests** in `pipeline/tests/test_tfl_buses.py`, writing kept answers in S9's format into `tmp_path`:
  - `test_a_ride_takes_the_difference_of_the_timetable_minutes`: route `O, A, B, C`; timetable from `O` with intervals `[[A, 2], [B, 2], [C, 5]]` gives rides `O→A 2`, `A→B 0`, `B→C 3`. The first ride starts at the origin, which the intervals do not list.
  - `test_minutes_that_go_down_give_a_ride_of_nothing`: intervals `[[A, 4], [B, 3]]` give `A→B 0`.
  - `test_a_ride_that_no_timetable_times_takes_the_straight_line_at_bus_speed`: two stops 500 m apart and no timetable give 2.0 minutes (±0.01).
  - `test_a_line_with_no_morning_departures_is_left_out`: `peak` 0 in each of its timetables, so its rides and headway are absent.
  - `test_the_headway_comes_from_the_morning_departures_both_ways`: `peak` 18 on each of two timetables gives 10.0 minutes.
  - `test_a_stop_with_no_position_is_left_out_with_its_untimed_rides`.
  - `test_the_quickest_of_two_timetables_wins_for_a_ride`.
  - `test_a_kept_answer_is_not_asked_again`: with every answer kept, `fetch` makes no request (monkeypatch `tfl_api.get` to fail).
- [ ] **Step 2: Run them and see them fail.** `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest tests/test_tfl_buses.py -q` from `pipeline/`. Expected: import error.
- [ ] **Step 3: Write `tfl_buses.py`** from the spike's `fetch` and `bus_network`, with the one fix above (each interval list starts at the route's origin) and the module docstring of a dataset module (what TfL gives, the fallback speed, the lines left out, why the answers are kept trimmed: about 12 MB, against several hundred for whole answers).
- [ ] **Step 4: Run the tests and see them pass.** Then run the whole module on the kept answers: `read(data_dir()/"raw"/"tfl"/"buses")` gives 605 lines and about 45,700 rides (S9's counts; a few more rides timed is expected from the fix).
- [ ] **Step 5: Commit.** `feat: read TfL's bus routes and timetables`

### Task 2: Each cell's minutes to each station, by foot or bus

**Files:**
- Create: `pipeline/src/atlas/indicators/station_access.py`
- Create: `pipeline/tests/test_station_access.py`

**Interfaces:**
- Consumes: `BusRoutes` (Task 1); `Network.times_within(places, origins, minutes)`; `cell_centres_bng`; `station_matrix.STREET_FACTOR`, `WALK_METRES_A_MINUTE`, `Ride`.
- Produces:
  - `Access = list[tuple[np.ndarray, np.ndarray]]`: for each cell, the station positions within reach and the minutes to each, the shape `times_within` gives.
  - `STOP_WALK = 10.0`, `TO_STATION = 6.0`, `BOARD_MINUTES = 0.5`, `REACH = 40.0`.
  - `bus_to_station(stops: pd.DataFrame, rides: Iterable[Ride], headways: Mapping[str, float], stations: pd.DataFrame, *, reach: float = REACH) -> np.ndarray`: `stops` and `stations` have `stop`, `Easting`, `Northing`; the result is float32, stations by stops, `inf` beyond `reach`. Build the graph of S9 (stop, stop-and-line and station nodes; edge costs as in the global constraints) and search back from each station in chunks of 100 with `dijkstra(..., limit=reach)` on the transposed graph.
  - `cell_access(network: Network, stations: pd.DataFrame, cells: list[str], *, walk: float = REACH, buses: tuple[pd.DataFrame, np.ndarray] | None = None) -> Access`: the street walk within `walk`; with `buses` (the stops and `bus_to_station`'s array), each station's time is the quicker of the walk and the walk to a stop within `STOP_WALK` plus the stop's time; times over `walk` are dropped. Stations in ascending position.

- [ ] **Step 1: Write the failing tests** on small graphs in metres (stations and stops on one street, as `test_station_matrix.py` builds them):
  - `test_a_stop_reaches_a_station_by_bus`: stop `P`, line `L` rides `P→Q` in 5 minutes with headway 10, station `S` 80 m from `Q`: 5 + 0.5 + 5 + 1.33 = 11.83 (±0.01).
  - `test_a_bus_runs_only_the_way_its_timetable_gives`: `Q` does not reach `S2` behind `P`.
  - `test_a_change_of_line_at_a_stop_waits_again`.
  - `test_a_stop_farther_than_six_minutes_from_any_station_reaches_none_on_foot`.
  - `test_a_way_longer_than_the_reach_is_dropped`.
  - `test_without_buses_the_access_is_the_walk`: equals `network.times_within` for the same stations.
  - `test_a_cell_takes_the_bus_where_it_is_quicker`, and `test_a_cell_keeps_the_walk_where_it_is_quicker`.
  - `test_a_stop_beyond_the_stop_walk_is_not_used`.
- [ ] **Step 2: Run them and see them fail.**
- [ ] **Step 3: Write `station_access.py`.** Its docstring says what S9 measured and that the times are an estimate (a mean wait of half the headway).
- [ ] **Step 4: Run them and see them pass.**
- [ ] **Step 5: Commit.** `feat: give each cell its minutes to the stations by foot or bus`

### Task 3: The build uses the new minutes

**Files:**
- Modify: `pipeline/src/atlas/indicators/station_matrix.py` (`cell_stations`)
- Modify: `pipeline/src/atlas/indicators/transport.py` (`travel_minutes`)
- Modify: `pipeline/src/atlas/build.py` (`_travel` and its docstring)
- Modify: `pipeline/tests/test_station_matrix.py`, `pipeline/tests/test_journeys.py`

**Interfaces:**
- Consumes: `Access`, `cell_access`, `bus_to_station` (Task 2); `tfl_buses.fetch` (Task 1).
- Produces: `cell_stations(access: Access, *, keep: int = 8) -> list[tuple[int, int, float]]` and `travel_minutes(access: Access, stations: pd.DataFrame, times: pd.DataFrame, cells: list[str]) -> pd.Series`. Both lose the network and the walk limit, which `cell_access` now holds.

- [ ] **Step 1: Change the tests first.** The existing tests build their access with `cell_access(network, stations, cells, walk=…)` and keep their numbers. Add `test_a_quicker_way_by_bus_counts_for_the_places` in `test_journeys.py`: an access whose bus time to the far station is quicker changes the mean as expected.
- [ ] **Step 2: Run them and see them fail** (wrong signatures).
- [ ] **Step 3: Change the two functions and `_travel`.** `_travel` reads `tfl_buses.fetch(data_dir)`, places the stops in British National Grid (as `transport.place_stops` does), computes `bus_to_station` and `cell_access` once, and passes the access to both. The walk is computed once instead of twice.
- [ ] **Step 4: Run the whole pipeline suite, ruff and pyright** (the venv commands in `tooling-on-this-machine`). Expected: all pass.
- [ ] **Step 5: Commit.** `feat: the travel times take a bus to the station where it is quicker`

### Task 4: The far end of a user's journey

**Files:**
- Create: `shared/fixtures/travel/bus-at-the-far-end.json`, `shared/fixtures/travel/walk-at-the-far-end-when-quicker.json`
- Modify: `shared/fixtures/travel/README.md` (the place may carry the links of its own cell)
- Modify: `pipeline/src/atlas/scoring/travel.py`, `pipeline/tests/test_travel_estimate.py`
- Modify: `pipeline/src/atlas/datasets/cities/london/facts.py` (`_travel_estimates`), `pipeline/src/atlas/travel_check.py` (`check`)
- Modify: `web/src/travel/estimate.ts`, `web/src/travel/estimate.test.ts`, `web/src/travel/load.ts`, `web/src/features/places/withPlaces.test.ts`

**Interfaces:**
- Produces:
  - Golden case format: `place` may have `stations: [[station, minutes], …]`, the links of the place's cell.
  - Python: `region_minutes(stations, matrix, links, centres, place, constants, place_cell: int | None = None)`. The last leg from station `q` is the quicker of the straight-line walk (within reach) and the minutes of the link of `place_cell` to `q`.
  - TypeScript: `TravelData.cellOf: (place: Point) => number`, the position of the cell that holds the place, or −1. `placeMinutes(data, place)` uses it for the same last leg. `loadTravel` builds `cellOf` with `latLngToCell` at the resolution of the bundle's cells and a map from cell to position.

- [ ] **Step 1: Write the two golden cases**, all points on longitude 0, constants as in the other cases, expected numbers worked in their descriptions:
  - `bus-at-the-far-end`: stations `[51.501, 0]` and `[51.7, 0]`, matrix `[[0, 25], [25, 0]]`, cell `51.5, 0` with links `[[0, 4.0]]`, place `51.75, 0` with links `[[1, 12.5]]`. No station is within a 40-minute walk of the place (the nearer is 92.43 minutes), so the way is 4 + 25 + 12.5 = **41.5**. Without the place's links there would be none.
  - `walk-at-the-far-end-when-quicker`: stations `[51.501, 0]` and `[51.6, 0]`, matrix `[[0, 30], [30, 0]]`, cell `51.5, 0` with links `[[0, 4.0]]`, place `51.601, 0` with links `[[1, 3.0]]`. The walk from the second station is 1.848618208877666 minutes, quicker than its link of 3.0, so the way is **35.84861820887767**.
- [ ] **Step 2: Write the failing tests.** Python: the golden-case tests pass `place_cell` for a region of two cells (the case's cell, and the place's cell with its links). Add `test_links_on_foot_still_give_the_walk_at_the_far_end`. TypeScript: the same for `placeMinutes`, `estimateCase` and the region test; add `a place outside the region's cells keeps the straight walk` (`cellOf` returns −1) and a `loadTravel` test that `cellOf` finds a point's cell and gives −1 far away.
- [ ] **Step 3: Run them and see them fail** (pytest from `pipeline/`; Vitest from PowerShell in `E:\GitHub\Livability-Atlas\web`).
- [ ] **Step 4: Change the Python reference and the TypeScript estimate**, and pass the place's cell in `_travel_estimates` (the cell of each default place, by `h3.latlng_to_cell` at the cells' resolution) and in `travel_check.check` (the destination cell `b` itself).
- [ ] **Step 5: Run every check.** Pipeline: pytest, ruff, pyright. Web: `npm run lint`, `npm run types`, `npm test`, `npm run build`, `npx playwright test`. Expected: all pass.
- [ ] **Step 6: Commit.** `feat: a user's place is reached by bus from the station where that is quicker`

### Task 5: Build, check and document

**Files:**
- Modify: `catalogue/factors.yaml` (`travel-time-to-places`: the method, and the spread in `curve_reason` from the new build)
- Modify: `docs/decisions.md` (D10: the choice, the known limits, a history line), `docs/spikes/S4-routing.md` (a note that S9 added buses), `docs/codemap.md` (the two new modules), `docs/progress.md`, `docs/backlog.md` (buses shipped)
- Generated: the factor explorer's copy (`just docs`, or its npm script)

- [ ] **Step 1: Build London** from `pipeline/`: `PYTHONUTF8=1 ./.venv/Scripts/atlas.exe build london`. Expected: QA with 0 failed; the travel known fact holds (between 85% and 97% of cells with a value, a median of 55 to 72 minutes); the station-matrix fact holds (rank correlation over 0.85, median ratio between 0.85 and 1.15). Build again and see the same version.
- [ ] **Step 2: Run the travel check** on the new bundle: `PYTHONUTF8=1 ./.venv/Scripts/atlas.exe travel-check london`. It reads the kept answers. Expected: a median error near S9's +5.5 minutes at 08:30, and within 20% near 85%. A gap of more than a minute from S9 needs an explanation before going on.
- [ ] **Step 3: Look at the map.** Run the dev server on the new bundle, add a place in outer London by postcode, and check with a Playwright script (Chromium with `--use-angle=d3d11`, closed at the end) that the map draws, the times change, and the page logs no errors.
- [ ] **Step 4: Write the docs** listed above, with the numbers of Steps 1 and 2. Run `atlas validate` and the explorer's refresh.
- [ ] **Step 5: Commit, review, PR.** `docs: buses in the travel estimate (D10, S9)`. Then `/code-review` on the branch, a pull request, green CI read in its own step, squash-merge.
