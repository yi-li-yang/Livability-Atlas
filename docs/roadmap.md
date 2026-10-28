# Roadmap

Phases end when their exit criteria are met, not on dates. Features beyond the current phase are kept in the [backlog](backlog.md).

## Phase 0: foundations (current)

Goal: turn the concept into decisions, a researched factor catalogue, a scoring method and a clean scaffold, so that Phase 1 can build without rework.

### Steps

- [x] **0.1 Foundations.** Living documents, licence, `CLAUDE.md`, `CONTRIBUTING.md`, README and `.gitignore`. Docs only. Reviewed and approved by the owner.
- [x] **0.2 Factor catalogue and factor explorer.**
  - [x] Factor explorer: a standalone page that draws the seed factor tree as both a treemap and a sunburst, sized by default weights, with live sliders and drill-down. It is published as a private Artifact for review, and the layout is chosen from it (D17). Both layouts stay, with a switch, and each factor has its own colour.
  - [x] Catalogue format: the fields of measured indicators and datasets, their checks, D07 as a rule, and the research shown in the factor explorer. Proved on NO₂ and PM2.5.
  - [x] The nine MVP candidates researched, one pull request each, with `/research-factor`: Transport, Environment, Safety, Housing and cost, Natural hazards, Daily amenities, Digital connectivity, Education, and Community and people.
  - [x] Top-down pass: expand the 18 top-level factors into sub-factors and measured indicators, each with its preference type (`catalogue/factors.yaml`). All 18 have sub-factors. The ten MVP factors have researched measured indicators with their preference types, and the other eight stay ideas until Phase 2.
  - [x] Bottom-up pass: inventory city, country and global datasets, each with its tier and what it can tell us (`catalogue/datasets.yaml`). It holds 30 datasets and six published rankings. Datasets for the other eight factors are inventoried when they are researched.
  - [x] Assess published rankings against the credibility rubric (`docs/factors/rankings.md`).
  - [x] Draft `docs/methodology/hard-to-measure.md`.
  - [x] Set default weights from evidence, with reasons, and compute the build order (D14).
  - [x] Propose the MVP set: about 10 top-level factors (D21: the nine researched, and Health care).
  - [x] Research Health care, the tenth MVP factor, with `/research-factor health-care`.
- [x] **Before 0.3: install the tools.** Install uv and just with winget. Set `PYTHONUTF8=1`, and point `UV_CACHE_DIR` at a folder on `E:`. Java 21 waits for spike S4.
- [x] **0.3 Scaffold and CI.** Starts with `superpowers:writing-plans`.
  - [x] `pipeline/`: a uv project with ruff, pyright and pytest. `atlas --help` runs, and `atlas validate` checks `catalogue/`.
  - [x] `web/`: a Vite + React + TypeScript app showing a MapLibre basemap of London, with Biome, Vitest and one Playwright smoke test.
  - [x] `shared/schemas/`, TypeScript type generation, and a CI check that the generated files are current.
  - [x] `justfile`, pre-commit, GitHub Actions running `just check`, and `.claude/settings.json`.
  - [x] The nested `CLAUDE.md` files, each with an `AGENTS.md` beside it (D20), for `pipeline/` and `web/`.
- [x] **0.4 Spikes S1–S8** (listed below). S1, S2 and S8 are done. S3 to S7 are partly done, each waiting on something the write-up names.
- [x] **0.5 Method and freeze.**
  - [x] Finalise `methodology/scoring.md`.
  - [x] Commit golden test cases to `shared/fixtures/scoring/`, covering nested trees, missing data, flipped directions and ideal ranges. 15 cases, and a Python reference scorer that reproduces them.
  - [x] Freeze the MVP factor list in the decision register. D21 and the [MVP scope](specs/2026-10-28-mvp-scope.md): ten factors, 41 measured indicators.
  - [x] Detail the Phase 1 milestones here. See Phase 1 below.

### Spikes

A spike is a small experiment with throwaway code. It answers one question, stops once that question is answered, and leaves one page in `docs/spikes/`.

