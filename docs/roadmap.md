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
- [ ] **0.4 Spikes S1–S8** (listed below).
- [ ] **0.5 Method and freeze.**
  - [ ] Finalise `methodology/scoring.md`.
  - [ ] Commit golden test cases to `shared/fixtures/scoring/`, covering nested trees, missing data, flipped directions and ideal ranges.
  - [ ] Freeze the MVP factor list in the decision register.
  - [ ] Detail the Phase 1 milestones here.

### Spikes

A spike is a small experiment with throwaway code. It answers one question, stops once that question is answered, and leaves one page in `docs/spikes/`.

| ID | Question |
| --- | --- |
| S1 | Can the PTAL grid be mapped to hex cells, and is there a PTAL release newer than the Elizabeth line (2022)? Done: [S1](spikes/S1-ptal.md) |
| S2 | What crime rates per hex cell do 12 months of Police.uk data give, with smoothing? Done: [S2](spikes/S2-crime.md) |
| S3 | How many hex cells have enough sales for a price per m² (Land Registry with EPC floor areas)? What is the finest open rent data for London, and is a model of rent from sale prices credible? |
| S4 | Can r5py with GTFS timetables, or the TfL API, build the station matrix? How large is the error of the in-browser estimate against TfL Journey Planner? What do TfL's terms and limits allow? The answers decide D10 |
| S5 | How should raster data (air quality, noise) be aggregated to hex cells? |
| S6 | How complete are Overture, Foursquare Open Source Places and OpenStreetMap, brand tags included? How much do straight-line and network walking distances differ? |
| S7 | Does the culture evidence ladder work on a sample of neighbourhoods, with a known-fact assertion for each kind of evidence? |
| S8 | Do the food signals (hygiene ratings, Michelin in Wikidata, cuisine variety, the independents' share) work for London? Do the brand groups track house prices? |

### Exit criteria

- [ ] Decisions D01–D21 are accepted, or marked "revisit" with a reason.
- [ ] `just validate` passes. Default weights carry reasons. The MVP factor list is frozen, with each dataset's licence checked.
- [ ] The factor explorer shows the full catalogue, and the D17 layout is chosen.
- [ ] Spikes S1–S8 are written up with their decisions.
- [ ] The scoring specification v0 and the golden test cases are committed.
- [x] `just check` passes locally and in GitHub Actions.
- [ ] A fresh Claude Code session finds the next task and the right commands from `CLAUDE.md` and `docs/progress.md` alone.

## Phase 1: London MVP

Goal: a public London map. Exit criteria: the MVP success criteria in [vision.md](vision.md#mvp-success-criteria-end-of-phase-1).

- [ ] **Walking skeleton.** One factor end to end: PTAL → hex cells → data bundle → coloured map.
- [ ] **Scoring and the visual factor tree.** The scoring engine, the chosen treemap or sunburst with sliders and drill-down for 3 factors, and default weights.
- [ ] **MVP factors.** The remaining factors, each added through the factor recipe.
- [ ] **Travel and hard limits.**
  - [ ] the station matrix
  - [ ] travel times to the default places
  - [ ] the in-browser estimate for a user's places
  - [ ] hard limits
- [ ] **Layers of detail.** Quick look, why this score, inside a factor and the evidence layer; the ranked neighbourhoods; a single-factor view (e.g. crime only).
- [ ] **Validation and release.** The QA report runs all its checks. The site is then released as a public static site, with the owner's go-ahead.

## Phase 2: depth and trust

Goal: the Phase 2 items in the [backlog](backlog.md#phase-2-depth-and-trust), in priority order. Exit criteria: the top 20 factors are built, and a data refresh runs with one command.

## Phase 3: more places

Goal: the across-cities scale, drill-down from country to city to neighbourhood, a global-tier baseline for any city, and a second city built by the region recipe. Exit criteria: the second city needed no code outside its datasets, and the across-cities view works.

## Phase 4: product

Goal: the Phase 4 items in the backlog. Exit criteria: decided at the end of Phase 3.

## Cycles

A cycle is one goal, written in [progress.md](progress.md) when it starts. It ends when the goal's check passes, not on a date. Each cycle closes with a demo note (a screenshot and what changed) and three retro lines: keep, change, try.
