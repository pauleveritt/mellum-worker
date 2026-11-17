I have implemented the endpoint specified in `specs/phase-7-sum.md`:

1. **Added `/sum` endpoint** in `app.py` that streams `numbers.txt` line by line and returns the sums of the two columns as JSON.
2. **Added a test** for the new endpoint in `tests/test_app.py` that verifies the response status code and the correct sums (`col1: 249467231, col2: 250168086`).

The changes are consistent with the requirement to use only standard library and to avoid loading the entire file into memory.

Let me know if you need further adjustments!