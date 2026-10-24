# Factor explorer and research notes

Tools and notes for building the factor catalogue in step 0.2 of Phase 0.

| File | What it is |
| --- | --- |
| [explorer.html](explorer.html) | The factor explorer: the factor tree drawn as a treemap and as a sunburst, with weight sliders. Its design is in the [spec](../specs/2026-10-24-factor-explorer.md) |
| `explorer-core.js` | The explorer's logic, without any drawing |
| `embed-catalogue.mjs` | Copies `catalogue/factors.yaml` into the page |
| `artifact-page.mjs` | Writes the copy of the page that is published as an Artifact |
| `*.test.mjs` | The tests, run with Node's built-in test runner |
| [research-notes.md](research-notes.md) | Starting points for the rest of step 0.2, carried over from the Phase 0 plan |

## Open the explorer

Open `explorer.html` in a browser. It needs an internet connection for D3 and js-yaml. The owner reviews the published Artifact.

## After editing the catalogue

```sh
node docs/factors/embed-catalogue.mjs
node --test "docs/factors/*.test.mjs"
```

Then publish the Artifact again. `node docs/factors/artifact-page.mjs <output.html>` writes the Artifact copy, which is published with `explorer-core.js` beside it.
