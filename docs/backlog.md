# Backlog

Features to add, grouped by target phase. Each item has a status: idea, planned, in progress or done. Link a spec once one exists. Work for Phase 0 and Phase 1 is tracked in the [roadmap](roadmap.md).

## Phase 2: depth and trust

| Item | Status |
| --- | --- |
| Place and street names drawn above the hex cells. deck.gl's interleaved mode does it but fails against MapLibre 6 (deck.gl 9.4); retry when deck.gl supports MapLibre 6, or draw a labels-only copy of the basemap above the cells | idea |
| More factors, in catalogue priority order | planned |
| Crime rates per resident and worker, so that centres with few residents and many workers, like the City of London, stop topping every crime ([spike S2](spikes/S2-crime.md)). Needs a workplace population table whose licence and geography are checked | idea |
| Presets, e.g. a renter commuting to the centre, a family with children, a retiree | idea |
| Preference profiles as shareable URLs, with places left out unless the user includes them | idea |
| Side-by-side comparison of two hex cells or neighbourhoods | idea |
| "No weak spots" scoring mode (weighted geometric mean) | idea |
| Sensitivity view: how stable the top 10 stays when weights shift ±20% | idea |
| Scoring curves that users can edit | idea |
| "Areas like X" search (ML) | idea |
| Price and rent models, and value for money (ML) | idea |
| Area types by clustering (ML) | idea |
| Scheduled data refresh with anomaly checks (ML) | idea |
| Buses in the travel-time estimate; cycling, step-free and night-time travel; jobs within 45 min | idea |
| Personal notes layer: users rate places they have visited, stored in the browser | idea |
| Destinations: the user picks public places or chains, e.g. Costco, IKEA or the nearest airport, and each is scored by distance to the nearest one. Starts as straight-line distance computed in the browser from a small points file per destination (brand tags, checked in spike S6); later car and public-transport times | idea |
| Your industry: jobs in a chosen industry within reach | idea |
| Brand presence: brand groups checked against data | idea |
| "Why we differ" view against published rankings | idea |
| Known facts and relations as a data file in the catalogue, once a second city shows which shapes repeat (today they are code in `datasets/cities/<region>/facts.py`, [spec](specs/2026-10-29-qa-report.md)) | idea |
| The QA report in the app's "About the data", with the version and the date of each dataset | idea |

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

## Dropped

| Item | Why | Date |
| --- | --- | --- |
| Weights learnt from pairwise choices ("which of these two areas do you prefer?") | Few users know enough areas well to compare them reliably | 2026-10-23 |
