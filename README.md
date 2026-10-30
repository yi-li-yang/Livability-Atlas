# Livability Atlas

An open-source decision tool for one question: **where should I live?**

Livability Atlas gathers evidence about places, such as cost, transport, safety, environment, community and amenities. It scores every area by each user's own weights and hard limits. The map lights up the best areas, a ranked list names them, and every score explains itself, one layer of detail at a time.

One scoring engine serves two scales: neighbourhoods within a city, and cities across countries. The first region is London.

> **Status: Phase 1, the London MVP.** The data pipeline builds London's data bundle (41 measured indicators across ten factors, each build checked by a QA report), and the web app scores its 16,668 hex cells in the browser by the user's own weights and limits, on a desktop or a phone. **It is live at <https://yi-li-yang.github.io/Livability-Atlas/>.** [docs/progress.md](docs/progress.md) shows the current state, and [docs/roadmap.md](docs/roadmap.md) shows what comes next.

## New here?

1. [Glossary](docs/glossary.md): the project's terms in plain words.
2. [Vision](docs/vision.md): what the tool is for, its goals, and what it leaves out for now.
3. [Architecture](docs/architecture.md): how the data pipeline, the data bundles and the web app fit together.
4. [Decisions](docs/decisions.md): every project decision, with its reasons and history.

The full index of documents is in [docs/README.md](docs/README.md).

## How it works

1. An offline **data pipeline** in Python downloads open datasets and computes measured indicators for every hex cell of a region.
2. It publishes one **data bundle** per region as static files.
3. The **web app** loads a data bundle and scores every hex cell in the user's browser. A user's preferences and places never leave their device.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licences

| What | Licence |
| --- | --- |
| Code | [AGPL-3.0](LICENSE). Outside contributions need a contributor licence agreement (CLA) |
| Documentation | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Data bundles | Each dataset's own licence, e.g. ODbL for data derived from OpenStreetMap. The factor catalogue will list every dataset with its licence and attribution |
