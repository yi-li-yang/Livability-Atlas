# Tech stack

Status: both projects are scaffolded. The pipeline's tools (uv, Pydantic, Typer, ruff, pyright, pytest, Hypothesis, pre-commit) are pinned in `pipeline/uv.lock`, and the web app's (Vite, React, TypeScript, MapLibre, Tailwind, Biome, Vitest, Playwright, json-schema-to-typescript) in `web/package-lock.json`. just and GitHub Actions run both. The factor explorer (step 0.2) still loads its two libraries from cdnjs and runs its tests with Node's built-in test runner. The geospatial libraries are installed, and spike S1 showed that their Windows wheels work. h3, Shapely, pandas, pyarrow, pyproj, openpyxl and requests are main dependencies, since `atlas` imports them. GeoPandas, pyogrio, rasterio, DuckDB, QuackOSM and scipy stay in the `spikes` group until a pipeline task imports them. DuckDB and QuackOSM, rasterio, scipy and requests joined them for spikes S2 to S6. QuackOSM 0.19 does not work with DuckDB 2, so the group pins DuckDB below 2. Update this file whenever a tool is added, swapped or upgraded, and record large changes in [decisions.md](decisions.md#d03-tech-stack).

The "From" column gives the step or phase in which a tool arrives.

## Data pipeline (Python)

