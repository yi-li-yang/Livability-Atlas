# S9: buses to and from the stations

Status: **done.** A spike of Phase 1 ([progress](../progress.md)). Its code is [pipeline/notebooks/s9_buses.py](../../pipeline/notebooks/s9_buses.py), throwaway and never imported by `atlas`.

## Question

The travel estimate walks from a cell to a station, rides the station matrix, and walks from a station to the place ([D10](../decisions.md#d10-travel-times)). Where a bus would take a person to or from the station sooner, the estimate is too long: a median 11 minutes, and 14 where the walks add up to more than 30 minutes ([S4](S4-routing.md)). Can a walk-and-bus leg from TfL's bus data, which needs no key, replace the walk-only leg at both ends, and how much does it cut the error that `atlas travel-check london` measures?

## Answer

- **Yes.** With a bus leg at both ends, the estimate is a median **5.5 minutes** too long at 08:30, not 10.8, and within 20% of the Journey Planner's time in **85%** of journeys, not 71%. The share more than 20% too long falls from 28% to 13%, and the share more than 20% too short stays at 1%.
- **The gain is largest where the walks are long:** where the two walks of today's estimate add up to more than 30 minutes, the error falls from +14.2 to +7.0 minutes.
- **More cells reach a station:** 95.0% of cells have a station within 40 minutes by walk or bus, against 92.2% on foot.
- **8 stations per cell are enough.** 16 gain 0.6 minutes and 1 point for a links file 37% larger.
- **No key is needed.** The fetch is 2,710 requests, about 40 a minute, so about 70 minutes once; the kept answers take 12 MB.

## What was done

1. **Fetched the bus data** from TfL's Unified API without a key: the 677 bus lines, each line's stops in order in both directions (1,354 answers), and the timetable from the first stop of each route (1,355 answers, 1,342 of them with minutes between stops). TfL answered 429 above about 50 requests a minute, so the fetch asked one at a time. The answers are kept, trimmed, in `data/raw/tfl/buses/`.
2. **Left out 72 lines with no weekday departures from 07:00 to 10:00:** 64 night buses and 8 school or once-a-day routes. They do not run at the times the check asks about. The other 605 lines give 45,721 rides between next stops at 19,932 stops.
3. **Built a graph of stops, lines and stations.** Boarding a line at a stop costs half the line's headway plus 0.5 minutes. The headway comes from the weekday departures from 07:00 to 10:00, as for TfL's rail lines (a median 12 minutes). A ride between next stops takes the timetable's minutes, or the straight line at 15 km/h for the 4% of rides that no timetable times. Getting off costs nothing. A stop links to each station within a 6-minute walk (the straight line, times 1.33 for the streets, at 80 m a minute).
4. **Searched back from each of the 863 stations**, up to 40 minutes, for the time from every stop to the station.
5. **Gave each cell a time to each station:** the quicker of the street walk (up to 40 minutes, as now) and the street walk to a stop (up to 10 minutes) plus that stop's time to the station. Each cell keeps its 8 quickest stations, as now.
6. **Used the same times at the far end.** The time from a station to a place is the quicker of the straight-line walk (as now) and the place's own cell's time to that station, read backwards: a station to the cell takes as long as the cell to the station.
7. **Compared with the 300 journeys** that `atlas travel-check london` kept: the Journey Planner's door-to-door times by every mode, at 08:30, 12:30 and 18:00 on Wednesday 25 November 2026. This made no new Journey Planner calls.

## Findings

At 08:30:

| Estimate | Journeys | Median error | Mean absolute error | Within 20% | More than 20% too long |
| --- | ---: | ---: | ---: | ---: | ---: |
| Now: walks only | 258 | +10.8 min | 13.3 min | 71% | 28% |
| A bus to the station only | 267 | +8.0 min | 11.4 min | 79% | 20% |
| **A bus at both ends, 8 stations kept** | 282 | **+5.5 min** | **8.7 min** | **85%** | **13%** |
| A bus at both ends, 16 stations kept | 282 | +4.9 min | 8.3 min | 86% | 12% |
| As above, and journeys by bus alone | 282 | +4.5 min | 8.1 min | 87% | 11% |

The other two times move the same way. With a bus at both ends and 8 stations kept, the error is +6.0 minutes at 12:30 (was +11.0) and +5.9 at 18:00 (was +10.5), within 20% in 87% and 85% of journeys.

The number of journeys grows from 258 to 282 because 24 journeys that had no estimate now have one: one of their cells is more than a 40-minute walk from any station, but reaches one by bus.

By the walks at both ends of today's estimate, as S4 grouped them (08:30):

| Walks | Journeys | Now | A bus at both ends, 8 kept |
| --- | ---: | ---: | ---: |
| 10 to 20 minutes | 53 | +3.2 min | +1.2 min |
| 20 to 30 minutes | 66 | +9.2 min | +4.4 min |
| Over 30 minutes | 134 | +14.2 min | +7.0 min |

By distance (08:30, a bus at both ends, 8 kept): under 5 km, +9.1 minutes and 30% within 20% (only 10 journeys); 5 to 15 km, +4.3 minutes and 75%; over 15 km, +5.4 minutes and 93%.

- **The estimate is still long, by design.** It waits half the headway at each boarding, as for a person who arrives at a random time. The Journey Planner times each journey to a departure, so it waits less.
- **Journeys by bus alone stay out.** The browser cannot make them from a station matrix, and a stop-to-stop matrix for 19,932 stops would be far larger. A bus alone is quicker than any rail journey in only 10 of 282 journeys, and all of its gain falls on journeys under 15 km.
- **A first run gave the lines with no morning departures the usual 12-minute headway,** so the night buses counted as day routes. It gave +4.4 minutes, which flatters the method. The numbers above leave those lines out.
- **The default places** (the Journey Planner's time from each station, plus the way to the station): 95.0% of cells have a value, against 92.2%. On the same cells, the median of the travel time falls from 63.1 to 61.3 minutes. The median cell changes by −0.4 minutes, and a tenth of cells become 7.5 minutes or more quicker.
- **The links file stays small:** 359 KB with 8 stations kept (the bundle's file is 368 KB now), or 493 KB with 16.

## Decisions

1. **Build it** (`feat/bus-access`): a bus leg at both ends, with 8 stations kept for each cell. One change in `_travel` in `build.py` gives the walk-or-bus times to both the default places and the cell-station links. The shape of `cell-stations.parquet` stays the same.
2. **The browser uses the place's cell at the far end.** The estimate takes the quicker of the straight-line walk from a station and the links of the place's cell, read backwards. A place outside the bundle's cells keeps the straight-line walk. The Python reference and the golden travel cases change with it.
3. **The bus data is part of the TfL Unified API dataset**, whose licence is checked, with one more line in what it tells. The fetch runs once, without a key, and its answers are kept in `data/raw/`.
4. **Journeys by bus alone stay out**, for the reasons above.
5. **r5py with the Bus Open Data Service stays the later engine**, for exact waits and other departure times. Buses no longer wait for the owner's registrations.

## What was not tested

- Other values of the set costs: 0.5 minutes to board, a 6-minute walk from a stop to a station, and a 10-minute walk to a stop. They were set, not fitted.
- Evenings after 19:00, nights and weekends: the check asks about weekday daytime only.
- How fast the bus data goes out of date: TfL changes routes several times a year, and a refresh fetches them again.

## After the spike

The build (bundle `446823cd3071`, D10) fixed two flaws that a code review found in this spike's graph. A stop linked straight to the stations within a 6-minute walk, so a cell could reach a station by walking to a stop and on, with no bus: that undercuts the street walk where the streets are long, such as across a river. Now a stop's way to a station boards and rides at least one bus. And the headway added up the departures of every first stop, where a short working's timetable also lists the buses that pass its first stop: each direction now counts its busiest first stop. The travel check on the built bundle gives the numbers above to within 0.1 minutes: +5.5 minutes at 08:30, within 20% in 85%. The notebook keeps the spike's graph.

## Reproduce

From `pipeline/`:

```sh
PYTHONUTF8=1 uv run python notebooks/s9_buses.py fetch
PYTHONUTF8=1 uv run python notebooks/s9_buses.py analyse
```

`fetch` takes about 70 minutes and keeps every answer, so a stopped run carries on. `analyse` takes a few minutes. It reads bundle `dc3d5a941943`, the answers that `atlas travel-check london` kept, and the Journey Planner's station times of the London build, and it keeps the walk times in `data/interim/s9/`.
