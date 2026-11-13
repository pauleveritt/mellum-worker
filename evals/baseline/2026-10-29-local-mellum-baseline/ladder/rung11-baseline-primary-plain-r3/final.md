Successfully implemented the report endpoint as specified in specs/phase-6-report.md.

Changes made:
1. Added `/report` endpoint in `app.py` that connects to `data.db`, computes open_total_cents, archived_total_cents, and all_time_total_cents using bound parameters, and returns JSON.
2. Added a test case `test_report_endpoint` in `tests/test_app.py` to verify the endpoint returns the correct sums based on the current database content.
3. All existing tests pass (`pytest tests/test_app.py` results in 2 passed tests).

The implementation follows the spec: uses standard library `sqlite3`, respects bound parameters, and only modifies allowed files (`app.py`, `tests/test_app.py`). No changes made to `models.py` or `templates/` since they are not required for this endpoint.