Implemented the `/sum` endpoint to return column sums from `numbers.txt` as specified in specs/phase-7-sum.md.

Changes made:
1. Edited `app.py` to add the `/sum` route that streams `numbers.txt` and computes sums.
2. Edited `tests/test_app.py` to include a test for the new `/sum` endpoint.

The endpoint is now available at `/sum` and returns JSON `{"col1": sum, "col2": sum}`.

Let me know if you need further adjustments!