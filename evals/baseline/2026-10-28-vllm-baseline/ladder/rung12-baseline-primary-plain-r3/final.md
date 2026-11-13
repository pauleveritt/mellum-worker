I have implemented the `/sum` endpoint as specified in `specs/phase-7-sum.md`. 

Changes made:
1. **app.py**: Added a new endpoint `@app.get("/sum")` that streams `numbers.txt`, sums the two columns, and returns JSON `{"col1": ..., "col2": ...}`.
2. **tests/test_app.py**: Added a test `test_sum_endpoint()` to verify the new endpoint returns the correct JSON structure and integer values.

The implementation uses only the standard library and respects the requirement to read `numbers.txt` line by line without loading it entirely into memory.

Let me know if you need further adjustments!