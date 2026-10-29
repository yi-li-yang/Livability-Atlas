# Test fixtures

`bundles/london/` is the small data bundle that the web app's tests load: the 209 hex cells within
8 steps of Soho.

**The service level, the walk to a station, the five crime rates, and two options each of Faith and
Your community are real data** (TfL's PTAL,
NaPTAN with OpenStreetMap streets, and the police.uk rates, from `just data london`).
`walk-to-green-space` and `gp-walk` are **fabricated** from a formula in `make_fixture.py`, so that
the tests have factors in Environment and Health care to weigh. They say nothing about London. This bundle is never published, and no build reads it.

Regenerate it with `uv run --project pipeline python web/e2e/fixtures/make_fixture.py` after
`just data london`.
