# Progress

## Now

- Step 0.1 is merged into `main` (#1).
- Step 0.2 has started. The [factor explorer spec](specs/2026-10-24-factor-explorer.md) is written on the local branch `feat/factor-explorer`, and the owner is reviewing it.

## Next

1. Once the owner approves the spec, write the factor explorer's implementation plan, then build it.
2. The rest of step 0.2: expand the factor catalogue top-down and bottom-up.
3. Before step 0.3:
   - Install uv and just with winget.
   - Set `PYTHONUTF8=1`, and point `UV_CACHE_DIR` at a folder on `E:`.
   - Optionally, upgrade Git for Windows from 2.41 and set `core.longpaths true`.

## Blocked

- Nothing.

## Log

### 2026-10-24

- **Step 0.2 started.** Wrote the [factor explorer spec](specs/2026-10-24-factor-explorer.md).
- **Step 0.1 merged** into `main` as pull request #1.
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
