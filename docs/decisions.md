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
| [D04](#d04-map-grid) | Map grid | H3 resolution 9, 2 km buffer zone, MSOA neighbourhoods | accepted |
| [D05](#d05-factor-structure) | Factor structure | Factor tree with dropdowns | accepted |
| [D06](#d06-scoring-method) | Scoring method | v0 in methodology/scoring.md | accepted |
| [D07](#d07-dataset-licences) | Dataset licences | Public builds: open licences that allow commercial use | accepted |
| [D08](#d08-sensitive-data-and-privacy) | Sensitive data and privacy | Composition as presence and diversity; personal data stays in the browser | accepted |
| [D09](#d09-default-places) | Default places | London's main job centres | proposed |
| [D10](#d10-travel-times) | Travel times | Station matrix + in-browser estimate, with a walk or a bus to and from the stations; the matrix from TfL's timetables now, r5py later | accepted |
| [D11](#d11-documentation) | Documentation | Living documents | accepted |
| [D12](#d12-licences) | Licences | Code AGPL-3.0 + CLA; docs CC BY 4.0; data per dataset | accepted |
| [D13](#d13-development-environment) | Development environment | Windows; `E:` on NTFS | accepted |
| [D14](#d14-default-weights) | Default weights | From evidence of what people value | accepted |
| [D15](#d15-llm-use) | LLM use | Free options first | proposed |
| [D16](#d16-scaling) | Scaling | Dataset tiers + region recipe | proposed |
| [D17](#d17-interface) | Interface | Progressive disclosure; visual factor tree as a treemap or a sunburst, one colour per factor | accepted |
| [D18](#d18-preference-types) | Preference types | Fixed, user direction, user range, user choice | accepted |
| [D19](#d19-food-quality) | Food quality | Open signals first | accepted |
| [D20](#d20-agent-rules) | Agent rules | One rule file, `CLAUDE.md`, bridged to other agents by `AGENTS.md` | accepted |
| [D21](#d21-mvp-factor-set) | MVP factor set | The nine top-level factors already researched, and Health care as a tenth | accepted |
| [D22](#d22-a-score-describes-the-homes-in-a-cell) | A score describes the homes in a cell | A hex cell with fewer than 10 homes has no score | accepted |
| [D23](#d23-the-maps-layers) | The map's layers | The colours under the water, roads and names, over the land use; no satellite | accepted |
| [D24](#d24-colour-by-score-or-by-rank) | Colour by score or by rank | The score by default; a legend switch to the rank in the region, in fifths | accepted |
| [D25](#d25-score-by-the-amount-never-by-rank) | Score by the amount, never by rank | A fixed ramp where a standard gives the ends, else a ramp whose ends come from the region's own values; no percentile curve | accepted |

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
  - Scoring about 17,000 hex cells in the browser takes milliseconds, so sliders respond at once.
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

- **Status:** accepted
- **Choice:**
  - Score H3 resolution 9 hex cells: about 0.1 km² and 350 m across each, and about 17,000 for Greater London.
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
  - Resolution 10: about 120,000 cells for London, heavier for little gain.
- **Revisit when:** Spikes S1 and S5 show that the grid misrepresents key datasets, or the browser struggles.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-28: spike S1 counted 16,883 resolution 9 cells under the PTAL contours, which cover Greater London, so "about 15,000" became "about 17,000", and the resolution 10 figure became about 120,000. Neither changes the choice.
  - 2026-10-28: accepted after spikes S1 and S5. TfL's PTAL grid maps to resolution 9 cells, with 16,883 under Greater London and no gap, and averaging at addresses showed no misrepresentation by the grid. Whether the browser keeps up with about 17,000 cells is measured in Phase 1.

## D05 Factor structure

- **Status:** accepted
- **Choice:** Factors form a tree. Top-level factors split into sub-factors, down to measured indicators. Every composite factor has its own weight, and its sub-factors open in a dropdown.
- **Why:** Most factors decompose: travel time, for instance, is the walk, the wait, the ride and the changes. A tree lets users fine-tune only where they care.
- **Alternatives considered:** A flat list of factors, which would be either too coarse or overwhelming.
- **Revisit when:** The factor explorer (step 0.2) shows that the tree is hard to use.
- **History:**
  - 2026-10-23: proposed after review asked for decomposition beyond travel time.
  - 2026-10-28: accepted. The factor explorer (step 0.2) draws the tree, the owner reviewed it and kept both layouts (D17), and ten top-level factors are researched to measured indicators with it.

## D06 Scoring method

- **Status:** accepted
- **Choice:** Scoring method (version 1) in [methodology/scoring.md](methodology/scoring.md):
  - scoring curves with stated thresholds
  - weighted means up the factor tree
  - hard limits applied first
  - missing data renormalised and flagged through data coverage
  - score contributions that add up to the livability score
  - 15 golden test cases in `shared/fixtures/scoring/`, which every engine must reproduce
- **Why:** Every step is transparent and testable. Scores stay comparable across regions wherever the measured indicators are.
- **Alternatives considered:**
  - Percentile ranks everywhere: scores become relative to each region.
  - A weighted geometric mean: kept as a later "no weak spots" mode.
  - An ML model of livability: there is no ground truth to train on.
- **Revisit when:** The web app's engine meets the golden test cases, or a real factor needs a rule that they do not cover.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-23: notation rewritten after review, with a symbols table, rendered formulas and a worked example. One rule added: a composite factor whose children all have weight 0 counts as weight 0, so it does not lower data coverage.
  - 2026-10-24: the rising or falling curve is named a ramp, the name the factor catalogue uses for it.
  - 2026-10-28: accepted as version 1, in step 0.5. The percentile curve, lookups with an unlisted category, hard limits and the meaning of missing data are defined exactly, and 15 golden test cases are committed with a Python reference scorer that reproduces them. The spikes' findings joined the spatial framework: walks along streets, residents shared by area, rates pooled with a floor, and noise averaged at addresses.
  - 2026-11-23: the percentile curve is removed, because a rank hides the amount (D25). A ramp may be on a log scale, and a region ramp takes its thresholds from the region's own values. The golden case `percentile` gives way to `ramp-log`.

## D07 Dataset licences

- **Status:** accepted
- **Choice:** The project is non-commercial for now, so the build uses every dataset it can, with its attribution; any dataset still needs a licence entry. Each dataset is marked `commercial_use`, true only where its licence allows redistribution and commercial use, with attribution, so that a future commercial edition knows what it may keep and what it must pay for or drop. The commercial list, by SPDX licence id:
  - the Open Government Licence: `OGL-UK-1.0`, `OGL-UK-2.0`, `OGL-UK-3.0`
  - Creative Commons: `CC-BY-3.0`, `CC-BY-4.0`, `CC-BY-SA-3.0`, `CC-BY-SA-4.0`, `CC0-1.0`
  - `ODbL-1.0`, `CDLA-Permissive-1.0`, `CDLA-Permissive-2.0` and `Apache-2.0`
  - TfL's open data licence, `LicenseRef-TfL-Open-Data`: version 2.0 of the Open Government Licence with TfL's amendments, which SPDX does not list
  - the Open Parliament Licence v3.0, `LicenseRef-OPL-3.0`, which SPDX does not list

  Datasets under non-commercial licences (e.g. Ookla's speed tests), restrictive terms or a licence not yet confirmed are marked `commercial_use: false` with a note, and are used in the build. `atlas build --commercial` leaves out the indicators built from them. Proprietary data that forbids redistribution, such as the published rankings, is still not copied into bundles: only ranks, with a citation. The catalogue's checks enforce the marking: a dataset with `commercial_use: true` needs a licence from the list, the date it was checked at the source, and its attribution ([catalogue/README.md](../catalogue/README.md#datasetsyaml)).
- **Why:** The owner decided on 2026-10-28 to build everything that is possible now and to pay for licences later, if there is ever a commercial edition, turning what they unlock into paid features. Marking each dataset keeps that edition possible.
- **Revisit when:** A commercial edition is planned, or a restricted dataset is worth licensing. It then moves to the commercial list under its new licence.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-24: the examples became an allowed list of SPDX ids, enforced by the factor catalogue's checks. A dataset whose licence is not yet confirmed stays out of public builds, as the London Atmospheric Emissions Inventory does until the GLA confirms its licence.
  - 2026-10-24: TfL's open data licence joined the allowed list. It allows commercial use and redistribution with attribution. Its amendments add registration for live feeds and a rate limit, and TfL may revise it without notice, so it is checked again before each public build.
  - 2026-10-29: the Open Parliament Licence v3.0 joined the allowed list, for the House of Commons Library's MSOA names. It is the Parliament's counterpart of the Open Government Licence: it allows use in products, commercial use and redistribution with an acknowledgement. I added it on my own judgement, within the owner's delegation, because the alternative was to leave the neighbourhood names out of commercial builds for no reason.
  - 2026-10-28: accepted. The catalogue checks enforce it by SPDX licence id in CI, and every dataset researched since carries its licence check. Four licences are still open (the LAEI, Defra's background maps, the ONS Postcode Directory and OS Code-Point Open), and stay out of public builds until read.
  - 2026-10-28: OS Code-Point Open is confirmed as the Open Government Licence: the OS OpenData licence page redirects to it, and the ONS's page on licences says its postcode products, derived from Code-Point Open, are under it, with three credits (the Ordnance Survey, Royal Mail and the ONS). Public builds use it. Three licences stay open.
  - 2026-10-28: the owner pointed at the London Datastore's air quality page and downloads were allowed. The LAEI 2022 files can be downloaded and are used in local builds, but neither the page nor the dataset page nor the Datastore's terms name a licence ("Not Specified"; the terms let anyone use the data for any lawful purpose and say nothing of redistribution or commercial use). So the LAEI stays out of public builds: `atlas build --public` leaves out the indicators from datasets that are not cleared, which today are NO₂ and PM2.5.
  - 2026-10-28: the owner decided that the project is non-commercial for now. The rule that a public build used only commercially licensed datasets became the marking `commercial_use` (renamed from `public_build`), and the build uses every dataset. Specs and logs written before this date say "public builds" for what is now "commercial builds".

## D08 Sensitive data and privacy

- **Status:** accepted
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
  - 2026-10-28: accepted. The Community and people research follows its framing rules (presence of a group the user chooses, and diversity), and the scoring method keeps a user's profile in the browser. The privacy policy waits for accounts, as it says.

## D09 Default places

- **Status:** proposed; revisit in Phase 1
- **Choice:** Until a user adds their own places, travel time uses the average door-to-door time to London's main job centres: the City (Bank), the West End (Oxford Circus), Canary Wharf and King's Cross. Each region defines its default places in `catalogue/regions/<region>.yaml`.
- **Why:**
  - Every user gets a meaningful travel factor, and these centres reflect typical commutes.
  - Default places are public, so their travel times can go into public builds.
- **Revisit when:** Employment data suggests a different set of centres.
- **History:**
  - 2026-10-23: proposed after review asked for a default when no places are set.
  - 2026-10-28: left proposed at the close of Phase 0. Phase 1's travel milestone builds the default places' times, and employment data may suggest a different set of centres.

## D10 Travel times

- **Status:** accepted
- **Choice:**
  - Default places get exact travel times, computed in the data pipeline.
  - A user's own places (up to 3) get an estimate computed in the browser: the walk to a nearby station, then a precomputed station-to-station travel-time matrix, then the walk to the place. Places never leave the device.
  - The matrix is built now from TfL's own timetables, with a shortest-path search: the Unified API's route sequences and timetables give TfL's lines (the minutes between stops, and the headway from the morning's departures), and one Journey Planner call for each pair of next stops gives National Rail's minutes. Boarding costs 5 minutes from the street plus half the headway and getting off 2 minutes (both fitted to the Journey Planner's times from each station to the default places), and a change to another station within 300 m costs the walk ([spec](specs/2026-11-22-own-places.md)). The app estimates a user's places from it in the browser, with no request: the way from the cell to its 8 quickest stations, the matrix, and the way from a station to the place. The way to a station is the quicker of the street walk and a walk of up to 10 minutes to a bus stop plus a bus, from TfL's bus timetables, within 40 minutes; the default places use the same ways to their stations. The way from a station to the place is the quicker of the straight-line walk and the links of the place's own cell, read backwards ([S9](spikes/S9-buses.md)). r5py with GTFS timetables stays the better engine (exact waits, several departure times), once the owner has registered for its timetable sources and installed a JDK 21. The Journey Planner cannot build the whole matrix: about 745,000 calls take some 200 hours without a key.
- **Why:** In a static-first app, the data pipeline cannot precompute every user's places.
- **Known limits:** On 300 random journeys from cell to cell at three times of day, the estimate is a median 5.5 to 6.0 minutes too long and within 20% in 85 to 87% ([S9](spikes/S9-buses.md); 11 minutes and 70% before the buses, [S4](spikes/S4-routing.md)). It waits half the time between trains or buses at each boarding, where a planned journey leaves in time for one, and it cannot make a journey by bus alone, which was quicker in 10 of S9's 282 journeys. To a central place it is a median 0.99 of the Journey Planner's time. Estimates carry the evidence type "estimate".
- **Revisit when:** r5py can run (exact waits, several departure times), or journeys by bus alone matter more than they did in S9. Exact routing arrives with a routing service (Phase 4).
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-28: accepted after [spike S4](spikes/S4-routing.md). The design stands, r5py is the engine, and the API is the fallback. r5py was not run, because its timetable sources need accounts that only the owner can create.
  - 2026-11-22: the matrix is built from TfL's timetables and the Journey Planner's National Rail times, with a shortest-path search, since the Journey Planner alone would take some 200 hours (my call, within the owner's delegation). r5py stays the later engine.
  - 2026-11-22: the error checked on 300 journeys at 08:30, 12:30 and 18:00: a median 11 minutes too long, within 20% in 70%, from the buses left out ([S4](spikes/S4-routing.md)).
  - 2026-11-24: [spike S9](spikes/S9-buses.md): a walk-and-bus leg at both ends, from TfL's bus routes and timetables without a key, cuts the error on the same journeys to a median 5.5 minutes too long, within 20% in 85%. To be built next, for the default places and a user's places.
  - 2026-11-24: built (bundle `446823cd3071`): the way to and from the stations is a walk or a bus, for the default places and a user's places; a stop's way to a station must ride a bus. The travel check on the new bundle gives S9's numbers: +5.5 minutes at 08:30, within 20% in 85%. 95.0% of cells have a travel time, against 92.2%, and no cell's time grew.

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
- **The start (2026-11-23):** only a few essentials count when a user starts: Renting cost, Walk to the nearest station, Travel time to places, all of Safety, Walk to a green space and Groceries (`starts_counted` in the catalogue). Every other factor starts at "Not counted", one action away, and takes its default weight when counted. "Start from" offers "A few essentials" and "Everything, equally" before the presets ([spec](specs/2026-11-23-start-with-essentials.md)).
- **Why:** Defaults only need to be a sensible starting point, and evidence makes them defensible for any user. A short start keeps the map clear: with all 15 top-level factors counted, the middle 80% of London's hex cells scored within 17 points of each other, because the factors are almost unrelated and each one added pulls every cell to the middle; and people keep what they start with.
- **History:**
  - 2026-10-23: first proposed as importance ratings by the first user. In review it changed to evidence-based defaults that users adjust in the app.
  - 2026-10-28: accepted. The 18 top-level factors' weights are set by how many of the five sources weigh each one, with the mapping and the build order in the [spec](specs/2026-10-28-default-weights.md). Matching a source's own category to one of ours took judgement, which the spec flags; sub-factor weights stay at the engineering default of 3 until their own evidence arrives.
  - 2026-10-30: the owner chose equal defaults: every top-level factor starts at 3, the middle of the 0 to 5 scale, except the two supporting factors (published rankings, resident wellbeing, not built), which stay at 1. The evidence-based weights are kept in the [spec](specs/2026-10-28-default-weights.md) as the reasoning that was set aside. Community composition also starts at 3, so that diversity counts; Your community, a choice, stays at 0 until the user picks a group (D08, D18). Why the owner chose it: the earlier defaults put inner and east London on top, because five of the ten factors measure access and Housing and cost marks the dear boroughs down, and an equal start makes no claim about what matters.
  - 2026-11-23: the owner chose to start with only a few important factors counted, "for example rent, tube, safety", with no question to the user, after asking whether adding factors one by one beats starting with all and removing some. The equal default weights stay as the weight a factor takes when counted. Profiles and links from before keep counting everything.

## D15 LLM use

- **Status:** proposed; revisit in Phase 4
- **Choice:**
  - Pipeline jobs run on a local open-weight model under Apache-2.0, pinned so that results reproduce.
  - Plain-language input in the app uses an in-browser model plus bring-your-own-key. The output is constrained to the preference-profile JSON Schema.
  - Free API tiers are used only behind a rate-limited proxy.
  - The Claude API is a paid quality option once there is revenue.
- **Why:** Free and private options cover the needs, and schema-constrained output lets even small models produce valid profiles.
- **Revisit when:** Phase 4, since free tiers change often.
- **History:**
  - 2026-10-23: proposed after review asked for free options.
  - 2026-10-28: left proposed at the close of Phase 0. LLM jobs start in Phase 3 and plain-language input in Phase 4, and free tiers change often.

## D16 Scaling

- **Status:** proposed; revisit in Phase 3
- **Choice:**
  - Each sub-factor lists dataset options by tier: city, then country, then global. A new region uses the best tier available, so every city gets a baseline from global datasets.
  - Each measured indicator is marked comparable across regions or not.
  - Adding a region takes a region file plus a country adapter, if one is missing.
  - Regions build and serve independently, as one data bundle each behind a CDN.
- **Why:** London becomes the first region, not a special case.
- **Revisit when:** The second city is built (Phase 3).
- **History:**
  - 2026-10-23: proposed after review asked how to scale to more cities and countries.
  - 2026-10-28: left proposed at the close of Phase 0. The second city is built in Phase 3, which tests the tier and region design.

## D17 Interface

- **Status:** accepted
- **Choice:**
  - Progressive disclosure in five layers: map, quick look, why this score, inside a factor, evidence.
  - Preferences are set in a visual factor tree whose areas follow the weights. It offers both layouts, a treemap and a sunburst, with a switch between them. The treemap shows first.
  - Each factor has its own colour, from the categorical palette of the Salt design system, in the factor tree and as a swatch by its name in "Why this score". A score has the colour of its value on one scale, red (worse) → yellow → blue-green (better), on the map, in the legend and in the bars of "Why this score". The interface itself stays in ink, so colour always means data.
  - Details are in [interface.md](interface.md).
- **Why:** Users see the answer first and are not flooded with detail. Sizes that follow the weights show at a glance how much each factor counts. The owner tried both layouts in the factor explorer and found each useful. The treemap shows first because rectangles show shares more faithfully than rings, and hold more labels.
- **Revisit when:** Testing in Phase 1 shows that one layout is rarely used, or that colour by factor confuses.
- **History:**
  - 2026-10-23: proposed after review asked for layered details and a visual, interactive factor list.
  - 2026-10-24: accepted after the owner tried the factor explorer. Both layouts stay, with a switch, and each factor has its own colour.
  - 2026-10-29: the switch is built, as "Boxes" and "Rings" in the app (the treemap and the sunburst are the contributors' words). The boxes still show first. The choice is kept in the browser and not in the link, because it is how the user likes to see the factors and not what they want, so a shared link opens in the recipient's own layout.
  - 2026-11-23: scores are coloured by how good they are, at the owner's request, because a factor named for a bad thing (Crime, Noise) did not say if a high score was good. The map leaves viridis for the same red → yellow → blue-green scale as the bars, so that yellow means "middling" everywhere. The bars of "Why this score" take their score's colour, and the factor's own colour moves to a swatch by its name.

## D18 Preference types

- **Status:** accepted
- **Choice:** Each measured indicator has one of four preference types:
  - fixed: everyone agrees, e.g. PM2.5
  - user direction: a "more ↔ less" switch, e.g. rain or nightlife
  - user range: an ideal band, e.g. temperature
  - user choice: a picker, e.g. industry or cuisines

  Defaults come from evidence, such as the more common preference or a comfort band. Choice factors start at weight 0.
- **Why:** Some factors have no universal "better": some people like rain, and others want none.
- **History:**
  - 2026-10-23: proposed after review raised rainfall as an example.
  - 2026-10-28: accepted. The catalogue's checks require each measured indicator's preference type and an ideal-range curve for a user-range one, and the golden test cases pin flipped directions for every curve shape.
  - 2026-10-29: user choice built ([spec](specs/2026-10-29-user-choice.md)): one column per option, the best of the options picked, a fixed direction, a first pick sets the weight to 3, and choices stay out of shared links (D08).

## D19 Food quality

- **Status:** accepted
- **Choice:**
  - Taste enters as a user choice of cuisines.
  - Quality comes from open signals: choice of restaurants, cuisine variety, food hygiene ratings (UK Food Standards Agency), Michelin recognition recorded in Wikidata, and the share of independents.
  - Ratings platforms (Google, Yelp, Tripadvisor, OpenRice, Tabelog, Dianping) are used only under a licence.
- **Why:** No open dataset rates restaurants, and the platforms' terms forbid storing their data.
- **Revisit when:** A ratings platform offers an affordable licence, or Wikidata's Michelin records become complete.
- **History:**
  - 2026-10-23: proposed after review asked how to measure restaurant quality and taste.
  - 2026-10-28: accepted after spike S8. Hygiene and cuisine variety work for London, independents are a noisy indirect signal, and Michelin recognition in Wikidata is too incomplete to count from (it misses known starred restaurants), so it stays an idea.

## D20 Agent rules

- **Status:** accepted
- **Choice:**
  - `CLAUDE.md` is the one source of rules for every coding agent.
  - `AGENTS.md` at the root is the bridge for other agents, Google Antigravity first. Antigravity always loads a root `AGENTS.md` or `GEMINI.md`, and its documentation does not mention `CLAUDE.md`. So `AGENTS.md` holds the line `@[CLAUDE.md](CLAUDE.md)`, which Antigravity replaces with that file's text. It resolves the path from the folder of the file that holds the line, and caps the result at 24,000 bytes. Any other tool shows the line as a plain link.
  - Beyond the include, `AGENTS.md` holds only a translation of the Claude Code tools that `CLAUDE.md` names, and the rules for two agents sharing a clone.
  - Each nested `CLAUDE.md` gets a sibling `AGENTS.md` made of one such line, because Antigravity loads `AGENTS.md` folder by folder.
- **Why:** One copy of the rules cannot drift. `AGENTS.md` is the file other agents look for, and the owner wants Claude Code and Antigravity to follow the same rules.
- **Alternatives considered:**
  - Copy the rules into `AGENTS.md` or `GEMINI.md`: the two copies would drift.
  - Symlink `AGENTS.md` to `CLAUDE.md`: symlinks need extra rights on Windows, and a third-party report says Antigravity does not follow them.
  - Make `AGENTS.md` the source and have `CLAUDE.md` import it: it rewrites the manual that already works, for no gain.
- **Revisit when:** The owner has run Antigravity in this repo and seen it follow the rules, Antigravity reads `CLAUDE.md` itself, or its include syntax changes.
- **History:**
  - 2026-10-26: proposed after the owner asked for Claude Code and Antigravity to share one set of rules. Built from Antigravity's documentation; not yet run in Antigravity.
  - 2026-10-26: accepted after the owner opened the repo in Antigravity and it saw the whole of `CLAUDE.md`. Antigravity runs only when the owner starts it: it is not a background process of Claude Code.

## D21 MVP factor set

- **Status:** accepted
- **Choice:** The MVP's factor tree holds ten top-level factors: the nine already researched, and Health care, which is researched next with `/research-factor health-care`. The nine are Housing and cost, Transport, Daily amenities, Environment, Natural hazards, Safety, Education, Digital connectivity, and Community and people. [vision.md's MVP success criterion](vision.md#mvp-success-criteria-end-of-phase-1) asks for "about 10".
- **Why:** Each of the nine already has measured indicators, a scoring curve (where S4 and S6 do not block it) and at least one dataset, from step 0.2's research. Health care ties D14's highest weight, is weighed by four of the five sources, and brings the set to the vision's ten. One more run of the research recipe is a small cost, and leaving the factor people weigh most unresearched would be the larger gap.
- **The weight table, and the one gap it shows:**

  | Weight (D14) | Researched | Not researched |
  | --- | --- | --- |
  | 4 | Housing and cost, Environment, Safety, Education | **Health care** |
  | 3 | Transport | Work and economy |
  | 2 | Daily amenities, Community and people | Culture and leisure, Governance and rights |
  | 1 | Natural hazards, Digital connectivity | Climate, Animal friendliness, Urban form and change, Published rankings, Resident wellbeing |

  Health care ties D14's highest weight, with Housing and cost, Environment and Safety, but was not among the nine: the original MVP candidates (`docs/factors/research-notes.md`) were chosen before D14's weights existed. This was the one gap the nine-factor set left at the top of the evidence. The options were:
  - keep the MVP at nine, and research Health care for Phase 2, or
  - add Health care as a tenth MVP factor, and research it with `/research-factor health-care`. Chosen.
- **Alternatives considered:**
  - The top ten factors by weight alone (the five at weight 4, Transport and Work and economy at weight 3, then three of the weight-2 factors): drops three already-researched factors (Natural hazards, Digital connectivity, one of Daily amenities or Community and people) in favour of unresearched ones, for a small weight gain and a larger research cost before step 0.3.
  - All 18 factors in the MVP: against the vision's "about 10", and nine of them have no measured indicators yet.
- **Revisit when:** The owner prefers nine, or Phase 1 planning finds that the ten do not cover a factor well enough to ship.
- **History:**
  - 2026-10-28: proposed, the last item of step 0.2.
  - 2026-10-28: accepted with Health care as a tenth. The owner delegated the decision, so it can be reversed in review.
  - 2026-10-28: frozen in step 0.5, with the [MVP scope](specs/2026-10-28-mvp-scope.md): the ten factors, their weights and all 41 researched measured indicators (32 ship at launch, 5 need a curve, 4 are blocked by a licence or an owner action). From now on, adding or removing a top-level factor from the MVP, or dropping a measured indicator from its scope, needs a record here.

## D22 A score describes the homes in a cell

- **Status:** accepted
- **Choice:** A hex cell's livability score describes the homes in it. A hex cell with fewer than 10 homes is not a place where people live, so it has no score: the map leaves it clear with a thin outline, so that the basemap shows the park, the airport or the industrial estate, and it is not ranked, not in a neighbourhood's mean score, and not among the values that set the ends of a region ramp (D25). The bundle counts the homes in each hex cell (`homes` in `cells.parquet`, and `homes.minimum` in the manifest), and the web app applies the rule. A bundle without the count scores every hex cell, as before.
- **How homes are counted:** in London, the homes with a domestic energy performance certificate (`epc-domestic`), each in the hex cell that holds its postcode's centre. The certificates cover most homes, and a hex cell of housing has dozens or hundreds; 22% of London's hex cells have none, and a hex cell with a few is mostly a park's lodge or a farm.
- **Why:** On the bundle of 2026-11-22, 19% of London's hex cells had no postcode at all (parks, Heathrow, industrial land, reservoirs, railway land). Their median score was 47 against 63 elsewhere, and 70% of them were in the lowest fifth of all scores, so about two thirds of the red on the map was land where nobody lives. They scored low because every walk starts at the hex cell's centre, deep in the park; rates per resident had almost no residents (Hyde Park: 29 violent crimes per 1,000 people, against 15 around it); and values shared from census areas by area gave a park the area's share (Richmond Park: 10% of homes with gigabit broadband, against 73% around it). The rule needs no list of parks or airports, so it works for any region.
- **Alternatives considered:**
  - A list of land uses to mask (parks from OS Open Greenspace, airports): misses industrial land, reservoirs and railway land, and needs a new list per region.
  - Walks from each hex cell's homes rather than its centre: the homes at a park's edge are a median of 48 m from their hex cell's centre, under a minute's walk, so this changes little. In the backlog.
  - Keep the scores and dim the hex cells: the number still misleads.
- **Not decided here:** homes beside a large park gain little, because the measures of what is within a walk (about 30% of the default weight) outweigh the park-related ones (about 7%), and a home beside a park does have less town within a walk. That follows from the equal default weights (D14). Measures that say the same thing sharing their weight (scoring.md, section 10) is in the backlog for the owner to decide.
- **Revisit when:** a commercial edition is built: the certificates' licence is not for commercial use (D07), so a commercial build has no count of homes and scores every hex cell, until another source of homes is chosen (backlog).
- **History:**
  - 2026-11-23: accepted. The owner saw parks, industrial land and airports score badly, and approved this rule and the clear hex cells with an outline.
  - 2026-11-23: the percentile curve is gone (D25); the cells with few homes now stay out of the values that set a region ramp's ends, which the build works out.

## D23 The map's layers

- **Status:** accepted
- **Choice:** The hex cells are drawn inside the basemap, not over it. From the bottom up: the land (the background, buildings, and the land use: parks, woods and grass, industrial and business land, railways, cemeteries), the hex cells, then the water, roads, railways and place names. The roads, the river and the names stay sharp over the colours, so the cells start at 80% opacity, not 50%. A hex cell with few or no homes (D22) has no fill, so the land use under it shows what is there. The land use comes from the basemap's own OpenMapTiles source, in pale greyed tints that stay at ΔE 8 or more from every score colour in normal vision and in red-green colour blindness (`web/src/features/map/colour.ts`). The layer order is worked out from each layer's type and source-layer, not from layer ids (`web/src/features/map/stack.ts`).
- **How:** deck.gl's layers are interleaved with MapLibre's through `@deck.gl/maplibre`, with `beforeId` on each layer. The first try, with `@deck.gl/mapbox`, failed against MapLibre 6. deck.gl adds its layers only while the style counts as loaded, which MapLibre reports only once every tile has loaded, so the app tells deck.gl the style is loaded for the moment it adds them (waiting for the map to be idle left the cells missing on a slow network).
- **Why:** With the cells in a canvas over the whole map, the colours washed over the streets, the Thames and the place names, and a cell with few homes showed only Positron's pale grey: parks were faint, and industrial land and railways were not drawn at all. The owner compared four styles from screenshots at city, district and street zoom (2026-11-23) and chose this one.
- **Alternatives considered:**
  - A satellite basemap. The only free source with no key and a clear licence is EOX's Sentinel-2 cloudless: 10 m pixels, blurry at street zoom, and its recent years are for non-commercial use only. Esri's World Imagery is sharp, but its free terms are for OpenStreetMap editing. And a colour drawn over a photograph changes with what is under it, so the cells stop matching the legend.
  - The same layer order on a grey map with no land use: the cleanest, but a park and an industrial estate look the same.
  - Each cell as a ring in its score colour, with the map clear inside: keeps the most map, but at city zoom the rings blur into noise.
- **Revisit when:** a satellite or aerial source with a clear licence and street-level detail turns up; the same layer order would hold.
- **History:**
  - 2026-11-23: accepted by the owner, after the comparison.

## D24 Colour by score or by rank

- **Status:** accepted
- **Choice:** The map colours its cells by their score, from 0 to 100, as before. A switch in the legend, "Score" and "Rank in London" (the region's name), colours them instead by the fifth of the region each falls in, among the cells that count (with homes, a score, and within the hard limits): each fifth takes one stop of the score scale, from red for the bottom fifth to blue-green for the top. Equal scores share a fifth. The choice is how the user likes to see the map, not what they want, so it is kept in the browser and not in the link, as the factor tree's layout is (D17). In score mode the legend also shows where the region's scores lie (a bar for each twentieth of the scale, ticks at 0, 50 and 100, and "Most of London scores 50 to 70", the middle 80% of the cells), and the map marks the top neighbourhoods' best cells with their places in the list while it shows the livability score.
- **Why:** The Impeccable critique of the map (2026-11-23) found that London's scores bunch between about 50 and 80, so the default map was a yellow-green wash with almost no red and no clear best areas; the first promise is that the map shows the best areas. The owner chose a switch over changing the default.
- **Alternatives considered:**
  - Colour by rank only: shows the spread but loses the absolute score, which the reasons and the quick look still give out of 100.
  - Stretch the scale to the region's spread: the colours would no longer mean the same score in every view, and the legend would need moving numbers.
- **Revisit when:** a second region arrives: "Rank in" names the region, and ranks never compare across regions.
- **History:**
  - 2026-11-23: accepted by the owner, from the critique's questions.

## D25 Score by the amount, never by rank

- **Status:** accepted
- **Choice:** Every scoring curve scores by the amount, never by rank.
  - **A fixed ramp** where a standard or a natural scale gives the two ends, as for the walks, air quality and noise.
  - **A region ramp** where nothing does: a ramp whose ends come from the region's own values, which the build writes into the bundle as numbers. From each end it leaves out the most extreme hex cells, up to 1 in 100, but never a value that a whole area shares (0.1% or more of the cells, and at least two), so a value per borough keeps its dearest and cheapest borough. Only the hex cells with homes count (D22).
  - **A log scale** where an amount grows by ratio: money, rates and densities score the logarithm of the value, so each step of the same percentage counts the same, in any currency; counts of places nearby score the logarithm of the count plus one, so the first few count most. Shares, indices, times and distances stay on a straight scale.
  - **No percentile curve.** The 38 indicators that used it moved: 12 to a region ramp on a log scale, 12 counts to a region ramp on the log of the count plus one, 10 to a region ramp on a straight scale, and 4 to a fixed ramp (A&E waiting from 35% to the NHS standard of 95%, life satisfaction over the UK's spread of local-authority means from 7.0 to 8.2, and school inspections and conservation areas from 0 to 100%).
  - When the map shows one measured indicator, the legend's ends give its values ("£3,739 a month", "£1,540 a month"), and the quick look gives the value of the hex cell.
  - The bundle's format is 2: an app that reads format 1 refuses it, and this one refuses a format 1 bundle, rather than misreading a curve.
- **Why:** The owner showed the map with only "Renting cost" on: boroughs at £2,834 and £3,739 a month had the same colour. A percentile scores a cell by its rank among the region's cells, so it follows how many cells hold each value, not the amount. On bundle 36eb7eb8e423, £905 a month between two boroughs moved a cell 5.5 points and £5 between two others moved it 6; council tax 10 points for £7 a year; burglary at 55 a year per 1,000 residents looked like 10; and "none nearby" scored in the middle, 42 for coworking. A region ramp on a log scale gives rent £3,739 0, £2,834 31, £2,349 52, £1,833 80 and £1,540 100, and keeps every indicator's spread at a standard deviation of 16 to 27 points. The details are in the [spec](specs/2026-11-23-score-by-the-amount.md).
- **Alternatives considered** (each tested on the same bundle):
  - A straight ramp for money: 60% to 64% of rent and buying cost fell in the top fifth.
  - The ratio to the region's median: no London rent scored above 63, and no council tax below 38.
  - Tukey fences, or a 5% trim kept to whole areas: they cut whole boroughs, so Kensington and Chelsea and Westminster both scored 0.
  - Half percentile and half ramp: £2,834 and £3,739 were only 18 points apart.
  - Ends at the 1st and 99th percentile of the cells: they kept Kensington and Chelsea only because it holds 1.01% of the cells.
  - Ends at the 1st and 99th percentile of the distinct values: for counts the tail holds the distinct values, so the cafés' top end was 424 and most cells scored red.
- **What it costs:** the amounts can look harsh. Council tax scores under 40 in 94% of the cells, because Westminster and Wandsworth are about £1,000 a year below the rest, and where most cells have none nearby (LGBTQ+ venues, coworking, water, nature sites), most cells score 0. Both are the true picture. With every factor counted, the centre leads the livability score more than before, because the counts of places nearby (cafés, venues, lines) now score 0 where there are none, where a rank gave 25 to 42. A region ramp is still relative to its region, as the percentile was. The "Rank in London" colouring (D24) orders the cells, so it cannot show amounts.
- **Revisit when:** a second region or currency arrives: check that its ends are sound in its QA report, and whether an indicator with a national scale should move to a fixed ramp.
- **History:**
  - 2026-11-23: accepted by the owner in plan mode: fix every percentile indicator with one rule, and a log scale for money.
