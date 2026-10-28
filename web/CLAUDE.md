# CLAUDE.md: web

Rules for the web app, beyond the root [CLAUDE.md](../CLAUDE.md). It is Vite, React and TypeScript in strict mode, in `src/`.

- Run everything through `just` from the repo root (`just check`, `just dev`, `just build`, `just e2e`, `just generate`).
- `src/generated/` is made from `shared/schemas/` by `just generate`. Never edit it. To change a type, change the Pydantic model in `pipeline/src/atlas/catalogue/models.py`.
- The user's weights, hard limits and places stay in the browser. Nothing here sends them anywhere (D08).
- Write the test first, and see it fail. A component test checks what the user sees, not how the component is built.
- Words the app shows must be plain to a newcomer, in British English, and use the glossary's terms.
- One feature per folder in `src/features/`.
- The app reads a data bundle from `/bundles/` and nothing else: `just data london`, then `just dev`, serves `data/published/` there (`ATLAS_BUNDLES_DIR` overrides it). The Playwright tests read a small bundle kept in `e2e/fixtures/bundles/`, which `e2e/fixtures/make_fixture.py` writes from the real one. A test in `pipeline/` fails if it goes stale.
- The hex cells are drawn with deck.gl's `PolygonLayer` and `h3-js` boundaries, not `H3HexagonLayer`: `@deck.gl/geo-layers` brings in glTF, ZIP and image parsers that `npm audit` flags, which the app never uses. Keep `npm audit` at zero.
- `npm run e2e` serves the last build and does not rebuild: use `just e2e`, or run `npm run build` first, or you test stale code.
- MapLibre 6 finds its worker script beside the bundle, where Vite does not put it, so `BaseMap.tsx` imports the worker with `?url` and calls `setWorkerUrl`. Without it the map builds and passes its tests, and draws a blank background. `e2e/smoke.spec.ts` guards this.
