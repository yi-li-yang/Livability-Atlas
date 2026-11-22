# S4: routing and the in-browser estimate

Status: **partly done.** A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s4_estimate_error.py](../../pipeline/notebooks/s4_estimate_error.py), throwaway and never imported by `atlas`. The estimate's error and TfL's terms are answered. r5py was not run, because its inputs need accounts that only the owner can create.

## Question

Can r5py with GTFS timetables, or the TfL API, build the station matrix? How large is the error of the in-browser estimate against TfL Journey Planner? What do TfL's terms and limits allow? The answers decide [D10](../decisions.md#d10-travel-times).

## Answer

- **The estimate works.** Walking to a nearby station, riding the station-to-station time, and walking from a station is within 10 minutes of the Journey Planner's door-to-door time for 74% of journeys, and within 20% for 81%, with a median error of 12%. It is never more than 20% too short, and more than 20% too long in 19% of journeys, which is the known limit that buses are not in the matrix.
- **The API can build the matrix, slowly.** 797 stations make about 634,000 ordered pairs, which is about 21 hours of calls at TfL's limit of 500 a minute, for one departure time.
- **r5py is the better engine and cannot be built yet.** It needs timetable data from three registered sources and a JDK, and the owner holds none of the accounts.
- **TfL's terms allow it,** with attribution and a warning.

## What was done

1. Listed 797 stations in London from DfT's NaPTAN: the rail stations and the metro stations (Tube, DLR and the rest of the metro entries).
2. Drew 30 pairs of homes cells at random, 4 to 20 km apart.
3. For each pair, asked the Journey Planner for the door-to-door time at 08:30 on Wednesday 4 November 2026, by all modes including buses, and by rail and walking only.
4. Estimated each pair as the browser would: the walk to each of the three nearest stations at each end (straight line, times 1.3 for the streets, at 4.8 km/h), plus the Journey Planner's time between each of the nine pairs of stations, taking the quickest. The station-to-station times stand in for a matrix built from it.
5. Compared the estimate with the door-to-door time. 330 anonymous calls, one every 1.5 seconds, 27 of the 30 pairs answered in full.

## Findings

| Against | Median journey | Median error | Mean absolute error | Within 10 minutes | Within 20% | More than 20% too long |
| --- | --- | --- | --- | --- | --- | --- |
| Journey Planner, all modes | 68 min | −2.5 min | 9.6 min | 74% | 81% | 19% |
| Journey Planner, rail and walking only | 78 min | −8.9 min | 9.8 min | 63% | 96% | 0% |

The estimate matches the rail-only journey within 20% in 96% of cases, so the error against all modes comes from buses. The rail-only estimate runs short by 9 minutes at the median, because it picks the best of nine station pairs, where the Journey Planner's door-to-door route need not. **The sample is small** (27 journeys, one morning), and it leaves out waits that vary through the peak, which a real matrix would average over several departures.

**TfL's terms** (the Transport Data Service page): commercial use and adapting the information, including combining it with other information, are allowed. Attribution must read "Powered by TfL Open Data", with the Ordnance Survey and Geomni lines. Traffic is limited to 500 calls a minute per data feed. The page sets no limit on caching or storing results, and does not mention journey planner results, so storing computed travel times is not excluded and is not mentioned either. TfL may revise the licence at any time without notice and does not guarantee supply. Anonymous calls worked for this volume.

**What r5py needs.** It needs a JDK 21 or later, which on Windows its documentation says to take from conda or Microsoft's OpenJDK build. It also needs timetables as GTFS, and TfL lists no GTFS timetable: its timetable feed covers the Tube, buses, DLR, tram, cable car and river services, and needs registration. Buses come from the Bus Open Data Service, which needs an account and token, and National Rail including the Elizabeth line comes from National Rail Open Data, which needs credentials. That is three registrations, and a conversion of TfL's feed to GTFS.

