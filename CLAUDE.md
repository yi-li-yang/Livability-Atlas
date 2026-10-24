# CLAUDE.md

Operating manual for Claude Code in this repository. Keep it under 150 lines.

## The project

Livability Atlas is an open-source tool that answers "where should I live?". An offline Python data pipeline turns open datasets into measured indicators per hex cell and publishes a static data bundle per region. A React web app scores every hex cell in the browser by the user's preference profile. The first region is London. The repo owner is the first user, but everything is built for any user.

The project is in **Phase 0**: decisions, factor catalogue, spikes and scaffold. See [docs/roadmap.md](docs/roadmap.md).

## Start and end of every session

- **Start:** read "Now" in [docs/progress.md](docs/progress.md). Look up unfamiliar terms in [docs/glossary.md](docs/glossary.md).
- **End:** update "Now / Next / Blocked" in `docs/progress.md` and add a dated log entry, newest first.

## Where things are

- `docs/`: the living documents. The index is [docs/README.md](docs/README.md).
- The planned layout (`catalogue/`, `pipeline/`, `web/`, `shared/`) is in [docs/architecture.md](docs/architecture.md#planned-layout). The current tree is in [docs/codemap.md](docs/codemap.md).
- `data/` is gitignored. `ATLAS_DATA_DIR` overrides its location.

## Commands

Step 0.3 adds a `justfile`, and every command (setup, check, test, validate, build, dev, docs) will then run through `just`. Until then:

- `node --test "docs/factors/*.test.mjs"` runs the factor explorer's tests.
- `node docs/factors/embed-catalogue.mjs` refreshes the explorer after an edit to `catalogue/factors.yaml`.

## Living documents: what to update when

| When | Update |
| --- | --- |
| A decision is made or changed | `docs/decisions.md`: edit the entry in place and add a dated history line |
| A tool is added, swapped or upgraded | `docs/tech-stack.md` |
| An idea comes up or a feature ships | `docs/backlog.md` |
| A milestone moves | `docs/roadmap.md` |
| The directory structure changes | `docs/codemap.md` |
| A new term appears | `docs/glossary.md`, with one meaning per term, under "In the app" if the app shows it |
| Every session | `docs/progress.md` |

Specs go to `docs/specs/YYYY-MM-DD-topic.md` and implementation plans to `docs/plans/YYYY-MM-DD-topic.md`. This overrides the superpowers default of `docs/superpowers/...`.

## Task loop

1. Pick the top item under "Next" in `docs/progress.md`.
2. Write a spec with `superpowers:brainstorming`, then a plan with `superpowers:writing-plans`. A small item needs only a paragraph.
3. Branch: `feat/`, `data/`, `docs/`, `fix/` or `spike/`.
4. Build with `superpowers:test-driven-development`.
5. Verify with `just check`, run the pipeline or app, and look at the map (`superpowers:verification-before-completion`).
6. Review with `/code-review` or `superpowers:requesting-code-review`.
7. Merge through a PR with green CI, squash-merged.
8. Update the living documents.

Recipes for adding a factor, a dataset or a region are in [CONTRIBUTING.md](CONTRIBUTING.md#recipes). After a recipe has been done by hand twice, turn it into a command in `.claude/commands/`.

## Conventions

- Write British English in docs and UI text.
- Use the glossary's terms. Each thing keeps one name in code, docs and UI. Words the app shows (the glossary's "In the app" part) must be clear to a newcomer, with no jargon. Jargon is fine only in words for contributors.
- Plans carry no dates or durations. Phases, cycles and spikes end when their checks pass.
- Commit messages follow Conventional Commits.
- Keep files small and focused: one module per dataset and one per indicator family.
- Generated files say "do not edit" at the top.

## Guardrails

- **The repo is public.** Never push or open a PR without the owner's go-ahead.
- Never commit anything under `data/`, any `.env` file, secrets, or anyone's personal places.
- Every dataset needs a licence entry before use. Public builds use only datasets whose licences allow redistribution and commercial use (D07).
- A user's places and preference profile stay in their browser (D08).
- The livability score stays a weighted sum that anyone can inspect. ML may only produce measured indicators or estimates, each labelled ([methodology/scoring.md](docs/methodology/scoring.md)).
- The interface follows progressive disclosure: the answer at the surface, details on demand ([interface.md](docs/interface.md)).
- Community composition is framed as presence of a group the user chooses, and as diversity, never as "fewer of group X" (D08).

## Environment (Windows)

- Shells: PowerShell and Git Bash. In Git Bash, give `gh api` endpoints without a leading slash, or the path gets rewritten.
- `E:` is NTFS (D13). Python comes from uv (3.13, in `pipeline/.venv`), separate from the conda base install.
- Set `PYTHONUTF8=1`, and pass `encoding="utf-8"` when opening text files, because the Windows code page here is not UTF-8.
- Set `UV_CACHE_DIR` to a folder on `E:`, so uv can hard-link packages instead of copying them.
