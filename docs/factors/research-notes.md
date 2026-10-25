# Research notes

Starting points for the rest of step 0.2, carried over from the approved Phase 0 plan. Each section moves to its home when its task is done, into `catalogue/datasets.yaml`, `docs/factors/rankings.md` or `docs/methodology/hard-to-measure.md`. Delete a section once it has moved.

## What some datasets can tell us

For the bottom-up pass.

| Dataset | What can be dug out of it |
| --- | --- |
| Census 2021 (ONS) | Age profile, household types, renters versus owners, car-free households, how people commute, ethnicity, religion, country of birth, main language, qualifications, self-reported health, students |
| HM Land Registry Price Paid | Median price, price per m² (with EPC floor areas), 5-year price trend, sales volume, new-build share, flats versus houses |
| Police.uk | Crime by category, trend, monthly pattern, share of cases resolved |
| OpenStreetMap and Overture | Amenities by type, cuisine variety, places of worship by faith, pubs and nightlife, cycle lanes, parks, street trees |
| EPC register | Home size, energy rating, building age, heating type, likely damp or cold homes |
| TfL data | Stations, lines, PTAL, fare zones, step-free access, night services |

## Likely datasets for the MVP candidates

Transport, Environment, Safety, and Housing and cost have moved into the catalogue. The rows below are still to research.

| Top-level factor | Sub-factors | Likely datasets |
| --- | --- | --- |
| Daily amenities | Everyday amenities and restaurants within a 10-minute walk; cuisine variety; food hygiene | Overture Places, Foursquare Open Source Places or OpenStreetMap; NHS GP list; Food Standards Agency |
| Community and people | Community composition; places of worship by faith | Census 2021 through ONS and Nomis; OpenStreetMap |
| Natural hazards | Flood risk | Environment Agency |
| Digital connectivity | Full-fibre availability, 5G coverage | Ofcom Connected Nations, whose resolution is still to be checked |
| Education | Nearby schools by phase and inspection outcome | DfE GIAS and Ofsted. Ofsted dropped single-word grades in 2024, so "rating" needs a new definition |

Most of these datasets are expected to be under the Open Government Licence. There are three exceptions:

- OpenStreetMap is under ODbL.
- Overture Places is under CDLA-Permissive-2.0.
- TfL data must carry the line "Powered by TfL Open Data".

Non-commercial datasets, such as Ookla's speed tests, never go into public builds (D07).

Each licence still needs checking at the source. The London Atmospheric Emissions Inventory, for one, gives its licence as "Not Specified" ([datasets.yaml](../../catalogue/datasets.yaml)).

## Environment: the sub-factors still to research

The [Environment research](../specs/2026-10-25-environment-research.md) left three sub-factors as ideas, outside the MVP. These are leads, with their licences still to check:

| Sub-factor | Leads |
| --- | --- |
| Tree canopy cover | A threshold from the "3-30-300" rule, which asks for 30% canopy cover in every neighbourhood. Data from ESA WorldCover (global) or Forest Research's map of trees outside woodland (England) |
| Water nearby | OS Open Rivers and OpenStreetMap, for the walk to a river, canal or lake |
| Urban heat | Land surface temperature from satellites, scored as a percentile within the region, since no standard threshold exists for it |

## Safety: the sub-factor still to research

The [Safety research](../specs/2026-10-25-safety-research.md) left road collisions as an idea, outside the MVP. The lead is the Department for Transport's road safety data (STATS19), which records each reported collision that injured someone, with its location. Its licence is still to check.

## Housing and cost: the sub-factor still to research

The [Housing and cost research](../specs/2026-10-25-housing-research.md) left home energy efficiency as an idea, outside the MVP. The lead is the energy certificates already in `datasets.yaml`, whose energy ratings are open when certificates are located by UPRN.

## Transport: the sub-factors still to research

The MVP rows moved into the catalogue with the [Transport research](../specs/2026-10-24-transport-research.md). Two sub-factors remain for later:

| Sub-factor | Measured indicator | London dataset |
| --- | --- | --- |
| Night and step-free travel | Night services within a walk; the nearest step-free station | TfL |
| Cycling | Protected lanes, cycle-hire docks, slope | TfL Cycle Infrastructure Database, OpenStreetMap, elevation data |

