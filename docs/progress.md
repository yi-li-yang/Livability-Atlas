# Progress

## Now

- Step 0.1 is merged into `main` (#1).
- Step 0.2: the factor explorer (#2), the [catalogue format](specs/2026-10-24-catalogue-format.md) (#3), the [Transport research](specs/2026-10-24-transport-research.md) (#4) and the `/research-factor` command (#5) are merged.
- Step 0.2: the research of [Environment](specs/2026-10-25-environment-research.md) (#6), [Safety](specs/2026-10-25-safety-research.md) (#7), [Housing and cost](specs/2026-10-25-housing-research.md) (#8), [Natural hazards](specs/2026-10-25-natural-hazards-research.md) (#9), [Daily amenities](specs/2026-10-25-daily-amenities-research.md) (#10), [Digital connectivity](specs/2026-10-25-digital-connectivity-research.md) (#11) and [Education](specs/2026-10-25-education-research.md) (#12) is merged, and the [Community and people research](specs/2026-10-25-community-research.md) is done.
- All nine MVP candidates are researched: 38 of the catalogue's 85 within-city measured indicators, from 26 datasets.
- `AGENTS.md` now bridges Google Antigravity to `CLAUDE.md` (D20). It is committed on `docs/agents-md`, not yet pushed, and not yet run in Antigravity.

## Next

1. The rest of step 0.2, in the roadmap's order:
   - Set default weights from evidence, with reasons, and compute the build order (D14).
   - Propose the MVP set of about 10 top-level factors.
2. Five checks the owner can make at any time:
   - Open the repo in Antigravity and ask it to list the project's guardrails. If it names the public repo, D07 and D08, the include works and D20 can be accepted.
   - Ask the GLA Air Quality Team, the contact on the London Datastore, to confirm an open licence for the London Atmospheric Emissions Inventory. Until then, or until the next check succeeds, air quality stays out of public builds.
   - Check the licence of Defra's background maps on UK-AIR, once the site is back online.
   - Ask TfL's WebCAT team for its latest PTAL data, since the open release is from 2015, before the Elizabeth line (spike S1).
   - Ask Royal Mail whether matching Price Paid Data to energy certificates by address, to publish prices per m² by area, is allowed. Until then, buying cost stays out of public builds (spike S3).
3. Before step 0.3:
   - Install uv and just with winget.
   - Set `PYTHONUTF8=1`, and point `UV_CACHE_DIR` at a folder on `E:`.
   - Optionally, upgrade Git for Windows from 2.41 and set `core.longpaths true`.

## Blocked

- Nothing.

## Log

### 2026-10-26

- **Agent rules bridged** for Google Antigravity (D20). Antigravity always loads a root `AGENTS.md` and its documentation does not mention `CLAUDE.md`, so the new [AGENTS.md](../AGENTS.md) includes `CLAUDE.md`, which stays the one source of rules. It also translates the Claude Code tools that `CLAUDE.md` names (the superpowers skills, `/research-factor`, `/code-review`) and sets rules for two agents sharing a clone: one agent per branch, a worktree each when they work at once, and a commit as the hand-over. Step 0.3's nested `CLAUDE.md` files will each need an `AGENTS.md` beside them. Built from Antigravity's documentation; it has not been run in Antigravity, hence the new check in "Next".

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
