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
| [D10](#d10-travel-times) | Travel times | Station matrix + in-browser estimate; r5py, with the TfL API as fallback | accepted |
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

## D07 Dataset licences

- **Status:** accepted
- **Choice:** The project is non-commercial for now, so the build uses every dataset it can, with its attribution; any dataset still needs a licence entry. Each dataset is marked `commercial_use`, true only where its licence allows redistribution and commercial use, with attribution, so that a future commercial edition knows what it may keep and what it must pay for or drop. The commercial list, by SPDX licence id:
  - the Open Government Licence: `OGL-UK-1.0`, `OGL-UK-2.0`, `OGL-UK-3.0`
  - Creative Commons: `CC-BY-3.0`, `CC-BY-4.0`, `CC-BY-SA-3.0`, `CC-BY-SA-4.0`, `CC0-1.0`
  - `ODbL-1.0`, `CDLA-Permissive-1.0`, `CDLA-Permissive-2.0` and `Apache-2.0`
  - TfL's open data licence, `LicenseRef-TfL-Open-Data`: version 2.0 of the Open Government Licence with TfL's amendments, which SPDX does not list

  Datasets under non-commercial licences (e.g. Ookla's speed tests), restrictive terms or a licence not yet confirmed are marked `commercial_use: false` with a note, and are used in the build. `atlas build --commercial` leaves out the indicators built from them. Proprietary data that forbids redistribution, such as the published rankings, is still not copied into bundles: only ranks, with a citation. The catalogue's checks enforce the marking: a dataset with `commercial_use: true` needs a licence from the list, the date it was checked at the source, and its attribution ([catalogue/README.md](../catalogue/README.md#datasetsyaml)).
- **Why:** The owner decided on 2026-10-28 to build everything that is possible now and to pay for licences later, if there is ever a commercial edition, turning what they unlock into paid features. Marking each dataset keeps that edition possible.
- **Revisit when:** A commercial edition is planned, or a restricted dataset is worth licensing. It then moves to the commercial list under its new licence.
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-24: the examples became an allowed list of SPDX ids, enforced by the factor catalogue's checks. A dataset whose licence is not yet confirmed stays out of public builds, as the London Atmospheric Emissions Inventory does until the GLA confirms its licence.
  - 2026-10-24: TfL's open data licence joined the allowed list. It allows commercial use and redistribution with attribution. Its amendments add registration for live feeds and a rate limit, and TfL may revise it without notice, so it is checked again before each public build.
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
  - The engine is r5py with GTFS timetables, which computes the whole matrix at several departure times in minutes. It waits for the owner's registrations for the timetable sources, and a JDK 21. The TfL Journey Planner API is the fallback: it builds the matrix in about 21 hours for one departure time, at TfL's limit of 500 calls a minute.
- **Why:** In a static-first app, the data pipeline cannot precompute every user's places.
- **Known limits:** Buses are not in the matrix, so bus-only trips come out too long: spike S4 found the estimate more than 20% too long in 19% of journeys, and within 20% in 81%, with a median error of 12% (27 journeys, one morning). Estimates carry the evidence type "estimate".
- **Revisit when:** The real matrix exists, to check the error on a larger sample and several departure times; or buses join the matrix. Exact routing arrives with a routing service (Phase 4).
- **History:**
  - 2026-10-23: proposed in the Phase 0 planning session.
  - 2026-10-28: accepted after [spike S4](spikes/S4-routing.md). The design stands, r5py is the engine, and the API is the fallback. r5py was not run, because its timetable sources need accounts that only the owner can create.

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
  - 2026-10-28: accepted. The 18 top-level factors' weights are set by how many of the five sources weigh each one, with the mapping and the build order in the [spec](specs/2026-10-28-default-weights.md). Matching a source's own category to one of ours took judgement, which the spec flags; sub-factor weights stay at the engineering default of 3 until their own evidence arrives.

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
  - Each factor has its own colour, from the categorical palette of the Salt design system. The interface itself stays in ink, so colour always means data.
  - Details are in [interface.md](interface.md).
- **Why:** Users see the answer first and are not flooded with detail. Sizes that follow the weights show at a glance how much each factor counts. The owner tried both layouts in the factor explorer and found each useful. The treemap shows first because rectangles show shares more faithfully than rings, and hold more labels.
- **Revisit when:** Testing in Phase 1 shows that one layout is rarely used, or that colour by factor confuses.
- **History:**
  - 2026-10-23: proposed after review asked for layered details and a visual, interactive factor list.
  - 2026-10-24: accepted after the owner tried the factor explorer. Both layouts stay, with a switch, and each factor has its own colour.

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