| ID | Question |
| --- | --- |
| S1 | Can the PTAL grid be mapped to hex cells, and is there a PTAL release newer than the Elizabeth line (2022)? Done: [S1](spikes/S1-ptal.md) |
| S2 | What crime rates per hex cell do 12 months of Police.uk data give, with smoothing? Done: [S2](spikes/S2-crime.md) |
| S3 | How many hex cells have enough sales for a price per m² (Land Registry with EPC floor areas)? What is the finest open rent data for London, and is a model of rent from sale prices credible? Partly done: [S3](spikes/S3-sales-and-rents.md); the price per m² waits for the EPC download and Royal Mail |
| S4 | Can r5py with GTFS timetables, or the TfL API, build the station matrix? How large is the error of the in-browser estimate against TfL Journey Planner? What do TfL's terms and limits allow? The answers decide D10. Partly done: [S4](spikes/S4-routing.md); r5py waits for the owner's timetable registrations |
| S5 | How should raster data (air quality, noise) be aggregated to hex cells? Partly done: [S5](spikes/S5-noise-aggregation.md); noise is settled, air quality and flooding are not |
| S6 | How complete are Overture, Foursquare Open Source Places and OpenStreetMap, brand tags included? How much do straight-line and network walking distances differ? Partly done: [S6](spikes/S6-places.md); food, supermarkets and shops are tested, other kinds are not |
| S7 | Does the culture evidence ladder work on a sample of neighbourhoods, with a known-fact assertion for each kind of evidence? Partly done: [S7](spikes/S7-culture-ladder.md); four rungs tested |
| S8 | Do the food signals (hygiene ratings, Michelin in Wikidata, cuisine variety, the independents' share) work for London? Do the brand groups track house prices? Done: [S8](spikes/S8-food-signals.md) |

### Exit criteria

- [x] Decisions D01–D21 are accepted, or marked "revisit" with a reason.
- [x] `just validate` passes. Default weights carry reasons. The MVP factor list is frozen, with each dataset's licence checked.
- [x] The factor explorer shows the full catalogue, and the D17 layout is chosen.
- [x] Spikes S1–S8 are written up with their decisions.
- [x] The scoring specification and the golden test cases are committed.
- [x] `just check` passes locally and in GitHub Actions.
- [ ] A fresh Claude Code session finds the next task and the right commands from `CLAUDE.md` and `docs/progress.md` alone.

## Phase 1: London MVP

Goal: a public London map. Exit criteria: the MVP success criteria in [vision.md](vision.md#mvp-success-criteria-end-of-phase-1).

Each milestone ends when its checks pass. The order follows what depends on what, and each is a set of pull requests that keep `just check` green. The decisions behind them are in the spike write-ups ([S1 to S8](spikes/S1-ptal.md)), the [MVP scope](specs/2026-10-28-mvp-scope.md) and the [scoring method](methodology/scoring.md).

- [ ] **Walking skeleton.** One factor end to end: PTAL → hex cells → data bundle → coloured map.
  - [ ] `atlas build london` for one factor writes a data bundle: `manifest.json` and `cells.parquet` for the 16,668 hex cells of Greater London (the ONS region's boundary, by cell centres), and the manifest's schema is exported to `shared/schemas/` and typed in the web app (the contract of [architecture.md](architecture.md#contracts)). Built, with the schema exported and its types generated; the web app does not read it yet.
  - [x] PTAL becomes a band for each cell by the band that covers most of it, ties to the lower band, and no value outside Greater London (S1). Tests assert it.
  - [ ] The web app loads the bundle and colours every cell with deck.gl, and a Playwright test sees the coloured map.
  - Check: the same command run twice gives byte-identical bundles. Tested on synthetic data, and run twice on the real London data, which gave the same version.
- [ ] **Scoring and the visual factor tree.** The scoring engine, the chosen treemap or sunburst with sliders and drill-down for 3 factors, and default weights.
  - [ ] The TypeScript engine reproduces all 15 golden cases of `shared/fixtures/scoring/`, and CI runs it and the Python reference scorer against them.
  - [ ] The factor tree (D17: both layouts, with a switch) with sliders and drill-down, and the default weights from the catalogue. The profile lives in the browser's storage and the URL, never on a server (D08).
  - Check: the map recolours within about 100 ms of a weight change over about 17,000 cells, measured in a test.
- [ ] **MVP factors.** The remaining factors, each added through the factor recipe.
  - [ ] In the [build order](specs/2026-10-28-mvp-scope.md#build-order): Safety, Environment, Education, Housing and cost, Health care, Transport, Daily amenities, Community and people, Natural hazards, Digital connectivity.
  - [ ] The 32 measured indicators that ship at launch first. Then the 5 that need a curve, whose curves come from the built data. Then the 4 that are blocked, as the owner's checks lift the blocks.
  - Check for each: its dataset checks, a known-fact assertion, and coverage in the QA report pass, and `atlas validate` passes. The methods in the catalogue carry the spikes' choices: street walks, residents shared by area, rates pooled with a floor, noise averaged at addresses, and the two sources of places pooled.
- [ ] **Travel and hard limits.**
  - [ ] the station matrix: r5py with timetables once the owner has registered for the three sources and installed a JDK, and the Journey Planner API otherwise (D10, [S4](spikes/S4-routing.md))
  - [ ] travel times to the default places
  - [ ] the in-browser estimate for a user's places, with its error checked on a larger sample and several departure times
  - [ ] hard limits, reproducing the `hard-limit-*` golden cases
- [ ] **Layers of detail.** Quick look, why this score, inside a factor and the evidence layer; the ranked neighbourhoods; a single-factor view (e.g. crime only).
  - [ ] The evidence layer shows each measured indicator's raw value, scoring curve, dataset, date, licence and evidence type.
  - [ ] Neighbourhood names come from the House of Commons Library's MSOA names.
  - Check: contributions shown in the app add up to the livability score, on the same cases as the golden ones.
- [ ] **Validation and release.** The QA report runs all its checks. The site is then released as a public static site, with the owner's go-ahead.
  - [ ] The QA report runs dataset checks, cross-checks and known-fact assertions ([validation.md](methodology/validation.md)), and each factor's data coverage.
  - [ ] `just build london` rebuilds the bundle from raw downloads, and gives the same result every time.
  - [ ] A new factor is added by the recipe with no change to the UI's code.
  - [ ] Every dataset in the bundle is licensed for public builds, with its attribution shown.
  - The release itself is the owner's decision: publishing is outward-facing.

## Phase 2: depth and trust

Goal: the Phase 2 items in the [backlog](backlog.md#phase-2-depth-and-trust), in priority order. Exit criteria: the top 20 factors are built, and a data refresh runs with one command.

## Phase 3: more places

Goal: the across-cities scale, drill-down from country to city to neighbourhood, a global-tier baseline for any city, and a second city built by the region recipe. Exit criteria: the second city needed no code outside its datasets, and the across-cities view works.

## Phase 4: product

Goal: the Phase 4 items in the backlog. Exit criteria: decided at the end of Phase 3.

## Cycles

A cycle is one goal, written in [progress.md](progress.md) when it starts. It ends when the goal's check passes, not on a date. Each cycle closes with a demo note (a screenshot and what changed) and three retro lines: keep, change, try.