Outside London, the Bus Open Data Service (BODS) publishes bus timetables for England. It becomes the country-tier dataset for bus routes when a second English city is added.

## Credibility of published rankings

Each published ranking gets a credibility rating of high, medium or low. The rating weighs six questions:

- Is the method published?
- How much data is behind it?
- Is the publisher independent? An estate agent, for example, is not.
- Is it recent?
- Does it cover our places?
- Does its licence let us store it?

Many rankings are proprietary. For those, store only the rank and a citation, and keep them out of public builds unless the licence allows more (D07).

## Culture: the evidence ladder

| Kind of evidence | Culture example | Evidence type |
| --- | --- | --- |
| Direct counts | Cultural venues within a 15-minute walk: theatres, music venues, galleries, cinemas, libraries (GLA Cultural Infrastructure Map) | direct |
| Access | Cultural venues within 30 minutes by public transport | direct |
| Variety | The number of distinct cuisines nearby | indirect |
| Character | Listed buildings and conservation areas (Historic England) | indirect |
| Activity | Event listings; geotagged Wikipedia articles and their page views | indirect |
| Perception, by ML | Street-level photos rated for liveliness and beauty; area descriptions tagged by an LLM | perception |
| Published rankings | Time Out neighbourhood lists, Sunday Times Best Places to Live | ranking |
| A user's own ratings | A personal notes layer, stored in the browser | the user's own |

The same ladder applies to other factors that are hard to measure, such as community life or feeling safe. Spike S7 tests it.

## Food and drink: quality signals

| Kind of evidence | Example | Dataset and licence | Evidence type |
| --- | --- | --- | --- |
| Choice | Restaurants and cafés within a 10-minute walk | OpenStreetMap, Overture, Foursquare Open Source Places | direct |
| Variety | The number of distinct cuisines nearby | OpenStreetMap cuisine tags | indirect |
| Your cuisines | Restaurants serving the cuisines a user picks | OpenStreetMap cuisine tags | direct |
| Hygiene | Food hygiene ratings of nearby restaurants | UK Food Standards Agency (open; country tier) | direct for hygiene, indirect for quality |
| Guide recognition | Michelin stars and Bib Gourmand, the Good Food Guide, The World's 50 Best | Wikidata (CC0) records the Michelin stars of many restaurants, though not all. The guides themselves are proprietary, so keep only counts and a citation | ranking |
| Independents | The share of restaurants that are not chains | OpenStreetMap and Overture brand tags | indirect |
| Ratings and reviews | Average rating and review count | Google, Yelp, Tripadvisor, OpenRice (Hong Kong), Tabelog (Japan), Dianping (China). Their terms forbid storing the data or require a partnership | perception |

Build from the open rows first. Treat each country's ratings platform as a country-tier dataset that needs a licence. Until it has one, ratings stay out of public builds (D07, D19). Spike S8 tests the open signals.

## Brand presence: shopping centres and brand groups

| Signal | Measured indicator | Example |
| --- | --- | --- |
| Shopping centres | The size of the shopping centres within reach | Westfield London, Westfield Stratford City |
| Brand variety | Distinct national and international chains within a 15-minute walk | |
| Brand groups | Brands grouped by what their choice of sites signals: premium, high footfall, large catchment, value | Premium: Gail's, Waitrose. High footfall: Pret, Starbucks. Large catchment: Costco, IKEA. Value: Aldi, Lidl |

Brand groups are listed per country. Each brand's group is checked against data before use, for example whether its presence tracks house prices, and brands that show no pattern are dropped. Brand presence partly mirrors house prices, so it gets a low default weight. Spike S8 checks how complete brand tags are for London.

## Your industry, across cities

An industry's strength in a city combines four signals:

- industry specialisation: the industry's share of local jobs, compared with its share worldwide
- its firms and headquarters, from Wikidata
- its flagship institutions and events
- credible rankings of the industry

## Catalogue fields still to come

The [catalogue format](../specs/2026-10-24-catalogue-format.md) added the fields that the Phase 0 plan listed, except three for each dataset: its update cadence, its access method and its cost. They arrive when the data pipeline starts fetching datasets.
