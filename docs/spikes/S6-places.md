# S6: how complete are the sources of places?

Status: **partly done.** A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s6_fetch.py](../../pipeline/notebooks/s6_fetch.py), [s6_completeness.py](../../pipeline/notebooks/s6_completeness.py) and [s6_counts.py](../../pipeline/notebooks/s6_counts.py), throwaway and never imported by `atlas`. Food and drink, supermarkets and shops are tested against a register. Pharmacies, gyms, libraries, GP practices and hospitals are not, for lack of a register to test against.

## Question

How complete are Overture, Foursquare Open Source Places and OpenStreetMap, brand tags included? How much do straight-line and network walking distances differ?

## Answer

- **Use Overture and OpenStreetMap together.** Neither is complete. Together they match about two thirds of London's cafés, restaurants and takeaways by name and place, and three quarters of its supermarkets and convenience shops, and the true figures are higher, because the test undercounts.
- **Foursquare adds little.** Its records are inside Overture already, and take Overture's match for eating places from 57% to 60%.
- **Brand tags are patchy in both:** OpenStreetMap tags a brand on 19% of its eating places, Overture on 12%.
- **Measure walks along streets.** A walk is a median 1.33 times its straight line, and more than 1.5 times for 23% of routes.

## What was done

1. Fetched Overture's places for Greater London's bounding box from release 2026-10-21.0 (750,251 places), OpenStreetMap's matching features from Geofabrik's London extract (39,501), and the Food Standards Agency's register of rated food businesses for the 33 boroughs (66,344 with a location).
2. Took the FSA register as the ground truth for food, because every food business has to be on it. For each kind (eating places: restaurants, cafés and takeaways, 33,126; pubs and bars, 3,539; supermarkets and hypermarkets, 2,229), counted the share of businesses that have a place of a matching kind in a source within 100 m, and the share that have one **with the same name** there (the words of the shorter name mostly shared).
3. Repeated the proximity test with each business moved 300 m, to find what chance alone gives, because London is dense.
4. For brand tags, took the 59 names that 20 or more eating places on the register share, such as Pret A Manger and Greggs, and counted how many of those businesses a source finds, and how many of the places it finds carry a brand.
5. Routed 150 walks from random homes to eating places 300 m to 1.5 km away with OpenStreetMap's foot routing, and divided each route's length by its straight line.
6. Counted cafés and restaurants within 800 m of each of 11,182 homes cells, in the two sources pooled.

## Findings

**Proximity alone misleads.** 19% to 54% of the register's businesses have a source place of the kind within 100 m by chance, depending on the kind and the source, so "a place within 100 m" (77% to 95%) overstates completeness. A near place is often a neighbour: in a look at twelve cafés and restaurants with a Foursquare eating place within 100 m, most had a different business next door. The name match is the measure to trust, and it is a lower bound, since the register holds legal names ("Crispy Dosa Wood Green Limited") and the sources hold trading names.

**Found by name within 100 m** (share of the register's businesses):

| | OpenStreetMap | Overture | Overture records with Foursquare among their sources | Both together |
| --- | --- | --- | --- | --- |
| Cafés, restaurants and takeaways | 43% | 60% | 5% | 66% |
| Pubs and bars | 62% | 65% | 2% | 71% |
| Supermarkets and convenience shops | 61% | 67% | 1% | 76% |

**Foursquare.** 66,976 of Overture's London places come from Foursquare, and 6,264 are eating places, but they account for about 1,250 of Overture's matches, against 11,900 from Meta and 5,200 from BrightQuery. The Foursquare Open Source Places data itself was not fetched, since Overture carries it.

**Staleness.** Overture marks 33,451 London places (4%) as permanently closed, 95% of them from its BrightQuery source, and the spike left them out. Of the rest, 16% of its eating places have no food business on the register within 100 m, against 3.5% of OpenStreetMap's: Overture is more complete, and OpenStreetMap more precise.

**Brand tags.** On the 2,845 businesses with a chain name:

| | Finds the chain business | Of those, carry a brand | Share of all its eating places with a brand |
| --- | --- | --- | --- |
| OpenStreetMap | 67% | 89% | 19% |
| Overture | 76% | 69% | 12% |

**Walking.** The network distance over the straight line has a median of 1.33 and a mean of 1.40, and runs from 1.13 to 1.88 for the middle 90% of routes. 23% of routes are more than 1.5 times their straight line. The 1.3 that the S4 estimate assumed for a walk to a station is the median, with a long tail.

**Counts.** Within 800 m of a home, the median has 11 cafés and 35 restaurants, and the 95th percentile 76 and 194. 2% of homes cells have no café, and 16% have 3 or fewer. These pooled counts understate, by the match rates above.

## Decisions

1. **Use both sources, and count a place once.** Overture, leaving out places it marks permanently closed, and OpenStreetMap. The catalogue's place datasets already list both.
2. **Foursquare gets no entry of its own.** Its records are in Overture.
3. **Measure the walks along streets,** not as a straight line, for the nearest-place indicators. The catalogue's method says so.
4. **Cafés and restaurants score by rank within the region,** a percentile curve, since no standard says how many are enough and the counts are too skewed for a ramp. Cuisine variety still waits for [S8](../roadmap.md#spikes).
5. **Do not trust a near place as a match.** Any later matching, such as for prices, needs names or identifiers.

## What was not tested

- **Pharmacies, gyms, libraries, GP practices and hospitals.** No open register was at hand: the legacy NHS file for GP practices now returns 403, and its replacement is an interactive export. A test of GP practices and A&E sites belongs with the [Health care research](../specs/2026-10-28-health-care-research.md).
- **A better name match,** and the places that sources list under the wrong category.
- **Where the gaps lie,** whether outer London or particular kinds of business are missing.
- **Network distance to the nearest place of each kind,** which would show how often the nearest by straight line is not the nearest by street.

## Reproduce

From `pipeline/`, with Geofabrik's London extract in `data/raw/osm/greater-london.osm.pbf`, and the data that S1 and S2 need:

```sh
uv run python notebooks/s6_fetch.py
uv run python notebooks/s6_completeness.py
uv run python notebooks/s6_counts.py
```

The fetch step reads Overture from its public S3 bucket with DuckDB, and the FSA register from its open API, and caches both. QuackOSM 0.19 needs DuckDB below version 2, which the `spikes` dependency group pins. The completeness script makes 150 foot-routing requests, one every 1.2 seconds.
