# Decision register

The living list of project decisions. Each entry holds the current choice and why, the alternatives considered, when to revisit it, a status and a dated history. To change a decision, edit its entry in place and add a history line. Git keeps the earlier text.

## Statuses

- **proposed:** stands unless challenged. Phase 0 work may confirm or change it.
- **accepted:** settled.
- **revisit:** under review, with a reason.
- **replaced:** superseded. The entry names its successor.

## Index

| ID | Decision | Current choice | Status |
| --- | --- | --- | --- |
| [D01](#d01-first-slice) | First slice | London, within-city scale | accepted |
| [D02](#d02-architecture) | Architecture | Static-first | accepted |
| [D03](#d03-tech-stack) | Tech stack | Kept in tech-stack.md | accepted |
| [D04](#d04-map-grid) | Map grid | H3 resolution 9, 2 km buffer zone, MSOA neighbourhoods | proposed |
| [D05](#d05-factor-structure) | Factor structure | Factor tree with dropdowns | proposed |
| [D06](#d06-scoring-method) | Scoring method | v0 in methodology/scoring.md | proposed |
| [D07](#d07-dataset-licences) | Dataset licences | Public builds: open licences that allow commercial use | proposed |
| [D08](#d08-sensitive-data-and-privacy) | Sensitive data and privacy | Composition as presence and diversity; personal data stays in the browser | proposed |
| [D09](#d09-default-places) | Default places | London's main job centres | proposed |
| [D10](#d10-travel-times) | Travel times | Station matrix + in-browser estimate; engine chosen by spike S4 | proposed |
| [D11](#d11-documentation) | Documentation | Living documents | accepted |
| [D12](#d12-licences) | Licences | Code AGPL-3.0 + CLA; docs CC BY 4.0; data per dataset | accepted |
| [D13](#d13-development-environment) | Development environment | Windows; `E:` on NTFS | accepted |
| [D14](#d14-default-weights) | Default weights | From evidence of what people value | proposed |
| [D15](#d15-llm-use) | LLM use | Free options first | proposed |
| [D16](#d16-scaling) | Scaling | Dataset tiers + region recipe | proposed |
| [D17](#d17-interface) | Interface | Progressive disclosure; visual factor tree as a treemap or a sunburst, one colour per factor | accepted |
| [D18](#d18-preference-types) | Preference types | Fixed, user direction, user range, user choice | proposed |
| [D19](#d19-food-quality) | Food quality | Open signals first | proposed |

## D01 First slice

- **Status:** accepted
- **Choice:** Build the within-city scale first, for London.
- **Why:** UK and London open data are unusually rich. National datasets include Police.uk, Census 2021, HM Land Registry, DEFRA, the Environment Agency and Ofcom. London adds PTAL, the London Atmospheric Emissions Inventory and the London Datastore.
- **Alternatives considered:**
  - The across-cities scale first: harmonised global datasets exist, but city-level cost of living is a major open-data gap.
  - Both scales thinly: neither would support a real decision.
- **Revisit when:** The London spikes (S1–S8) show that key datasets are unusable.
- **History:**
  - 2026-10-23: accepted in the Phase 0 planning session.

## D02 Architecture

- **Status:** accepted
- **Choice:** Static-first. An offline data pipeline (Python) precomputes measured indicators and publishes one data bundle per region as static files. The web app scores everything in the browser.
- **Why:**
  - Most datasets change yearly or monthly, so precomputing them costs little.
  - Scoring about 15,000 hex cells in the browser takes milliseconds, so sliders respond at once.
  - Hosting static files is free.
  - Personal data never needs to leave the browser.
- **Alternatives considered:**
  - A Python-only prototype (Streamlit or Panel): fastest first map. But every slider change runs on a server, the interface has a low ceiling, and a public app would need a rewrite.
  - Full-stack from day one (FastAPI + PostGIS + React): ready for accounts and server routing. But it means running and paying for a database and an API before any user needs them.
- **Revisit when:** Accounts, exact routing for each user, or a region too large for the browser become necessary (Phase 4).
- **History:**
  - 2026-10-23: accepted in the Phase 0 planning session.

## D03 Tech stack

- **Status:** accepted
- **Choice:** As recorded in [tech-stack.md](tech-stack.md), with each tool's reasons and alternatives.
- **Revisit when:** A tool is added, swapped or upgraded. Record the change in tech-stack.md, and here as well if it is large.
- **History:**
  - 2026-10-23: accepted in the Phase 0 planning session.

## D04 Map grid

- **Status:** proposed
- **Choice:**
  - Score H3 resolution 9 hex cells: about 0.1 km² and 350 m across each, and about 15,000 for Greater London.
  - Compute measured indicators over the region plus a 2 km buffer zone.
  - Name areas with MSOAs, using the House of Commons Library's readable names.
- **Why:**
  - Cells of equal size avoid the distortions of odd-shaped administrative boundaries.
  - H3 is hierarchical, so coarser levels serve zoomed-out views, and it covers the globe.
  - The buffer zone stops edge effects.
  - MSOAs give people names they recognise.
- **Alternatives considered:**
  - Administrative areas only: their sizes are unequal, and results change with the boundaries chosen.
  - Resolution 8: about 0.7 km² per cell, too coarse for streets.
  - Resolution 10: about 100,000 cells for London, heavier for little gain.
- **Revisit when:** Spikes S1 and S5 show that the grid misrepresents key datasets, or the browser struggles.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.

## D05 Factor structure

- **Status:** proposed
- **Choice:** Factors form a tree. Top-level factors split into sub-factors, down to measured indicators. Every composite factor has its own weight, and its sub-factors open in a dropdown.
- **Why:** Most factors decompose: travel time, for instance, is the walk, the wait, the ride and the changes. A tree lets users fine-tune only where they care.
- **Alternatives considered:** A flat list of factors, which would be either too coarse or overwhelming.
- **Revisit when:** The factor explorer (step 0.2) shows that the tree is hard to use.
- **History:**
  - 2026-10-23: proposed after review asked for decomposition beyond travel time.

## D06 Scoring method

- **Status:** proposed
- **Choice:** Scoring method v0 in [methodology/scoring.md](methodology/scoring.md):
  - scoring curves with stated thresholds
  - weighted means up the factor tree
  - hard limits applied first
  - missing data renormalised and flagged through data coverage
  - score contributions that add up to the livability score
- **Why:** Every step is transparent and testable. Scores stay comparable across regions wherever the measured indicators are.
- **Alternatives considered:**
  - Percentile ranks everywhere: scores become relative to each region.
  - A weighted geometric mean: kept as a later "no weak spots" mode.
  - An ML model of livability: there is no ground truth to train on.
- **Revisit when:** Step 0.5 finalises the method with golden test cases.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-23: notation rewritten after review, with a symbols table, rendered formulas and a worked example. One rule added: a composite factor whose children all have weight 0 counts as weight 0, so it does not lower data coverage.
  - 2026-10-24: the rising or falling curve is named a ramp, the name the factor catalogue uses for it.

## D07 Dataset licences

- **Status:** proposed
- **Choice:** Public builds use only datasets whose licences allow redistribution and commercial use, with attribution. The allowed list, by SPDX licence id:
  - the Open Government Licence: `OGL-UK-1.0`, `OGL-UK-2.0`, `OGL-UK-3.0`
  - Creative Commons: `CC-BY-3.0`, `CC-BY-4.0`, `CC-BY-SA-3.0`, `CC-BY-SA-4.0`, `CC0-1.0`
  - `ODbL-1.0`, `CDLA-Permissive-1.0`, `CDLA-Permissive-2.0` and `Apache-2.0`
  - TfL's open data licence, `LicenseRef-TfL-Open-Data`: version 2.0 of the Open Government Licence with TfL's amendments, which SPDX does not list

  Datasets under non-commercial licences (e.g. Ookla's speed tests), restrictive terms (e.g. ratings platforms) or a licence not yet confirmed may appear only in local builds, flagged in the factor catalogue. The catalogue's checks enforce this: a dataset marked for public builds needs a licence from the list, the date it was checked at the source, and its attribution ([catalogue/README.md](../catalogue/README.md#datasetsyaml)).
- **Why:** A public site redistributes the data it shows, and a paid edition must stay possible.
- **Revisit when:** A restricted dataset is worth licensing. It then moves to the allowed list under its new licence.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-24: the examples became an allowed list of SPDX ids, enforced by the factor catalogue's checks. A dataset whose licence is not yet confirmed stays out of public builds, as the London Atmospheric Emissions Inventory does until the GLA confirms its licence.
  - 2026-10-24: TfL's open data licence joined the allowed list. It allows commercial use and redistribution with attribution. Its amendments add registration for live feeds and a rate limit, and TfL may revise it without notice, so it is checked again before each public build.

## D08 Sensitive data and privacy

- **Status:** proposed
- **Choice:**
  - Community composition from Census 2021 (ethnicity, religion, country of birth, main language, life stage) is included, with a default weight of 0. It is framed as presence of a group the user chooses, and as diversity, never as "fewer of group X".
  - Crime is shown as rates, with notes on reporting.
  - Deprivation is a context layer, not a default-weighted factor.
  - A user's places and preference profile stay in their browser. A shared link leaves places out unless the user includes them.
- **Why:**
  - Being near one's community, or wanting a mixed area, is a common and legitimate need. The framing serves it and keeps a public site defensible.
  - Places reveal home and work, so they must not leave the user's device.
- **Revisit when:** Before any wider launch, review how sensitive data is shown. Before accounts exist, write a privacy policy.
- **History:**
  - 2026-10-23: first proposed with demographic composition excluded. In review it was included, framed as presence and diversity.

## D09 Default places

- **Status:** proposed
- **Choice:** Until a user adds their own places, travel time uses the average door-to-door time to London's main job centres: the City (Bank), the West End (Oxford Circus), Canary Wharf and King's Cross. Each region defines its default places in `catalogue/regions/<region>.yaml`.
- **Why:**
  - Every user gets a meaningful travel factor, and these centres reflect typical commutes.
  - Default places are public, so their travel times can go into public builds.
- **Revisit when:** Employment data suggests a different set of centres.
- **History:**
  - 2026-10-23: proposed after review asked for a default when no places are set.

## D10 Travel times

- **Status:** proposed; the engine stays open until spike S4
- **Choice:**
  - Default places get exact travel times, computed in the data pipeline.
  - A user's own places (up to 3) get an estimate computed in the browser: the walk to a nearby station, then a precomputed station-to-station travel-time matrix, then the walk to the place. Places never leave the device.
  - The engine is r5py with GTFS timetables, or the TfL Journey Planner API if the timetable conversion fails.
- **Why:** In a static-first app, the data pipeline cannot precompute every user's places.
- **Known limits:** Buses are not in the matrix, so bus-only trips come out too long. Estimates carry the evidence type "estimate".
- **Revisit when:** Spike S4 reports the estimate's error and picks the engine. Exact routing arrives with a routing service (Phase 4).
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.

## D11 Documentation

- **Status:** accepted
- **Choice:**
  - Living Markdown documents in `docs/`, indexed in [README.md](README.md).
  - Decisions are recorded in this register and edited in place, with dated history.
  - The codemap is generated from per-directory READMEs once the tree passes about 100 files.
- **Why:** The documents carry the project's memory between sessions and for new contributors.
- **History:**
  - 2026-10-23: accepted in the Phase 0 planning session. At the owner's request, this living register replaced fixed architecture decision records.

## D12 Licences

- **Status:** accepted
- **Choice:**
  - Code: AGPL-3.0, with a contributor licence agreement (CLA) for outside contributions.
  - Documentation: CC BY 4.0.
  - Data bundles: each dataset's own licence, e.g. ODbL for data derived from OpenStreetMap.
- **Why:** The project is open source now, with the option of a paid edition later. AGPL-3.0 stops anyone from hosting a closed, modified copy. The CLA keeps the owner's right to offer a paid edition.
- **Alternatives considered:** Apache-2.0 or MIT. Both are easier for companies to adopt, but anyone could build a closed paid product from the code.
- **History:**
  - 2026-10-23: accepted in the Phase 0 planning session.

## D13 Development environment

- **Status:** accepted
- **Choice:**
  - Windows, with PowerShell and Git Bash. The repo lives on `E:`, formatted NTFS.
  - Python 3.13 managed by uv in `pipeline/.venv`, separate from conda.
  - npm for the web app, and just for commands.
  - `PYTHONUTF8=1` is set, and `UV_CACHE_DIR` points to `E:`.
- **Why:** NTFS provides the links, ownership records and journal that the tools need.
- **History:**
  - 2026-10-23: `E:` was found to be exFAT, which has no symlinks, hard links, ownership records or journal. The owner reformatted it to NTFS the same day, and the move was verified.

## D14 Default weights

- **Status:** proposed
- **Choice:** Default weights come from evidence of what people value. There are two kinds of source:
  - established livability frameworks: the OECD Better Life Index, the EIU Global Liveability Index, Mercer Quality of Living and the AARP Livability Index
  - surveys of why people move home, e.g. the English Housing Survey

  Factors that appear in most sources start higher. Community composition starts at 0, and the supporting factors start low. The factor catalogue records each default with its reason, and users change weights in the app.
- **Why:** Defaults only need to be a sensible starting point, and evidence makes them defensible for any user.
- **History:**
  - 2026-10-23: first proposed as importance ratings by the first user. In review it changed to evidence-based defaults that users adjust in the app.

## D15 LLM use

- **Status:** proposed
- **Choice:**
  - Pipeline jobs run on a local open-weight model under Apache-2.0, pinned so that results reproduce.
  - Plain-language input in the app uses an in-browser model plus bring-your-own-key. The output is constrained to the preference-profile JSON Schema.
  - Free API tiers are used only behind a rate-limited proxy.
  - The Claude API is a paid quality option once there is revenue.
- **Why:** Free and private options cover the needs, and schema-constrained output lets even small models produce valid profiles.
- **Revisit when:** Phase 4, since free tiers change often.
- **History:**
  - 2026-10-23: proposed after review asked for free options.

## D16 Scaling

- **Status:** proposed
- **Choice:**
  - Each sub-factor lists dataset options by tier: city, then country, then global. A new region uses the best tier available, so every city gets a baseline from global datasets.
  - Each measured indicator is marked comparable across regions or not.
  - Adding a region takes a region file plus a country adapter, if one is missing.
  - Regions build and serve independently, as one data bundle each behind a CDN.
- **Why:** London becomes the first region, not a special case.
- **Revisit when:** The second city is built (Phase 3).
- **History:**
  - 2026-10-23: proposed after review asked how to scale to more cities and countries.

## D17 Interface

- **Status:** accepted
- **Choice:**
  - Progressive disclosure in five layers: map, quick look, why this score, inside a factor, evidence.
  - Preferences are set in a visual factor tree whose areas follow the weights. It offers both layouts, a treemap and a sunburst, with a switch between them. The treemap shows first.
  - Each factor has its own colour, from the categorical palette of the Salt design system. The interface itself stays in ink, so colour always means data.
  - Details are in [interface.md](interface.md).
- **Why:** Users see the answer first and are not flooded with detail. Sizes that follow the weights show at a glance how much each factor counts. The owner tried both layouts in the factor explorer and found each useful. The treemap shows first because rectangles show shares more faithfully than rings, and hold more labels.
- **Revisit when:** Testing in Phase 1 shows that one layout is rarely used, or that colour by factor confuses.
- **History:**
  - 2026-10-23: proposed after review asked for layered details and a visual, interactive factor list.
  - 2026-10-24: accepted after the owner tried the factor explorer. Both layouts stay, with a switch, and each factor has its own colour.

## D18 Preference types

- **Status:** proposed
- **Choice:** Each measured indicator has one of four preference types:
  - fixed: everyone agrees, e.g. PM2.5
  - user direction: a "more ↔ less" switch, e.g. rain or nightlife
  - user range: an ideal band, e.g. temperature
  - user choice: a picker, e.g. industry or cuisines

  Defaults come from evidence, such as the more common preference or a comfort band. Choice factors start at weight 0.
- **Why:** Some factors have no universal "better": some people like rain, and others want none.
- **History:**
  - 2026-10-23: proposed after review raised rainfall as an example.

## D19 Food quality

- **Status:** proposed
- **Choice:**
  - Taste enters as a user choice of cuisines.
  - Quality comes from open signals: choice of restaurants, cuisine variety, food hygiene ratings (UK Food Standards Agency), Michelin recognition recorded in Wikidata, and the share of independents.
  - Ratings platforms (Google, Yelp, Tripadvisor, OpenRice, Tabelog, Dianping) are used only under a licence.
- **Why:** No open dataset rates restaurants, and the platforms' terms forbid storing their data.
- **Revisit when:** Spike S8 has tested the open signals, or a ratings platform offers an affordable licence.
- **History:**
  - 2026-10-23: proposed after review asked how to measure restaurant quality and taste.
