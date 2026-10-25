# Transport research plan

A small item, so a short plan. The design and findings are in [the spec](../specs/2026-10-24-transport-research.md). Commands run from the repo root in Git Bash, with the scratchpad tools described in the [catalogue format plan](2026-10-24-catalogue-format.md#shared-setup).

1. **Research** each within-city measured indicator of Transport: its unit, curve and evidence, and each dataset's licence at its source.
2. **Code, test first.** In `docs/factors/explorer-core.js`, add TfL's licence to D07's allowed list, list a lookup's categories from best to worst, read a lookup by its unit, and keep numbers with their units. Run `node --test "docs/factors/*.test.mjs"` and see each new test fail, then pass.
3. **Catalogue.** Add the four datasets to `catalogue/datasets.yaml`, and fill in Transport's measured indicators in `catalogue/factors.yaml`. Check both files with the catalogue check from the catalogue format plan, Task 6, and expect `OK: no problems`. Run `node docs/factors/embed-catalogue.mjs`.
4. **Browser check.** Add the Transport step to the scratch browser check, and run it in Edge. Look at the PTAL tooltip's screenshot.
5. **Documents.** Update D07, `catalogue/README.md`, the glossary, the research notes, the codemap and the progress log. Run the documentation check.
6. **Publish and open the pull request.** Publish the Artifact again, push `data/transport-research`, and open the pull request. It merges on the owner's word.
