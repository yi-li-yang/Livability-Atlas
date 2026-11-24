# Backlog

Features to add, grouped by target phase. Each item has a status: idea, planned, in progress or done. Link a spec once one exists. Work for Phase 0 and Phase 1 is tracked in the [roadmap](roadmap.md).

## Phase 2: depth and trust

| Item | Status |
| --- | --- |
| Place and street names drawn above the hex cells | shipped: the cells sit under the water, roads and names, over the land use (D23) |
| `DESIGN.md` for the Impeccable design skill (`/impeccable document`), now that the map's look is settled | idea |
| A full `/impeccable critique` of the map and the legend | shipped: 24/40 on 2026-11-23, and its three P1 and two P2 items are fixed (#108, #110 to #113) |
| A `/impeccable critique` of the rest of the app: the factor tree and the preferences panel, the reasons panel, the phone sheets | planned |
| A search for a postcode or an area on the map, in the browser only (D08), from the map critique | idea |
| A way back to all of London after the map flies to a place, from the map critique | idea |
| Keyboard access to the hex cells, beyond the list of top neighbourhoods, from the map critique | idea |
| A short "how to read the map", from the map critique | idea |
| More factors, in catalogue priority order | planned |
| Placeholders at WCAG AA contrast (they were 3.9:1), found by `impeccable detect` (2026-11-23; its "card inside a card" was a false positive: a bordered toggle) | shipped: 4.7:1 |
| Crime rates per resident and worker, so that centres with few residents and many workers, like the City of London, stop topping every crime ([spike S2](spikes/S2-crime.md)). Needs a workplace population table whose licence and geography are checked | idea |
| Presets, e.g. a renter commuting to the centre, a family with children, a retiree | shipped: "Start from", from the manifest's `presets` |
| Preference profiles as shareable URLs, with places left out unless the user includes them | idea |
| Side-by-side comparison of two hex cells or neighbourhoods | idea |
| "No weak spots" scoring mode (weighted geometric mean) | shipped: the "How the factors combine" switch |
| Sensitivity view: how stable the top 10 stays when weights shift ±20% | shipped: a line under "Top neighbourhoods" and a mark on the steady ones |
| Rescoring in a Web Worker, so that the stability (30 rescorings, about 1 s in "No weak spots") never holds the page up at all | idea |
| A switch for the direction of each user-direction indicator, and a band for each user-range indicator | shipped: "More is better" and "Less is better", and "Full marks from … to …" |
| Scores coloured by how good they are, so that a factor named for a bad thing (Crime, Noise) reads plainly | shipped: one red → yellow → blue-green scale on the map, the legend and the bars |
| Scoring curves that users can edit | idea |
| Start with a few essentials, and "Everything, equally" in Start from ([spec](specs/2026-11-23-start-with-essentials.md), D14) | shipped |
| A "pick your top few" step for a first visit, from the full list (Bond, Carlson and Keeney 2008; Netzer and Srinivasan 2011), if the essentials start leaves people with flat weights | idea |
| Score by the amount, never by rank: a region ramp, a log scale, no percentile curve ([spec](specs/2026-11-23-score-by-the-amount.md), D25) | shipped |
| The values at the ends of the legend, and the value of a hex cell in the quick look, when the map shows one measured indicator | shipped (with D25) |
| Move an indicator with a national scale from a region ramp to a fixed ramp, so its score compares across regions (school league tables, years of good health), once a second region needs it | idea |
| "Areas like X" search (ML) | idea |
| Price and rent models, and value for money (ML) | idea |
| Area types by clustering (ML) | idea |
| Scheduled data refresh with anomaly checks (ML) | idea |
| Buses in the travel-time estimate for a user's places (the station matrix has rail only, so a place a bus reaches quicker is estimated too far); cycling, step-free and night-time travel; jobs within 45 min | planned: spike S9 first (progress.md, Next) |
| Postcodes of the user's places geocoded by street address, or by a search for a place name, both still in the browser | idea |
| Personal notes layer: users rate places they have visited, stored in the browser | idea |
| Destinations: the user picks public places or chains, e.g. Costco, IKEA or the nearest airport, and each is scored by distance to the nearest one. Starts as straight-line distance computed in the browser from a small points file per destination (brand tags, checked in spike S6); later car and public-transport times | idea |
| Your industry: jobs in a chosen industry within reach | idea |
| Brand presence: brand groups checked against data | idea |
| "Why we differ" view against published rankings | idea |
| Known facts and relations as a data file in the catalogue, once a second city shows which shapes repeat (today they are code in `datasets/cities/<region>/facts.py`, [spec](specs/2026-10-29-qa-report.md)) | idea |
| The QA report in the app's "About the data", with the version and the date of each dataset | idea |
| No score where nobody lives: a hex cell with few or no homes (parks, airports, industrial land) is left clear and not ranked (D22) | shipped |
| Walks measured from each hex cell's homes, not its centre. On the London bundle of 2026-11-22 the homes at a park's edge were a median of 48 m from their hex cell's centre, so the gain is small (D22) | idea |
| A source of homes for a commercial edition, since the energy certificates' licence is not for commercial use: OS Open UPRN with a way to tell homes apart, or AddressBase (D22) | idea |
| Measures that say the same thing share their weight (scoring.md, section 10). About 30% of the default weight measures what is within a walk, over 9 top-level factors, against about 7% for parks and nature, so a home beside a large park gains little. Changes every score and D14: for the owner to decide after seeing the map without the parks' scores | idea |

## Phase 3: more places

| Item | Status |
| --- | --- |
| Across-cities scale: GHS Urban Centre Database, global datasets, published city rankings | idea |
| Global-tier baseline map for any city; more country adapters, open to contributors | idea |
| Drill-down from country to city to neighbourhood | idea |
| Street-photo and text-derived indicators for hard-to-measure factors (ML, LLM) | idea |
| Finer air quality, noise and rent by ML downscaling | idea |
| Localisation: currencies, units, UI languages | idea |
| Your industry across cities: industry specialisation, firms, institutions, credible rankings | idea |
| Climate for the across-cities scale: sunshine duration, daylight, wind, rain, temperature ranges | idea |

## Phase 4: product

| Item | Status |
| --- | --- |
| API + PostGIS, accounts, preference profiles saved across devices | idea |
| Routing service for exact door-to-door times, buses included | idea |
| A progressive web app, then native apps | idea |
| Plain-language input and grounded area summaries (LLM, free options first) | idea |
| Privacy policy, terms, and a review of how sensitive data is shown | idea |
| A paid edition, if wanted (AGPL-3.0 with the CLA keeps this possible) | idea |
| Analytics and a "this score looks wrong" feedback button | idea |
| Licensed ratings data for food quality, e.g. OpenRice in Hong Kong | idea |

## Project setup

| Item | Status | When |
| --- | --- | --- |
| CLA text and the CLA Assistant check | planned | Before the first outside contribution is merged |
| Markdown link check and markdownlint in CI, as scripts in the repo (earlier pull requests ran them from a session's scratchpad) | idea | After the scaffold |

## Not now

| Item | Revisit when |
| --- | --- |
| Property listings or live market data | A listings partner or open API exists |
| User accounts | Users need their preference profiles on several devices |
| Exact door-to-door routing for a user's own places | A routing service exists (Phase 4) |
| Native mobile apps | The web app works well on phones |
| Within-city maps outside London | Phase 3, once the region recipe is proven |
| Forecasts (prices, gentrification) | Trend data is in place |
| A satellite basemap (D23) | A source with street-level detail and a licence that allows this use turns up; EOX's Sentinel-2 cloudless is too coarse, and Esri's free terms are for OpenStreetMap editing |

## Dropped

| Item | Why | Date |
| --- | --- | --- |
| Weights learnt from pairwise choices ("which of these two areas do you prefer?") | Few users know enough areas well to compare them reliably | 2026-10-23 |