### The check on the station matrix (2026-11-22)

The matrix was built from TfL's timetables ([spec](../specs/2026-11-22-own-places.md)), and `atlas travel-check london` asked the Journey Planner, by every mode, for 300 random journeys from one hex cell's centre to another's, at 08:30, 12:30 and 18:00 on Wednesday 25 November 2026, and compared each with the estimate that the app makes. 258 journeys have both times at each hour.

| Journeys | Count | Median error | Mean absolute error | Within 20% |
| --- | ---: | ---: | ---: | ---: |
| 08:30 | 258 | +10.8 min | 13.3 min | 71% |
| 08:30, under 5 km | 9 | +12.7 min | 15.5 min | 11% |
| 08:30, 5 to 15 km | 81 | +9.5 min | 14.3 min | 58% |
| 08:30, over 15 km | 168 | +11.1 min | 12.8 min | 80% |
| 12:30 | 258 | +11.0 min | 13.5 min | 71% |
| 12:30, under 5 km | 9 | +13.1 min | 17.3 min | 11% |
| 12:30, 5 to 15 km | 81 | +9.4 min | 13.9 min | 62% |
| 12:30, over 15 km | 168 | +11.7 min | 13.0 min | 79% |
| 18:00 | 258 | +10.5 min | 13.9 min | 69% |
| 18:00, under 5 km | 9 | +11.1 min | 15.3 min | 22% |
| 18:00, 5 to 15 km | 81 | +10.4 min | 14.7 min | 59% |
| 18:00, over 15 km | 168 | +10.6 min | 13.5 min | 76% |

**The estimate is too long by a median 11 minutes (a ratio of 1.14), at each of the three times,** and within 20% in 70% of journeys. The error grows with the walks to stations at both ends: a median 6 minutes where the two walks add up to 10 to 20 minutes, 10 minutes at 20 to 30, and 14 minutes over 30. So it is the buses that the matrix leaves out, which carry the Journey Planner to and from stations quicker than a walk in outer London. Random journeys are mostly from outer cell to outer cell, which is the worst case: to a central place, where the stations are close, the estimate is a median 0.98 of the Journey Planner's time (3,401 journeys from each station to the four default places), and the QA report's comparison over every cell gives a rank correlation of +0.95 and a median ratio of 0.99. The time of day changes almost nothing, since the matrix's waits are half the morning headway and the Journey Planner's peak and midday services differ little. Journeys under 5 km are too few (9) to say more than that the estimate is long for them too.

## Decisions

1. **The design stands:** a browser estimate from the walk, the station matrix and the walk, labelled an estimate. D10 is accepted.
2. **The engine is r5py with GTFS timetables,** because it computes the whole matrix at several departure times in minutes, where the API would take about 21 hours for one. It waits for the owner's registrations. **The Journey Planner API is the fallback,** proven by this spike, with a key from TfL's portal for the 500 calls a minute.
3. **Add buses later,** as the next largest source of error. Bus times need the BODS timetables in the same r5py run.
4. **Check the estimate again on a larger sample** when the real matrix exists, across several departure times. Done on 2026-11-22 (above): buses stay the largest source of error.

## What the owner can do

- Register for the three timetable sources: the Bus Open Data Service, National Rail Open Data, and TfL's open data portal. Put the credentials in `.env`, which is never committed.
- Install a JDK 21 (Microsoft's OpenJDK build) when the registrations are done.

## What was not tested

- r5py itself, and how long it takes for London.
- Bus journeys inside the estimate, and the best number of nearby stations to try (three here).
- A matrix at several departure times, and weekends.

## Reproduce

From `pipeline/`, with NaPTAN in `data/raw/naptan/naptan.csv` (DfT's bulk download) and spike S2's data:

```sh
uv run python notebooks/s4_estimate_error.py
```

It takes about 10 minutes, and caches every answer in `data/interim/s4_cache.json`, so an interrupted run resumes.
