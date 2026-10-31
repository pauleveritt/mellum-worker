The specs for phase 6 have been implemented.

Changes made:
- `app.py`: Added `/report` endpoint that queries `data.db` and returns JSON with `open_total_cents`, `archived_total_cents`, and `all_time_total_cents`.
- `tests/test_app.py`: Added `test_report_endpoint` to verify the new endpoint using the current data from `data.db`.

The endpoint is now functional and returns:
```json
{
  "open_total_cents": 500,
  "archived_total_cents": 1000,
  "all_time_total_cents": 2099
}
```