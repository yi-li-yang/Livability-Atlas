# Your places: the station matrix and the travel estimate in the browser

Status: built. Queue rows T0.1 and 3.1, and the last item of the roadmap's "Travel and hard limits" (D10).

## Goal

A user adds up to 3 places of their own (work, family) and the map scores travel time to them in place of the 4 default places. The estimate runs in the browser, so the places never leave it (D08, D10).

## The estimate

For a hex cell $c$ and a place $p$:

$$T(c, p) = \min\Big(\text{walk}(c, p),\ \min_{s \in S(c),\ q \in S(p)} \big[\text{walk}(c, s) + M(s, q) + \text{walk}(q, p)\big]\Big)$$

- $S(c)$: the stations within a 40-minute street walk of the cell's centre, at most the 8 quickest, with their walking minutes (`cell-stations.parquet`, from the street network, as the travel time to the default places already uses).
- $S(p)$: the stations within 40 minutes of the place, by straight line times 1.33 (S6: the median ratio of a street walk to its straight line) at 80 m a minute. The browser has no street network.
- $\text{walk}(c, p)$: the same straight-line walk from the cell's centre, so a place next door is not routed through a station.
- $M(s, q)$: the station matrix, whole minutes from station $s$ to station $q$ at about 08:30 on a weekday, including the wait at the first platform and at each change.

The result carries the evidence type "estimate". Buses are not in the matrix (D10's known limit).

## The station matrix (pipeline)

The Journey Planner cannot give all pairs (about 745,000 calls, some 200 hours without a key). The matrix is built from timetables with a shortest-path search instead.

- **TfL's own lines** (Tube, DLR, Overground, Elizabeth line, tram): `Line/{id}/Route/Sequence/{direction}` gives the stop order of each route, and `Line/{id}/Timetable/{first stop}` the minutes from the first stop to each later one (`stationIntervals`) and the departures (`knownJourneys`), whose number between 07:00 and 10:00 on a weekday gives the headway. Both answer without a key (checked on 2026-11-22). **Not every timetable answers:** some fail at TfL's end and a few list only weekends, so every pair of next stops in a route sequence is a ride, timed by a timetable where one gave it and otherwise by its straight line at the mode's speed between stops (Tube 550 m a minute, about 33 km/h; DLR 450; Overground 600; Elizabeth line 700; tram 350), and a line with no weekday departures takes its mode's usual headway (Tube 4 minutes, DLR and Elizabeth line 6, tram 8, Overground 10).
- **National Rail**: TfL lists each operator's routes (`orderedLineRoutes`, by NaPTAN id) but gives no timetable. The minutes between two stops that a service calls at one after the other come from one Journey Planner call each, by National Rail only, at 08:30 on Wednesday 25 November 2026 (the Journey Planner refuses a day that has passed, so the date is fixed in `tfl_timetables.DATE` and must move ahead for a new fetch), for the 845 pairs inside the region's box. About one in ten has no single train (the pair is served by an Elizabeth line or Overground train that TfL lists under the operator), and takes its straight line at 900 m a minute. The headway is a fixed 12 minutes.
- **The graph**: a node for each station and one for each (station, line); a ride edge between next stops of a route; boarding costs 5 minutes from the street to the platform plus half the line's headway; getting off costs 2 minutes from the platform to the street; a change of line pays both; a change to a stop of another id within 300 m in a straight line (such as 940G and 910G at the same station) costs the walk at 1.33 times the straight line. Dijkstra from each station gives a row of the matrix, in whole minutes.
- **The two walks are fitted**, to the Journey Planner's times from each station to the four default places (3,401 journeys): with no walks the estimate is a median 0.82 of the Journey Planner's time, with 5 and 2 minutes 0.98, and 81% of the journeys are within 20% (mean absolute error 5.3 minutes). The longest misses are journeys where a bus is quicker (Mile End to Canary Wharf: 18 minutes by the Journey Planner, 35 estimated).
- **Checks**: a known fact of the QA report compares the estimate for the four default places with the indicator built from the Journey Planner, cell by cell. On the London build of 2026-11-22: 92% of cells have both, the rank correlation is +0.95, the estimate is a median 0.99 of the Journey Planner's time, and within 20% in 97.5% of cells. The fact fails below 85% of cells, a correlation of +0.85, or a median outside 0.85 to 1.15.
- **A day that has passed**: the Journey Planner refuses one, so a fetch whose answers are mostly empty stops and says to move `DATE` ahead, and keeps none of the empty ones.

## The bundle

A bundle may carry more files beside `cells.parquet`; the manifest lists them under `travel` (`stations`, `cell_stations`, `matrix`, and the walking speed and street factor). The version hash covers every file in a fixed order, so a rebuild stays byte-identical. The app fetches them only when the user adds a first place.

## The app

- "Your places" in the preferences panel: up to 3, each with a name the user types. A place is added by a postcode, looked up in a table of the region's postcodes shipped in the bundle (Code-Point Open, OGL, already a dataset), loaded whole on first use so no postcode is sent anywhere; or by clicking the map.
- With one place or more, `travel-time-to-places` is the mean of $T$ over the user's places, with the indicator's own ramp. The reasons show the minutes to each place.
- Places are kept in the browser's storage only, never in the link.

## Error check

`atlas travel-check london` asks the Journey Planner for 300 random pairs of cells (from one cell's centre to another's) at 08:30, 12:30 and 18:00, keeping the answers by the cells' ids, and writes the error table (median, mean absolute, share within 20%, by distance band) to the S4 write-up and D10's history. Result (2026-11-22): 258 journeys with both times at each hour; the estimate is a median 11 minutes too long and within 20% in 70%, the same at the three times, and the error grows with the walks to stations, so it comes from the buses left out.
