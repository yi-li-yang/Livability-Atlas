# Golden test cases for the travel estimate

Fixed inputs with expected minutes, which the web app's estimator (`web/src/travel/estimate.ts`) and the Python reference (`pipeline/src/atlas/scoring/travel.py`) must both reproduce within 1e-9. The method is in [the spec](../../../docs/specs/2026-11-22-own-places.md). The expected numbers are worked by hand in each case's description: do not regenerate them from an engine.

A place may carry `stations`, the links of the cell that holds it, as a cell does. They are read backwards, as the minutes from each station to the place, on foot or by bus (spike S9); the last leg from a station is the quicker of that and the straight walk. A case without them is a place outside the region's cells.
