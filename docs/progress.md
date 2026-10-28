# Progress

## Now

- Step 0.1 is merged into `main` (#1).
- Step 0.2: the factor explorer (#2), the [catalogue format](specs/2026-10-24-catalogue-format.md) (#3), the [Transport research](specs/2026-10-24-transport-research.md) (#4) and the `/research-factor` command (#5) are merged.
- Step 0.2: the research of [Environment](specs/2026-10-25-environment-research.md) (#6), [Safety](specs/2026-10-25-safety-research.md) (#7), [Housing and cost](specs/2026-10-25-housing-research.md) (#8), [Natural hazards](specs/2026-10-25-natural-hazards-research.md) (#9), [Daily amenities](specs/2026-10-25-daily-amenities-research.md) (#10), [Digital connectivity](specs/2026-10-25-digital-connectivity-research.md) (#11) and [Education](specs/2026-10-25-education-research.md) (#12) is merged, and the [Community and people research](specs/2026-10-25-community-research.md) is done.
- All ten MVP factors are researched: 43 of the catalogue's 86 within-city measured indicators, from 32 datasets.
- Step 0.2: [default weights and the build order](specs/2026-10-28-default-weights.md) (D14) are done.
- `AGENTS.md` now bridges Google Antigravity to `CLAUDE.md` (D20). The owner has run Antigravity on it, and it saw the whole of `CLAUDE.md`. Merged as pull request #16.
- Step 0.3 is built, in two pull requests ([plan](plans/2026-10-28-scaffold.md)). Part 1 is merged as #19 and part 2 as #20, both with CI green. Part 1: uv and just are installed, `pipeline/` holds the `atlas` command with `validate` and `schemas`, the catalogue's Pydantic models are exported to `shared/schemas/`, and `just check` runs in CI. `atlas validate` passes on the real catalogue. Part 2: `web/` shows a MapLibre basemap of London, with TypeScript types generated from the schemas, and CI runs its checks and a Playwright smoke test.
- The MVP factor set ([D21](decisions.md#d21-mvp-factor-set)), the last item of step 0.2, is decided: the nine researched top-level factors and Health care as a tenth. The owner delegated the call, and it can be reversed. The [Health care research](specs/2026-10-28-health-care-research.md) is done, and with it step 0.2: the top-down and bottom-up passes are ticked for the ten MVP factors, and the other eight factors stay ideas until Phase 2.

## Next

1. Step 0.4, the spikes S4 to S8 ([roadmap](roadmap.md#spikes)), in the order of their dependencies. S1 and S2 are done, and S3 is partly done.
2. Seven checks the owner can make at any time:
   - Ask the GLA Air Quality Team, the contact on the London Datastore, to confirm an open licence for the London Atmospheric Emissions Inventory. Until then, or until the next check succeeds, air quality stays out of public builds.
   - Check the licence of Defra's background maps on UK-AIR, once the site is back online.
   - Sign in with a GOV.UK One Login and download the domestic energy performance certificates (CSV, England and Wales) into `data/raw/epc/`, so that spike S3 can finish the price per m² in a private build.
   - Read the OS OpenData licence page, which answered 503 on 2026-10-28, for Code-Point Open. If it is the Open Government Licence, public builds can place GP practices from their postcodes with it, as an alternative to the ONS Postcode Directory.
   - Read the licence on the ONS Postcode Directory's own page on the Open Geography Portal. Until it states one, GP practices cannot be placed from their postcodes in public builds, and patients per GP stays out of them.
   - Ask TfL's WebCAT team for its latest PTAL data, since the open release is from 2015, before the Elizabeth line (spike S1).
   - Ask Royal Mail whether matching Price Paid Data to energy certificates by address, to publish prices per m² by area, is allowed. Until then, buying cost stays out of public builds (spike S3).
3. Optionally, upgrade Git for Windows from 2.41 and set `core.longpaths true`.

## Blocked

- Nothing.

## Log

### 2026-10-28

- **Spike S3 partly done: sales, prices and rents** ([write-up](spikes/S3-sales-and-rents.md)). Pooling a cell with its neighbours within two steps over 24 months gives 20 or more sales in 99% of London's homes cells, and 40 or more in 95%, so a price needs that pooling. The price per m² itself waits for two things only the owner can do: a GOV.UK One Login to download the energy certificates, and Royal Mail's answer. The finest open rents are the ONS's by postcode district, which join the catalogue as a dataset but stay out of the score, because the ONS says they should not be compared between areas. A model of rent from sale prices is within 7% of a district's rent, against 8% for the borough's average, so it is not worth a per-cell value.
- **Spike S2 done: crime rates per hex cell** ([write-up](spikes/S2-crime.md)). Twelve months of Met and City of London data (1.1 million records) give usable rates per 1,000 residents with three choices: share each output area's residents between the cells it overlaps by area (placing them at centroids left 38% of cells empty), pool each cell with its neighbours within two steps (about an 8-minute walk), and add a floor of 3,000 residents at the London-wide rate. The five crime indicators move to `spiked`. One problem stays open: the City of London tops every category, because workers and visitors are in the crime counts but not in the residents. It is in the backlog for Phase 2.
- **Spike S1 done: PTAL to hex cells** ([write-up](spikes/S1-ptal.md)). TfL's 100 m grid maps cleanly to resolution 9 cells, and the band that covers most of a cell matches the band at its centre in 82% of cells, against 69% for the band of the mean index, so the catalogue's method stands. The London Datastore has only the 2015 release, with no newer open release, so the owner's WebCAT request stays. Greater London comes to 16,883 cells, so "about 15,000" is now "about 17,000" in the docs. The geospatial libraries are installed in the pipeline's `spikes` dependency group, and their Windows wheels work.
- **Health care researched, the tenth MVP factor,** with the [spec](specs/2026-10-28-health-care-research.md). GP access becomes two measured indicators, the walk to a GP practice (the pharmacies curve, from CIHT) and patients per GP (1,800 per GP is the planning benchmark of the Healthy Urban Development Unit; the zero end waits for London's data). A&E travel time becomes distance to A&E in straight-line kilometres, which is how the one published study measures it. NHS England's registers, patient counts and workforce data are under the Open Government Licence. The ONS Postcode Directory, which turns practices' postcodes into places, stays out of public builds until its own page states a licence, so public builds place GP surgeries from OpenStreetMap for now. Dentists stay an idea: no open source says which practices take new NHS patients.
- **Line endings fixed** (#22). Windows checkouts got CRLF and Biome failed on them, so `.gitattributes` now sets LF everywhere.

- **MVP factor set decided (D21),** the last item of step 0.2. The nine researched top-level factors stay, and Health care joins them as a tenth. Health care ties D14's highest weight (4, with Housing and cost, Environment and Safety), is weighed by four of the five sources, and the vision asks for about 10. Researching it is one more run of `/research-factor`, so the cost is small and the choice is easy to reverse. The owner delegated the call, so this can be reversed in review.
- **Scaffold and CI, part 2 (step 0.3).** `web/` is a Vite, React and TypeScript app with a MapLibre basemap of London (OpenFreeMap), Tailwind, Biome, Vitest and a Playwright smoke test. `just generate` writes TypeScript types from `shared/schemas/`, and CI fails if a generated file is stale. Looking at the built app showed a blank map: MapLibre 6 could not find its worker script, and the build and the first smoke test had both passed. The worker is now imported with `?url`, and a second smoke test fails if it is not served as JavaScript. CI on GitHub's runner passes `just check`, the build and the Playwright smoke test, which meets the step's exit criterion.
- **Scaffold and CI, part 1 (step 0.3).** Wrote the [plan](plans/2026-10-28-scaffold.md) for the whole step, in two parts, and built the first. uv and just are installed with winget. The catalogue's rules, which the factor explorer checked in JavaScript, are now Pydantic models plus checks across records, and `atlas validate` passes on the real catalogue. `atlas schemas` exports the models to `shared/schemas/` for the web app's types. The `justfile`, pre-commit (ruff, large files, gitleaks), the `.claude/settings.json` permissions and CI are in. Pyright found two typing mistakes in the first draft, which the plan now shows corrected. Choices the roadmap left open, all reversible: the geospatial libraries and shadcn/ui wait until something imports them, Playwright runs as `just e2e` and not inside `just check`, and a Markdown link check in CI is in the backlog.
- **Default weights and the build order set from evidence (D14),** with the [spec](specs/2026-10-28-default-weights.md) recording the method. Each of the 18 top-level factors' weight counts how many of five sources weigh it: the OECD, EIU, Mercer and AARP livability frameworks, and the English Housing Survey's reasons for moving. Housing and cost, Environment, Safety, Health care and Education come out highest, at 4; Climate, Natural hazards, Animal friendliness, Digital connectivity and Urban form and change come out lowest, at the floor of 1. The factor explorer now requires every top-level factor to give its reason, not only those away from the engineering default of 3. The build order ranks the nine researched MVP candidates by weight, then by how many of their measured indicators are already clear for public builds: Safety first, Digital connectivity last.
- Fixed a stale count in this file's "Now": published rankings had added two more researched measured indicators since the "38" figure was written.

### 2026-10-26

- **Agent rules bridged** for Google Antigravity (D20). Antigravity always loads a root `AGENTS.md` and its documentation does not mention `CLAUDE.md`, so the new [AGENTS.md](../AGENTS.md) includes `CLAUDE.md`, which stays the one source of rules. It also translates the Claude Code tools that `CLAUDE.md` names (the superpowers skills, `/research-factor`, `/code-review`) and sets rules for two agents sharing a clone: one agent per branch, a worktree each when they work at once, and a commit as the hand-over. Step 0.3's nested `CLAUDE.md` files will each need an `AGENTS.md` beside them. Built from Antigravity's documentation. The owner then opened the repo in Antigravity, and it saw the whole of `CLAUDE.md`, so D20 is accepted. Antigravity runs only when the owner starts it.

### 2026-10-25

- **Hard-to-measure factors drafted** in [hard-to-measure.md](methodology/hard-to-measure.md): the evidence ladder, seven rules for using it, and the ladder applied to culture, food quality, brand presence, community life, feeling safe and industry strength. One new rule guards against bias in models that rate streets from photos (D08). The matching sections leave the research notes.
- **Published rankings merged** into `main` as pull request #14.
- **Published rankings assessed** in [rankings.md](factors/rankings.md). Of six, the EIU and the OECD rate high, the Sunday Times medium, and Time Out, Mercer and Monocle low. Each joins `datasets.yaml` with its rating and reason. None may go into public builds: five are proprietary, and the OECD's data terms are still to confirm. Within London, the Sunday Times and Time Out become listings, researched as measured indicators.
- **Community and people merged** into `main` as pull request #13.
- **Community and people researched, the last MVP candidate.** Your community scores the presence of a group the user picks, and diversity scores Simpson's index over the census's ethnic groups, both by rank and both in a fixed direction, as D08 requires. Faith scores the walk to the nearest place of worship of the user's faith. The Census 2021 topic summaries join the catalogue. All nine MVP candidates are now researched.
- **Education merged** into `main` as pull request #12.
- **Education researched.** Schools become three measured indicators: the walk to the nearest state primary school and the nearest secondary school, from CIHT's distances for school trips, and the inspection results of nearby schools. Ofsted's report cards, in force since November 2025, do not compare directly with its earlier grades, so the inspection curve waits for a definition that spans both. The DfE's register of schools and Ofsted's inspection records are open.
- **Digital connectivity merged** into `main` as pull request #11.
- **Digital connectivity researched.** Ofcom's open data gives gigabit-capable broadband down to output areas, but full fibre only by local authority, so full-fibre availability becomes gigabit broadband. 5G comes only by borough, and is measured from all four networks, since nearly every London premises has 5G from at least one. The ONS output area boundaries join the catalogue, for gigabit broadband and for the crime rates.
- **Daily amenities merged** into `main` as pull request #10.
- **Daily amenities researched.** Groceries, pharmacies, gyms and libraries score by the walk to the nearest one, from CIHT's walking distances; cafés, restaurants and cuisines by how many lie within a 10-minute walk, their curves waiting for spike S6; and food hygiene by the share of nearby businesses rated good or very good. Overture Places joins the catalogue under three open licences, which the checks now accept joined by AND, with the Food Standards Agency's ratings.
- **Natural hazards merged** into `main` as pull request #9.
- **Natural hazards researched.** Flood risk from rivers and the sea, and from surface water, is researched as the share of each hex cell with a 1 in 100 chance or more of flooding in any year, from the Environment Agency's 2 m maps, which are open. Subsidence stays as an idea: its usual source is licensed commercially.
- **Housing and cost merged** into `main` as pull request #8.
- **Housing and cost researched.** Buying cost (£ per m²), renting cost (£ a month, by borough) and council tax (Band D, by borough) are researched, each scored by rank within the region. The ONS rents and MHCLG's council tax are open. Price Paid Data's addresses come with Royal Mail's terms, which may not allow matching sales to energy certificates, so it stays out of public builds until Royal Mail confirms. The certificates themselves are open when located by UPRN.
- **Safety merged** into `main` as pull request #7.
- **Safety researched.** Crime becomes five measured indicators: burglary, violence and sexual offences, robbery and theft from the person, vehicle crime, and anti-social behaviour, as rates per 1,000 residents (D08). No standard sets a safe level of crime, so they score by rank within the region. Police.uk and the Census 2021 resident counts are both open. Road collisions stay as an idea.
- **Environment merged** into `main` as pull request #6.
- **Environment researched.** Road, rail and aircraft noise, and the walk to a green space, are researched, with the [spec](specs/2026-10-25-environment-research.md) recording each choice. The road and rail noise curves come from ProPG, aircraft noise from the government's aviation thresholds, and the green space walk from Natural England's standard and CIHT's guidance. All four new datasets, Defra's noise maps and OS Open Greenspace, may go into public builds. Tree canopy, water nearby and urban heat stay as ideas, with leads in the research notes.
- **Research-factor command.** Researching a factor had been done twice by hand, so `/research-factor <id>` now runs the recipe (#5).
- **Transport merged** into `main` as pull request #4, at the owner's word.

### 2026-10-24

- **Transport researched.** Walk to the nearest station, rail and Tube lines nearby, bus routes nearby, service level (PTAL), travel cost and travel time to places are researched, with the [spec](specs/2026-10-24-transport-research.md) recording each choice. The walking thresholds come from CIHT's guidance and TfL's PTAL, and travel cost from TfL's 2026 fare caps. The curves for lines, routes and travel time wait for spikes S6 and S4. TfL's open data licence joined D07's allowed list, so all four Transport datasets may go into public builds.
- **Catalogue format merged** into `main` as pull request #3.
- **Catalogue format built.** Measured indicators gained their research fields in `catalogue/factors.yaml`, and datasets have their own file, `catalogue/datasets.yaml`. The checks enforce D07 by SPDX licence id. The factor explorer shows each measured indicator's unit, curve, evidence type and datasets. NO₂ and PM2.5 are researched, with curves from the WHO's 2021 guidelines.
- **Licence finding.** Neither air-quality dataset can go into a public build yet. The London Datastore gives the LAEI's licence as "Not Specified", and UK-AIR, which hosts Defra's background maps, was offline for security updates. Both are recorded in `datasets.yaml` with a note, and the two checks are in "Next".
- **Catalogue format started.** Wrote its [spec](specs/2026-10-24-catalogue-format.md) and [plan](plans/2026-10-24-catalogue-format.md). The owner chose to research the MVP factors first, in this session, after the format.
- **Factor explorer merged** into `main` as pull request #2.
- **Factor explorer revised.** After trying both layouts, the owner kept both, with a switch, and asked for a colour for each factor. The colours come from the categorical palette of the Salt design system, in an order checked for normal and colour-blind vision. D17 is accepted.
- **Factor explorer built.** The seed factor tree is in `catalogue/factors.yaml`, and the page has its tests and a browser check in Edge. It is published as a private Artifact, and its pull request is open.
- **Step 0.2 started.** Wrote the [factor explorer spec](specs/2026-10-24-factor-explorer.md).
- **Step 0.1 merged** into `main` as pull request #1.
- **Step 0.1 approved.** The owner reviewed every document and gave the go-ahead. The branch was pushed and a pull request opened.
- **Idea: destinations.** The owner asked for optional distance to services such as Costco, IKEA and the nearest airport. Parked in the [backlog](backlog.md) under Phase 2, with the term "Destination" added to the [glossary](glossary.md).
- **Glossary.** Split into two parts: words the app shows, which must be plain, and words for contributors, where jargon is fine. Three app terms got plainer names: location quotient became industry specialisation, market signal became brand presence, and confidence label became evidence type, with its value "proxy" renamed "indirect".

### 2026-10-23

- **Planning.** The Phase 0 plan went through five review rounds and was approved. Its decisions are recorded as D01–D19 in [decisions.md](decisions.md).
- **Environment.** `E:` was reformatted from exFAT to NTFS (D13), so Git now accepts the repo by file ownership.
- **Step 0.1.**
  - Committed the original concept document, which had never been committed.
  - Added the AGPL-3.0 licence and `.gitignore`.
  - Wrote the living documents, `CLAUDE.md`, `CONTRIBUTING.md` and a new README.
- **Review of step 0.1.** Rewrote the notation in [methodology/scoring.md](methodology/scoring.md): a symbols table, formulas that render on GitHub and in VS Code, and a worked example checked by script.
