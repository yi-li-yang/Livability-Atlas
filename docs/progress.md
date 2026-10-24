# Progress

## Now

- Phase 0, step 0.1 (foundations) is reviewed and approved. The branch `docs/phase-0-foundations` is pushed, with a pull request open against `main`.

## Next

1. Squash-merge the step 0.1 pull request. There is no CI yet; step 0.3 adds it.
2. Step 0.2: build the factor explorer on the seed factor tree, then expand the factor catalogue top-down and bottom-up.
3. Before step 0.3:
   - Install uv and just with winget.
   - Set `PYTHONUTF8=1`, and point `UV_CACHE_DIR` at a folder on `E:`.
   - Optionally, upgrade Git for Windows from 2.41 and set `core.longpaths true`.

## Blocked

- Nothing.

## Log

### 2026-10-24

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
