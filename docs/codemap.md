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
│   │   └── catalogue/     # models.py (the one definition of the catalogue files), checks.py, load.py, schema.py
│   ├── tests/
│   └── notebooks/         # spike scripts: throwaway, never imported by the package
├── web/                   # the web app: Vite, React and TypeScript
│   ├── CLAUDE.md          # its rules for agents (AGENTS.md beside it includes this)
│   ├── src/
│   │   ├── features/map/  # the MapLibre basemap of London
│   │   └── generated/     # TypeScript types from shared/schemas (generated)
│   └── e2e/               # the Playwright smoke tests
├── shared/
│   └── schemas/           # JSON Schema exported from the Pydantic models (generated)
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
        └── 2026-10-28-health-care-research.md
```
