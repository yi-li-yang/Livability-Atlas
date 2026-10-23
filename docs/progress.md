# Progress

## Now

- Phase 0, step 0.1 (foundations) is done on the local branch `docs/phase-0-foundations` and awaits the owner's review. Nothing has been pushed.

## Next

1. The owner reviews the step 0.1 documents. On the owner's go-ahead, push the branch and open a pull request.
2. Step 0.2: build the factor explorer on the seed factor tree, then expand the factor catalogue top-down and bottom-up.
3. Before step 0.3:
   - Install uv and just with winget.
   - Set `PYTHONUTF8=1`, and point `UV_CACHE_DIR` at a folder on `E:`.
   - Optionally, upgrade Git for Windows from 2.41 and set `core.longpaths true`.

## Blocked

- Nothing.

## Log

### 2026-10-23

- **Planning.** The Phase 0 plan went through five review rounds and was approved. Its decisions are recorded as D01–D19 in [decisions.md](decisions.md).
- **Environment.** `E:` was reformatted from exFAT to NTFS (D13), so Git now accepts the repo by file ownership.
- **Step 0.1.**
  - Committed the original concept document, which had never been committed.
  - Added the AGPL-3.0 licence and `.gitignore`.
  - Wrote the living documents, `CLAUDE.md`, `CONTRIBUTING.md` and a new README.
