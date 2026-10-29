# Codemap

A map of the repository as it is now. It is kept by hand until the tree reaches about 100 files. After that, `just codemap` generates it from the first line of each directory's `README.md`. The planned layout is in [architecture.md](architecture.md#planned-layout).

```text
Livability-Atlas/
├── README.md              # what the project is, status, licences
├── CLAUDE.md              # operating manual for the coding agents; the one source of rules
├── AGENTS.md              # bridge for other agents (Antigravity): includes CLAUDE.md
├── CONTRIBUTING.md        # how to contribute; the CLA; recipes
├── LICENSE                # AGPL-3.0
├── .gitignore             # keeps data/, .env files and build output out of git
├── .gitattributes         # line-ending normalisation
├── justfile               # every command: setup, check, test, validate, generate, docs
├── .pre-commit-config.yaml  # checks before each commit: ruff, large files, gitleaks
├── .github/workflows/ci.yml  # CI: runs `just check` and the generated-file check
├── .claude/
│   ├── settings.json      # shared permissions for the coding agents
│   └── commands/
│       └── research-factor.md  # the recipe for researching one factor, as a Claude Code command
├── pipeline/              # the data pipeline: Python package `atlas`, a uv project
│   ├── CLAUDE.md          # its rules for agents (AGENTS.md beside it includes this)
│   ├── pyproject.toml     # dependencies, ruff, pyright and pytest settings
│   ├── src/atlas/
│   │   ├── cli.py         # the `atlas` command: validate, schemas
│   │   ├── paths.py       # the repository's folders
│   │   ├── secrets.py     # reads a token from the environment or the git-ignored `.env`, and never prints it
│   │   ├── scoring/       # engine.py: the reference scorer, which reproduces the golden test cases
│   │   ├── build.py       # builds a region's data bundle from raw downloads
│   │   ├── fetch.py       # downloads with a cache and a checksum
│   │   ├── spatial/       # grid.py: a region's hex cells
│   │   ├── indicators/    # one module per indicator family: crime.py (rates per 1,000 residents, pooled over two steps with a floor), flood.py (the share of a cell at risk of flooding), transport.py (minutes on foot to a station, lines or routes within a walk), education.py (to a school), health.py (to a GP practice, patients per GP within a walk), environment.py (to a park), air_quality.py (the mean concentration over a cell), noise.py (the mean level at a cell's addresses), housing.py (a borough's value for each of its cells), connectivity.py (the gigabit share of a cell's homes), prices.py (the price per square metre of the homes sold nearby), community.py (Simpson's diversity index and group shares of a cell's residents), faith.py (to the nearest place of worship of each religion), places.py (Overture's and OpenStreetMap's places pooled), amenities.py (to the nearest of a kind, counts and cuisines within a walk, the share of good hygiene ratings)
│   │   ├── datasets/      # one module per dataset, by tier: cities/london/{ptal,laei,tfl_lines}.py, countries/gb/{ons_regions,census_residents,census_ethnic_group,census_religion,nhs_gp,epc,hm_land_registry,addresses,output_areas,police_uk,ea_flood_risk,naptan,gias,nhs_ods,code_point,os_open_greenspace,defra_noise,fsa,ons_local_authorities,ons_rents,mhclg_council_tax,ofcom}.py, world/{openstreetmap,overture}.py
│   │   ├── publish/       # manifest.py (the contract with the web app) and bundle.py (writes the bundle)
│   │   └── catalogue/     # models.py (the one definition of the catalogue files), checks.py, load.py, schema.py
│   ├── tests/
│   └── notebooks/         # spike scripts: throwaway, never imported by the package
├── web/                   # the web app: Vite, React and TypeScript
│   ├── CLAUDE.md          # its rules for agents (AGENTS.md beside it includes this)
│   ├── src/
│   │   ├── data/          # bundle.ts: reads a data bundle (manifest and Parquet cells)
│   │   ├── scoring/       # curves.ts: scoring curves; engine.ts: the scorer for one hex cell; region.ts: the fast scorer for the whole region; explain.ts: one cell's score, factor by factor, with its rank. All reproduce the golden test cases, as the Python reference scorer does
│   │   ├── profile/       # storage.ts: the preference profile in the browser's storage and the link
│   │   ├── features/factors/  # FactorTree (the treemap with sliders), treemap (the layout), level (what each level shows), colours, QuickLook (the hover card), WhyPanel (the reasons for a hex cell's score)
│   │   ├── features/map/  # HexMap (the basemap with the hex cells over it), hexcells (shapes and colours), colour, Legend
│   │   └── generated/     # TypeScript types from shared/schemas (generated)
│   ├── serve-bundles.ts   # serves data/published/ at /bundles/ in dev and preview
│   └── e2e/               # the Playwright tests, and a small data bundle (fixtures/) to load
├── shared/
│   ├── schemas/           # JSON Schema exported from the Pydantic models (generated)
│   └── fixtures/scoring/  # the golden test cases, written by hand: 15 JSON files and a README
├── catalogue/             # the factor catalogue
│   ├── README.md          # the field reference, and how it is checked
│   ├── factors.yaml       # the factor tree, down to measured indicators
│   └── datasets.yaml      # every dataset, with its tier and licence
└── docs/
    ├── README.md          # index of all documents
    ├── conceptualisation.md  # the original idea document
    ├── glossary.md        # project terms in plain words
    ├── vision.md          # goals, target users, not-now list, MVP success criteria
    ├── progress.md        # now / next / blocked, and a dated log
    ├── roadmap.md         # phases, steps, spikes, exit criteria
    ├── backlog.md         # features to add, by phase
    ├── decisions.md       # the decision register, D01–D19
    ├── tech-stack.md      # every technology and why
    ├── architecture.md    # system diagram, contracts, planned layout
    ├── interface.md       # progressive disclosure, visual factor tree
    ├── codemap.md         # this file
    ├── factors/           # the factor explorer and research notes (step 0.2)
    │   ├── README.md            # how to open, refresh, test and publish the explorer
    │   ├── explorer.html        # the factor explorer page
    │   ├── explorer-core.js     # its logic, without drawing
    │   ├── embed-catalogue.mjs  # copies the catalogue's two files into the page
    │   ├── artifact-page.mjs    # writes the copy published as an Artifact
    │   ├── *.test.mjs           # tests, run with Node's test runner
    │   ├── rankings.md          # the published rankings, rated for credibility
    │   └── research-notes.md    # research tables from the Phase 0 plan
    ├── methodology/
    │   ├── hard-to-measure.md  # the evidence ladder for factors without a direct measure
    │   ├── scoring.md     # spatial framework and scoring method v0
    │   └── validation.md  # how the data and the method are checked
    ├── plans/             # implementation plans, one per work item
    │   ├── 2026-10-24-catalogue-format.md
    │   ├── 2026-10-24-factor-explorer.md
    │   ├── 2026-10-24-transport-research.md
    │   └── 2026-10-28-scaffold.md
    ├── spikes/            # one page per feasibility experiment (step 0.4)
    │   ├── S1-ptal.md
    │   ├── S2-crime.md
    │   ├── S3-sales-and-rents.md
    │   ├── S4-routing.md
    │   ├── S5-noise-aggregation.md
    │   ├── S6-places.md
    │   ├── S7-culture-ladder.md
    │   └── S8-food-signals.md
    └── specs/             # design specs, one per work item
        ├── 2026-10-24-catalogue-format.md
        ├── 2026-10-24-factor-explorer.md
        ├── 2026-10-24-transport-research.md
        ├── 2026-10-25-community-research.md
        ├── 2026-10-25-daily-amenities-research.md
        ├── 2026-10-25-digital-connectivity-research.md
        ├── 2026-10-25-education-research.md
        ├── 2026-10-25-environment-research.md
        ├── 2026-10-25-housing-research.md
        ├── 2026-10-25-natural-hazards-research.md
        ├── 2026-10-25-safety-research.md
        ├── 2026-10-28-default-weights.md
        ├── 2026-10-28-health-care-research.md
        └── 2026-10-28-mvp-scope.md
```
