# Architecture

Status: planned (D02, accepted). `catalogue/`, `pipeline/` (its command line, catalogue models and checks), `shared/schemas/` and `web/` (a basemap of London, and types generated from the schemas) exist. The rest is built from Phase 1.

## Overview

```text
catalogue/*.yaml   factor tree, datasets, regions (validated in CI)
      │
      ▼
data pipeline (Python, offline)
  fetch         → data/raw (cached, checksum recorded)
  load + clean  → aggregate to hex cells (region + 2 km buffer zone)
  indicators    → validate (dataset checks, cross-checks, known-fact assertions)
  routing       → station travel-time matrix; travel times to default places
  publish       → data/published/<region>/<version>/  (the data bundle)
      │
      ▼  static files on a CDN
web app (React, in each user's browser)
  load the data bundle
  → apply the preference profile (weights, hard limits, places; kept in the browser)
  → estimate travel times to the user's places
  → score every hex cell (TypeScript)
  → draw the hexagon map, the visual factor tree, the ranked neighbourhoods
    and the hex cell detail, one layer at a time
```

## Components

- **Factor catalogue** (`catalogue/`). YAML files, validated in CI:
  - `factors.yaml`: the factor tree down to measured indicators, with scoring curves, preference types and default weights
  - `datasets.yaml`: every dataset and published ranking, with its tier, licence, attribution, date and what it can tell us
  - `regions/<region>.yaml`: each region's boundary, grid, buffer zone and default places
  - `presets/`: ready-made preference profiles
- **Data pipeline** (`pipeline/`, Python package `atlas`). It runs offline. It fetches and caches datasets, aggregates them to hex cells over the region and its buffer zone, computes and validates measured indicators, computes travel times, and publishes a data bundle. Its command line is `atlas fetch / build / publish / validate`.
- **Data bundle** (`data/published/<region>/<version>/`). Static files, and the only thing the web app reads.
- **Web app** (`web/`, React + TypeScript). It loads a data bundle, applies the user's preference profile, estimates travel times to the user's places, and scores every hex cell. It then draws the map, the visual factor tree, the ranked neighbourhoods and the layers of detail.

## The data bundle

| File | Contents |
| --- | --- |
| `manifest.json` | Factor tree, scoring curves, preference types, datasets, licences and dates |
| `cells.parquet` | One row per hex cell, one column per measured indicator |
| `cell-stations.parquet` | For each hex cell, the stations within a 15-min walk and the walking minutes to each |
| `station-matrix.parquet` | Station-to-station public-transport times, including average waits and changes |
| `areas.geojson` | Neighbourhood outlines and names |
| `qa.md` | The QA report: checks, coverage, and changes since the last build |

## Contracts

- **Manifest schema.** It is defined once in Pydantic, in the pipeline, and exported to JSON Schema in `shared/schemas/`. TypeScript types are generated from it into `web/src/generated/`, and CI checks that they are current.
- **Preference profile.** A JSON object holding:
  - a weight for each node of the factor tree
  - for each measured indicator, the direction, ideal range or choice
  - hard limits
  - up to 3 places

  It lives in the browser's storage and can be shared as a URL, without places unless the user includes them. Its schema also lives in `shared/schemas/`. It is kept readable and documented, so that an LLM can later turn plain-language wishes into a profile.
- **Scoring parity.** The TypeScript engine and its Python copy must both reproduce the golden test cases in `shared/fixtures/scoring/`.

## Privacy boundary

Nothing personal reaches the data pipeline or any server. A user's weights, hard limits and places stay in their browser. Travel times to the default places are public, and travel times to a user's own places are computed on their device.

## Travel times

Default places get exact travel times from the data pipeline. A user's own places get an estimate in the browser: the walk to a nearby station, the ride from the station-to-station matrix, then the walk to the place. Spike S4 chooses the engine that builds the matrix: r5py with GTFS timetables, or the TfL Journey Planner API (D10).

## Scaling

Each sub-factor draws on the best dataset tier available for a region: city, then country, then global. Each region builds and serves on its own, as one data bundle behind a CDN, listed in a region index. Zoomed out, the app switches to coarser H3 levels, or to city units at the across-cities scale. When a region outgrows the browser, its data moves to map tiles (PMTiles) or to server-side scoring (D16).

## Later (Phase 4)

FastAPI with PostgreSQL/PostGIS will hold accounts and saved preference profiles, and a routing service will give exact door-to-door times. The schemas stay the same, so the web app changes where it loads data from, not how it scores.

## Planned layout

```text
Livability-Atlas/
├── README.md  LICENSE  CONTRIBUTING.md  CLAUDE.md  AGENTS.md
├── justfile                # every command: setup, check, test, validate, build, dev, docs
├── .claude/settings.json   # shared permissions; commands/ added once a recipe repeats
├── .github/workflows/ci.yml
├── catalogue/              # factor catalogue: machine-readable, validated in CI
│   ├── factors.yaml        #   the factor tree, down to measured indicators and scoring curves
│   ├── datasets.yaml       #   every dataset and published ranking
│   ├── presets/            #   ready-made preference profiles
│   └── regions/london.yaml #   boundary, grid, buffer zone, default places
├── pipeline/               # Python package `atlas` (uv project)
│   ├── CLAUDE.md  AGENTS.md
│   ├── src/atlas/
│   │   ├── cli.py
│   │   ├── catalogue/      # Pydantic models and loaders
│   │   ├── datasets/       # one module per dataset, grouped by tier
│   │   │   ├── global/     #   OSM, Overture, satellite-derived data, GTFS
│   │   │   ├── countries/gb/  # Police.uk, Census, Land Registry, …
│   │   │   └── cities/london/ # PTAL, LAEI, cultural infrastructure map, …
│   │   ├── spatial/        # hex grid, buffer zone, aggregation to hex cells
│   │   ├── indicators/     # one module per indicator family
│   │   ├── routing/        # station matrix, travel times to default places
│   │   ├── scoring/        # Python copy of the scoring engine
│   │   ├── ml/             # from Phase 2: models that produce measured indicators
│   │   └── publish/        # data bundle writer and QA report
│   ├── tests/
│   └── notebooks/          # exploration and spikes; never imported by the package
├── web/                    # Vite + React + TypeScript, static build
│   ├── CLAUDE.md  AGENTS.md
│   ├── src/
│   │   ├── features/       # map, preferences, factor-tree, ranking, cell-detail
│   │   ├── scoring/        # the TypeScript scoring engine
│   │   ├── travel/         # in-browser travel-time estimate
│   │   ├── data/           # data bundle loading
│   │   └── generated/      # types generated from shared/schemas (do not edit)
│   └── e2e/
├── shared/
│   ├── schemas/            # JSON Schema exported from Pydantic
│   └── fixtures/scoring/   # golden test cases
├── docs/                   # living documents
└── data/                   # gitignored: raw/, interim/, published/
```
