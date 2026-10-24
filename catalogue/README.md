# Factor catalogue

The machine-readable factor catalogue. The [glossary](../docs/glossary.md) defines its terms.

`factors.yaml` holds the factor tree, with every factor's default weight and the reason for it. Its first version is the seed tree from the Phase 0 plan. The datasets, the regions and the presets arrive in later steps.

## Checks

Until step 0.3, the [factor explorer](../docs/factors/README.md) checks `factors.yaml` whenever it loads, and lists any problem instead of drawing. From step 0.3, `atlas validate` checks the whole catalogue in CI.

After editing `factors.yaml`, refresh the explorer's copy and run its tests:

```sh
node docs/factors/embed-catalogue.mjs
node --test "docs/factors/*.test.mjs"
```
