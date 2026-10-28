# CLAUDE.md: pipeline

Rules for the data pipeline, beyond the root [CLAUDE.md](../CLAUDE.md). The Python package is `atlas`, in `src/atlas/`.

- Run everything through `just` from the repo root (`just check`, `just test`, `just validate`, `just generate`).
- `src/atlas/catalogue/models.py` is the one definition of the catalogue files. Change a rule there, then run `just generate` and commit the regenerated `shared/schemas/`. Never edit a generated file.
- A rule about one factor or one dataset goes in `models.py`. A rule across records goes in `checks.py`.
- Open text files with `encoding="utf-8"`, and write generated files with `newline="\n"`.
- Write the test first, and see it fail. A data check needs a case that passes and a case that fails.
- One module per dataset and one per indicator family.
