Implemented the `/report` endpoint as specified. The endpoint queries the `tickets` table in `data.db` and returns JSON with the three integer-cent sums:
- `open_total_cents`
- `archived_total_cents`
- `all_time_total_cents`

Changes made:
1. Added `/report` route to `app.py` with proper database queries using bound parameters.
2. Updated `tests/test_app.py` to include a test for the new endpoint, which now passes with the correct sums (open: 500, archived: 1000, all_time: 2099).

The implementation follows all requirements: uses only the standard library `sqlite3`, discovers the schema dynamically, avoids float values, and uses bound parameters for any filters.