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

## Decisions

1. **The design stands:** a browser estimate from the walk, the station matrix and the walk, labelled an estimate. D10 is accepted.
2. **The engine is r5py with GTFS timetables,** because it computes the whole matrix at several departure times in minutes, where the API would take about 21 hours for one. It waits for the owner's registrations. **The Journey Planner API is the fallback,** proven by this spike, with a key from TfL's portal for the 500 calls a minute.
3. **Add buses later,** as the next largest source of error. Bus times need the BODS timetables in the same r5py run.
4. **Check the estimate again on a larger sample** when the real matrix exists, across several departure times.

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
