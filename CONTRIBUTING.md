# Contributing to Livability Atlas

Thank you for your interest. The project is in Phase 0: it is settling its decisions, factor catalogue and scoring method before writing code. Ideas, dataset suggestions and corrections are welcome now. Code contributions open once the scaffold exists (Phase 0, step 0.3).

## Before you start

Read, in this order:

1. [docs/glossary.md](docs/glossary.md): the project's terms.
2. [docs/vision.md](docs/vision.md): the goals, and what is out of scope for now.
3. [docs/decisions.md](docs/decisions.md): the decisions already made, and why.

## Licences and the CLA

- The code is licensed under AGPL-3.0 ([LICENSE](LICENSE)).
- The documentation is licensed under CC BY 4.0.
- Outside contributors sign a contributor licence agreement (CLA) before their first pull request is merged. The CLA keeps open the option of a paid edition alongside the open-source one. The CLA text and the CLA Assistant check will be published before the first outside contribution is merged.

## How changes are made

1. Open an issue that describes the change.
2. Create a branch: `feat/`, `data/`, `docs/`, `fix/` or `spike/`.
3. Write tests first, and keep files small and focused.
4. Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/).
5. Open a pull request. CI must pass, and changes are squash-merged.
6. Update the living documents your change affects (see [docs/README.md](docs/README.md)).

Never commit data files, `.env` files, secrets or personal locations.

## Recipes

These checklists define when a repeated job is done.

### Any task

- Tests were written first and pass, and `just check` is green (once the scaffold exists).
- The docs are updated.
- The diff contains no data, secrets or personal places.

### Add a factor

1. Tree node: plain name, description, default weight with its reason, parent.
2. Measured indicators, each with its unit, preference type, a scoring curve with its justification, a confidence label, and whether it is comparable across regions.
3. A dataset entry, with its tier and licence checked.
4. Fetching is idempotent and cached, and the checksum is recorded.
5. A documented method aggregates the data to hex cells.
6. QA checks run: range, nulls, coverage, at least one known-fact assertion, and a cross-check wherever an independent dataset exists.
7. A test runs on a small fixture.
8. The factor appears in the web app through the manifest alone, with no change to UI code: in the factor tree, in its dropdown and in the evidence layer.
9. The QA report and the progress log are updated.

### Add a dataset

Record its tier, URL, licence (checked against decision D07), attribution text, date and update cadence. Cache the raw file with its checksum, and list what the dataset can tell us.

### Add a region

1. Write `catalogue/regions/<region>.yaml`: boundary, grid, buffer zone, default places and neighbourhood boundaries.
2. Write a country adapter for that country's datasets, if none exists yet.
3. Build every default factor from the best available dataset tier, or mark it unavailable.
4. Produce a QA report.

Once the region recipe is proven (Phase 3), country adapters make good first contributions.
