# Golden test cases for the travel estimate

Fixed inputs with expected minutes, which the web app's estimator (`web/src/travel/estimate.ts`) and the Python reference (`pipeline/src/atlas/scoring/travel.py`) must both reproduce within 1e-9. The method is in [the spec](../../../docs/specs/2026-11-22-own-places.md). The expected numbers are worked by hand in each case's description: do not regenerate them from an engine.
