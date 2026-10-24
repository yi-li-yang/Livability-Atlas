# Codemap

A map of the repository as it is now. It is kept by hand until the tree reaches about 100 files. After that, `just codemap` generates it from the first line of each directory's `README.md`. The planned layout is in [architecture.md](architecture.md#planned-layout).

```text
Livability-Atlas/
├── README.md              # what the project is, status, licences
├── CLAUDE.md              # operating manual for Claude Code
├── CONTRIBUTING.md        # how to contribute; the CLA; recipes
├── LICENSE                # AGPL-3.0
├── .gitignore             # keeps data/, .env files and build output out of git
├── .gitattributes         # line-ending normalisation
└── docs/
    ├── README.md          # index of all documents
    ├── conceptualisation.md  # the original idea document
    ├── glossary.md        # project terms in plain words
    ├── vision.md          # goals, target users, not-now list, MVP success criteria
    ├── progress.md        # now / next / blocked, and a dated log
    ├── roadmap.md         # phases, steps, spikes, exit criteria
    ├── backlog.md         # features to add, by phase
    ├── decisions.md       # the decision register, D01–D19
    ├── tech-stack.md      # every technology and why
    ├── architecture.md    # system diagram, contracts, planned layout
    ├── interface.md       # progressive disclosure, visual factor tree
    ├── codemap.md         # this file
    ├── methodology/
    │   ├── scoring.md     # spatial framework and scoring method v0
    │   └── validation.md  # how the data and the method are checked
    └── specs/             # design specs, one per work item
        └── 2026-10-24-factor-explorer.md
```
