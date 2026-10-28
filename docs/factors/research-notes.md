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

## The MVP candidates

All nine MVP candidates are researched. Their measured indicators are in `catalogue/factors.yaml`, their datasets in [datasets.yaml](../../catalogue/datasets.yaml), and each has a spec in [docs/specs/](../specs/). What the research found about licences:

- Most datasets are under the Open Government Licence.
- OpenStreetMap is under ODbL, Overture Places under three open licences by source, and TfL's data under TfL's own licence, which D07 accepts.
- Three datasets need the owner's checks before a public build: the London Atmospheric Emissions Inventory and Defra's background maps, for air quality, and Price Paid Data, for buying cost.

Non-commercial datasets, such as Ookla's speed tests, never go into public builds (D07).

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

## Natural hazards: the sub-factor still to research

The [Natural hazards research](../specs/2026-10-25-natural-hazards-research.md) left subsidence as an idea, outside the MVP. The British Geological Survey's GeoSure maps ground movement hazards, but it is licensed commercially, so an open alternative or a licence is needed first.

## Daily amenities: the sub-factors still to research

The [Daily amenities research](../specs/2026-10-25-daily-amenities-research.md) left these as ideas, outside the MVP. Their signals are in [hard-to-measure.md](../methodology/hard-to-measure.md).

| Sub-factor | Leads |
| --- | --- |
| Your cuisines | A count of the restaurants serving the cuisines a user picks, from OpenStreetMap's cuisine tags (spike S8) |
| Guide recognition | Michelin recognition recorded in Wikidata (CC0) |
| Independent restaurants | The share of restaurants without a brand tag in OpenStreetMap and Overture (spike S8) |
| Brand presence | Shopping centres, brand variety and brand groups, from brand tags (spike S8) |
| Destinations | The walk or travel time to places a user picks, planned for Phase 2 |
| Cuisine variety across cities | The variety of cuisines in a whole city, for the across-cities scale |

GP access, which the MVP row once listed here, belongs to Health care.

## Education: the sub-factors still to research

The [Education research](../specs/2026-10-25-education-research.md) left nurseries and school league tables as ideas, outside the MVP, and the definition of an inspection that meets the standard open. The leads, with their licences still to check:

| Sub-factor | Leads |
| --- | --- |
| Nurseries | Ofsted's records of childcare providers and their inspections |
| School league tables | The Department for Education's school performance tables, such as results at the end of primary and secondary school |

## Community and people: the sub-factors still to research

The [Community and people research](../specs/2026-10-25-community-research.md) left community life as an idea, outside the MVP. The leads, with their licences still to check:

| Sub-factor | Leads |
| --- | --- |
| Community spaces | Community centres and halls in OpenStreetMap and Overture |
| LGBTQ+-friendly venues | Venues tagged in OpenStreetMap; the tags' completeness needs a check, as for spike S8 |
| Local election turnout | Results published by London Elects and by councils |
| How long residents stay | Census 2021's counts of residents who lived at another address a year before |

## Transport: the sub-factors still to research

The MVP rows moved into the catalogue with the [Transport research](../specs/2026-10-24-transport-research.md). Two sub-factors remain for later:

| Sub-factor | Measured indicator | London dataset |
| --- | --- | --- |
| Night and step-free travel | Night services within a walk; the nearest step-free station | TfL |
| Cycling | Protected lanes, cycle-hire docks, slope | TfL Cycle Infrastructure Database, OpenStreetMap, elevation data |

Outside London, the Bus Open Data Service (BODS) publishes bus timetables for England. It becomes the country-tier dataset for bus routes when a second English city is added.

## Health care: the sub-factors still to research

The [Health care research](../specs/2026-10-28-health-care-research.md) researched GP access and the distance to A&E, and left two sub-factors as ideas. The leads, with their licences still to check:

| Sub-factor | Leads |
| --- | --- |
| Dentists | NHS England's list of dental practices (in the ODS, already in the catalogue) gives where practices are. Whether they take new NHS patients is not published as open data: the NHS Business Services Authority says it does not record it, and its open data holds no file for it. The NHS's Find a Dentist service shows it practice by practice. A map of practices alone would mislead |
| Health-care quality and cost | For the across-cities scale: the OECD and EIU health indicators, and the other published rankings, which wait for Phase 3 |

Other leads outside the MVP: hospital waiting times by trust, and the NHS's own GP Patient Survey, which would add how patients rate their access to a practice (a perception measure, labelled as such).

## Catalogue fields still to come

The [catalogue format](../specs/2026-10-24-catalogue-format.md) added the fields that the Phase 0 plan listed, except three for each dataset: its update cadence, its access method and its cost. They arrive when the data pipeline starts fetching datasets.
