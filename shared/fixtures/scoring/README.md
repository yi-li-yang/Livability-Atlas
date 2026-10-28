# Golden test cases for scoring

Fixed inputs with expected results, which the TypeScript engine of the web app and the Python reference scorer (`pipeline/src/atlas/scoring/engine.py`) must both reproduce within 1e-9. The format and the cases are described in [scoring.md](../../../docs/methodology/scoring.md#13-golden-test-cases).

The expected numbers are written by hand. Do not regenerate them from an engine: a change to the method changes them here, in the same pull request, with the arithmetic shown in the case's own comment.
