# CLAUDE.md: web

Rules for the web app, beyond the root [CLAUDE.md](../CLAUDE.md). It is Vite, React and TypeScript in strict mode, in `src/`.

- Run everything through `just` from the repo root (`just check`, `just dev`, `just build`, `just e2e`, `just generate`).
- `src/generated/` is made from `shared/schemas/` by `just generate`. Never edit it. To change a type, change the Pydantic model in `pipeline/src/atlas/catalogue/models.py`.
- The user's weights, hard limits and places stay in the browser. Nothing here sends them anywhere (D08).
- Write the test first, and see it fail. A component test checks what the user sees, not how the component is built.
- Words the app shows must be plain to a newcomer, in British English, and use the glossary's terms.
- One feature per folder in `src/features/`.
