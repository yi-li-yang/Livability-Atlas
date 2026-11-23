# Plan: score by the amount, never by rank

The design is in [the spec](../specs/2026-11-23-score-by-the-amount.md). Each step writes its tests first and sees them fail. Branch `feat/score-by-amount`.

1. **Models** (`pipeline/src/atlas/catalogue/models.py`):
   - `Ramp` gets `log` and `offset`. A log ramp needs t0 + offset > 0 and t1 + offset > 0, and an offset needs `log`.
   - A new `RegionRamp` (`better`, `log`, `offset`) joins the catalogue's curves.
   - `Percentile` goes.
   - The manifest's curves are the catalogue's without `region-ramp`, and a manifest ramp may say `from_region`. Each option of a choice indicator may carry its own curve.
2. **Ends** (`pipeline/src/atlas/publish/curves.py`, new): `region_ends(values)` and `resolve(curve, values)`, from the cells with homes. Tests:
   - whole areas are kept;
   - 1% is cut from cell values;
   - a count keeps 0;
   - cells with few homes are ignored;
   - `better: higher` works;
   - equal ends give no curve.
3. **Build** (`publish/bundle.py`): the manifest resolves each region ramp from its column, and each option's from its own column.
4. **Scorers:** the ramp's `log` and `offset` in `pipeline/src/atlas/scoring/engine.py` and `web/src/scoring/curves.ts`; the percentile goes from both, with `regionValues` and its fast path in `web/src/scoring/region.ts`. Choice options use their own curve. Golden fixtures:
   - a new `ramp-log.json`;
   - `percentile.json` is removed;
   - at least 15 cases are kept.
5. **Generated files:** `atlas schemas`, then `npm run generate`.
6. **The app:**
   - `describeCurve` and `startsHigherIsBetter`;
   - the legend's end labels for one measured indicator;
   - the value in "On the map".
7. **QA:**
   - `curve_span` handles the log scale.
   - `qa.md` lists the region ramps' ends.
   - A check of the ends.
8. **The factor explorer:** the shape list, its check and its wording, with tests; then `node docs/factors/embed-catalogue.mjs`.
9. **The catalogue:** the 38 curves and their reasons, and the shape table in `catalogue/README.md`; then `atlas validate`.
10. **Rebuild:**
    - `atlas build london` and its QA report.
    - The e2e fixture keeps the full bundle's ends.
11. **Documents:**
    - D25, with history lines on D06 and D22;
    - `scoring.md`, the glossary, `codemap.md`, the backlog and `progress.md`.

Then check: run all the checks, look at the map with rent, council tax, burglary and cafés alone, run e2e, review, and open the pull request.
