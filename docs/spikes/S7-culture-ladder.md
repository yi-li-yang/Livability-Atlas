# S7: the culture evidence ladder

Status: **partly done.** A spike of step 0.4 ([roadmap](../roadmap.md#spikes)). Its code is [pipeline/notebooks/s7_culture_ladder.py](../../pipeline/notebooks/s7_culture_ladder.py), throwaway and never imported by `atlas`. Four of the ladder's rungs are tested. The access rung waits for the station matrix, and the perception, ranking and user's-own rungs cannot be tested on open data.

## Question

Does the culture evidence ladder work on a sample of neighbourhoods, with a known-fact assertion for each kind of evidence?

## Answer

**The counting rungs work, and agree: venues, variety of venues, listed buildings and Wikipedia articles all separate London's cultural centres from its suburbs, and pass every assertion.** The activity rung's second signal, Wikipedia page views, does not: it measures how famous a place is, not how much culture goes on in it. The test is a coarse one, and it cannot say how well the rungs rank places that are alike.

## What was done

1. Took twelve places: six cultural centres (Soho, the South Bank, Shoreditch, Camden Town, Brixton, Greenwich) and six suburbs (Orpington, Chigwell, Edgware, Sutton, Hayes in Bromley, Upminster).
2. Measured, within an 800 m walk of each (1 km for Wikipedia):
   - **Direct:** the venues of the ladder's example kinds in the GLA's Cultural Infrastructure Map: theatres, music venues, commercial galleries, museums and public galleries, cinemas, libraries, arts centres and dance venues.
   - **Variety:** how many of the map's 35 kinds of venue, apart from pubs, listed buildings and heritage at risk, are present.
   - **Character:** the listed buildings and whether the point lies in a conservation area, from planning.data.gov.uk.
   - **Activity:** the geotagged Wikipedia articles within 1 km, and the monthly page views in 2025 of the 20 nearest.
3. Asserted one known fact for each rung, and checked it.

## Findings

| Place | Venues | Kinds of venue | Listed buildings | In a conservation area | Articles within 1 km | Views a month, 20 nearest |
| --- | --- | --- | --- | --- | --- | --- |
| Soho | 200 | 19 | 936 | yes | 500 | 19,084 |
| South Bank | 55 | 18 | 297 | yes | 500 | 12,005 |
| Shoreditch | 90 | 24 | 354 | yes | 189 | 16,541 |
| Camden Town | 33 | 17 | 188 | yes | 109 | 20,985 |
| Brixton | 18 | 18 | 80 | yes | 58 | 6,705 |
| Greenwich | 18 | 13 | 193 | yes | 77 | 46,610 |
| Orpington | 1 | 2 | 6 | no | 6 | 7,291 |
| Chigwell | 0 | 0 | 21 | no | 5 | 3,855 |
| Edgware | 2 | 4 | 13 | no | 11 | 4,945 |
| Sutton | 5 | 6 | 13 | no | 27 | 10,811 |
| Hayes, Bromley | 1 | 2 | 12 | no | 6 | 2,042 |
| Upminster | 2 | 3 | 11 | no | 14 | 5,790 |

The Wikipedia search returns at most 500 articles, which Soho and the South Bank reach.

**All eight known-fact assertions hold:** Soho has more venues than any suburb, and the South Bank at least five times the median suburb's; Soho has at least three more kinds of venue than the median suburb, and every centre has more than it; Greenwich has more listed buildings than any suburb, and lies in a conservation area; Soho has more Wikipedia articles than any suburb, and the centres' median views exceed the suburbs'. The centres' medians against the suburbs': 44 venues against 1.5, 18 kinds against 2.5, 245 listed buildings against 12.5.

**The rungs agree about centres against suburbs,** with rank correlations of 0.84 to 0.98 across the twelve places, except for page views (0.68 to 0.80). **Within the six centres they agree less:** 0.5 to 0.9 among venues, kinds, listed buildings and article counts. Page views stand apart (−0.06 with venues, 0.14 with listed buildings, −0.52 with kinds of venue), with only six centres behind each figure.

**Page views follow fame.** Greenwich has the most views by far (46,610 a month for its 20 nearest articles) with 18 venues, probably because its landmarks, such as the Cutty Sark and the Royal Observatory, draw readers from everywhere. Brixton, a lively centre, has the fewest views of any centre. Views of what is nearby tell how famous the neighbourhood's landmarks are, not how much goes on there.

**The test is coarse.** Any measure that counts anything cultural separates Soho from Edgware. It does not show which of the rungs ranks two alike places correctly. A known-fact assertion between neighbouring centres, such as "Shoreditch has more live music than Camden Town", would need a ground truth that the spike did not have.

**The data.** The Cultural Infrastructure Map is under the Open Government Licence v3, and dated: its venues are from 2018 and 2019, with some revised in 2023. The dataset's page lists a 2023 web service with a newer version, marked as restricted, which the spike did not try to read.

## Decisions

1. **The ladder's top rungs stand as the culture indicators:** venues within a walk (direct), and the variety of kinds (indirect). They agree, so the weight can sit on one, and the other can show the kinds.
2. **Character, listed buildings and conservation areas, stays as a rung,** as an indirect indicator.
3. **Drop Wikipedia page views as a culture signal.** The number of geotagged articles is a weaker substitute, which hits a ceiling of 500 in the centre and reflects what editors chose to write about. It is not an MVP candidate.
4. **Add the Cultural Infrastructure Map to the catalogue,** under the Open Government Licence v3, with its dates stated. The culture research (not in the MVP) will decide how fresh the data has to be.
5. **The access rung** (venues within 30 minutes by public transport) waits for the station matrix of [S4](S4-routing.md).

## What was not tested

- **Access, perception, published rankings and the user's own ratings.** The first needs the matrix, the second a model, and the third needs licences ([rankings](../factors/rankings.md)).
- **Event listings,** the activity rung's other example: no open source was found.
- **Listed buildings' and conservation areas' licence.** planning.data.gov.uk serves Historic England's and the councils' data, and the licence was not read, so they are not in the catalogue.
- **A larger sample,** and venues the map does not hold, such as pubs with live music.

## Reproduce

From `pipeline/`, with the map's GeoPackage in `data/raw/cim/cim.gpkg`:

```sh
uv run python notebooks/s7_culture_ladder.py
```

It makes about 300 calls to Wikipedia, Wikimedia and planning.data.gov.uk, caches each in `data/interim/s7_cache.json`, and takes a few minutes the first time.