| Tool | Role here | Why | Alternatives considered | From |
| --- | --- | --- | --- | --- |
| [Python 3.13](https://docs.python.org/3.13/) with [uv](https://docs.astral.sh/uv/) | Language and environment manager. The project lives in `pipeline/.venv`, separate from conda | Geospatial ecosystem; uv is fast and locks dependencies | conda (heavier, mixes with the base install), Poetry | 0.3 |
| [GeoPandas](https://geopandas.org/), [Shapely 2](https://shapely.readthedocs.io/), [pyogrio](https://pyogrio.readthedocs.io/) | Vector data | Standard, with Windows wheels | — | 0.4 (the first spike that imports them) |
| [rasterio](https://rasterio.readthedocs.io/), [exactextract](https://isciences.github.io/exactextract/) | Raster data; area-weighted means from raster to hex cell | Accurate weights for partly covered cells | rioxarray with manual weighting | 0.4 |
| [h3](https://uber.github.io/h3-py/) (v4) | The hex grid (D04) | Hierarchical, global, equal-sized cells | S2 cells, square grids | 0.4 (the first spike that imports them) |
| [DuckDB](https://duckdb.org/docs/) with its spatial extension, [pyarrow](https://arrow.apache.org/docs/python/) | Fast SQL over Parquet; Parquet reading and writing | Handles large tables on one machine | PostGIS, which needs a server | 0.4 (the first spike that imports them) |
| [QuackOSM](https://github.com/kraina-ai/quackosm) | Reading OpenStreetMap extracts from Geofabrik | Bulk and offline, with no API rate limits | Overpass API (rate-limited), pyrosm | 0.4 |
| [Overture Maps](https://docs.overturemaps.org/) Places, Foursquare Open Source Places | Points of interest, with brand tags | Permissive licences; read through DuckDB | Google Places, whose terms forbid storing | 0.4 |
| [r5py](https://r5py.readthedocs.io/) with GTFS timetables, or the [TfL Unified API](https://api.tfl.gov.uk/) | Station travel-time matrix; travel times to default places | Spike S4 decides (D10). r5py needs Java 21 | OpenTripPlanner, commercial routing APIs | 0.4 |
| [Pydantic v2](https://docs.pydantic.dev/) | Schemas for the factor catalogue and the data bundle, exported to JSON Schema | One definition, checked on both sides | dataclasses with jsonschema | 0.3 |
| [pandera](https://pandera.readthedocs.io/) | Table checks in the pipeline | Declarative checks on DataFrames | Great Expectations (heavier) | 0.4 |
| [Typer](https://typer.tiangolo.com/) | The `atlas` command line: fetch, build, publish, validate | Simple and typed | Click, argparse | 0.3 |
| [ruff](https://docs.astral.sh/ruff/), [pyright](https://microsoft.github.io/pyright/) | Linting, formatting, type checks | Fast; pyright matches VS Code's Pylance | flake8 with black, mypy | 0.3 |
| [pytest](https://docs.pytest.org/), [Hypothesis](https://hypothesis.readthedocs.io/) | Tests, including property tests for scoring | Property tests catch whole classes of scoring bugs | unittest | 0.3 |
| [scikit-learn](https://scikit-learn.org/), [LightGBM](https://lightgbm.readthedocs.io/) | ML for estimates and data QA | Standard and light | Deep learning frameworks, only for imagery later | Phase 2 |
| [Ollama](https://ollama.com/) with open-weight models under Apache-2.0 | LLM jobs in the pipeline | Free, local, and reproducible when pinned | Free API tiers, whose terms change | Phase 3 |

## Web app (TypeScript)

| Tool | Role here | Why | Alternatives considered | From |
| --- | --- | --- | --- | --- |
| [TypeScript](https://www.typescriptlang.org/docs/) (strict), [React](https://react.dev/), [Vite](https://vite.dev/) | App framework and build | Largest ecosystem; builds to static files | Next.js (its server features are not needed), SvelteKit | 0.3 |
| [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) | Base map | Open source, no per-view fees | Mapbox GL (licence and fees), Leaflet (slow with many hexagons) | 0.3 |
| [deck.gl](https://deck.gl/docs) `PolygonLayer`, with [h3-js](https://github.com/uber/h3-js) cell boundaries | Drawing and recolouring about 17,000 hex cells over the MapLibre basemap | One WebGL layer, recoloured at every weight change. `H3HexagonLayer` draws the same hexagons, but its package, `@deck.gl/geo-layers`, brings in glTF, ZIP and image parsers that `npm audit` flags (11 findings that the app could not reach), so it is left out | `H3HexagonLayer`, plain MapLibre layers | 1 (walking skeleton) |
| [OpenFreeMap](https://openfreemap.org/) (its light grey Positron style, which sits quietly under data), later [Protomaps](https://docs.protomaps.com/) | Basemap tiles | Free, with no key; Protomaps can be self-hosted | MapTiler, Mapbox (keys, fees) | 0.3 |
| [D3](https://d3js.org/) 7.9: d3-hierarchy, d3-shape and d3-transition | Treemap and sunburst layouts and drawing for the visual factor tree | Full control over sizing, drill-down and animation | ECharts (less control) | 0.2 (factor explorer, from cdnjs) |
| Categorical palette of the [Salt design system](https://www.saltdesignsystem.com/salt/foundations/color/categorical-colors) (J.P. Morgan, Apache-2.0) | One colour per factor in the visual factor tree, with tints for sub-factors | 20 colours of equal lightness, each carrying white text at 4.5:1 or more, with a full tint scale for both themes | Tableau 20 (busier mix of dark colours and pastels), IBM Carbon (14 colours, too few), Adobe Spectrum (designed for 6) | 0.2 (factor explorer) |
| [js-yaml](https://github.com/nodeca/js-yaml) 4.1 | Reads the embedded `catalogue/factors.yaml` and `catalogue/datasets.yaml` inside the factor explorer | The page keeps the catalogue as YAML, with no build step | Converting to JSON first, which needs a build step before step 0.3 | 0.2 (factor explorer, from cdnjs) |
| [Tailwind CSS](https://tailwindcss.com/docs), [shadcn/ui](https://ui.shadcn.com/) | Styling; accessible dropdowns, popovers, sheets and tabs | Accessible building blocks for progressive disclosure | MUI, Chakra UI | 0.3 (Tailwind), Phase 1 (shadcn/ui) |
| [Zustand](https://zustand.docs.pmnd.rs/) | State: the preference profile, kept in browser storage and the URL | Small and simple | Redux Toolkit | Phase 1 |
| [hyparquet](https://github.com/hyparam/hyparquet) | Reading Parquet data bundles in the browser | Pure JavaScript, and small. It reads Snappy natively, so the pipeline writes Snappy and the app needs no extra codec package | parquet-wasm, Arrow IPC, JSON | 1 (walking skeleton) |
| [json-schema-to-typescript](https://github.com/bcherny/json-schema-to-typescript) | Generating TypeScript types from the shared schemas | Keeps the pipeline and the web app in step | Hand-written types | 0.3 |
| [WebLLM](https://webllm.mlc.ai/) | In-browser LLM for plain-language input | Free and private | Free API tiers behind a proxy; bring your own key | Phase 4 (prototype earlier) |
| [Biome](https://biomejs.dev/), tsc, [Vitest](https://vitest.dev/), [Playwright](https://playwright.dev/) | Linting and formatting, type checks, unit and end-to-end tests | Fast; one tool for linting and formatting | ESLint with Prettier, Jest, Cypress | 0.3 |
| [npm](https://docs.npmjs.com/) | Packages | Already installed; one package needs nothing more | pnpm, worth reconsidering if workspaces arrive | 0.3 |

## Tooling and delivery

| Tool | Role here | Why | Alternatives considered | From |
| --- | --- | --- | --- | --- |
| [just](https://just.systems/man/en/) | One command runner for people, Claude and CI | Cross-platform | Make (not on Windows by default), npm scripts | 0.3 |
| [Node's test runner](https://nodejs.org/api/test.html) (`node --test`) | Tests for the factor explorer before the scaffold exists | Built into Node 24, so nothing is installed | Vitest, which arrives with the web app | 0.2 |
| [Google Antigravity](https://antigravity.google/docs/rules) | An optional second coding agent beside Claude Code | It loads the root `AGENTS.md`, which includes `CLAUDE.md`, so both follow one set of rules (D20) | Copies of the rules in `GEMINI.md`, which would drift | 0.2 |
| [pre-commit](https://pre-commit.com/) with ruff, Biome, [gitleaks](https://github.com/gitleaks/gitleaks) and a large-file check | Checks before each commit | Stops secrets and data from reaching a public repo | Husky | 0.3 |
| [GitHub Actions](https://docs.github.com/actions) | CI running `just check` | Free for public repos | — | 0.3 |
| [CLA Assistant](https://cla-assistant.io/) | CLA signatures on pull requests | The common choice on GitHub | — | Before the first outside contribution |
| GitHub Pages or Cloudflare Pages; [Cloudflare R2](https://developers.cloudflare.com/r2/) | Hosting the static site; data bundles once they outgrow the site | Free tiers; R2 charges no egress fees | Netlify, Vercel, S3 | Phase 1 |

## Later (Phase 4, when users need them)

| Tool | Role here | Why | Alternatives considered |
| --- | --- | --- | --- |
| [FastAPI](https://fastapi.tiangolo.com/), PostgreSQL with [PostGIS](https://postgis.net/) and [h3-pg](https://github.com/zachasme/h3-pg) | Accounts, saved preference profiles, server-side scoring for large regions | Python, like the pipeline; PostGIS is the standard spatial database | Supabase (hosted Postgres) |
| A routing service (r5 or similar) | Exact door-to-door times, buses included | Removes the limits of the in-browser estimate | Commercial routing APIs |
| A progressive web app, then native apps | Mobile | Reuses the web app first | — |

## Environment (Windows)

- Shells: PowerShell and Git Bash.
- `E:` is NTFS (D13).
- Set `PYTHONUTF8=1`, because the Windows code page is not UTF-8.
- Set `UV_CACHE_DIR` to a folder on `E:`, so uv can hard-link packages into `pipeline/.venv`.
- Install Java 21 only if spike S4 picks r5py.
- Git for Windows is 2.41: upgrade it when convenient, and set `core.longpaths true`.
