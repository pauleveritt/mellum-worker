The report endpoint has been successfully implemented in `app.py`. It listens on `GET /report` and returns JSON with the required sums computed from the `tickets` table in `data.db`.

The endpoint uses bound parameters and correctly handles the logic:
- `open_total_cents`: Sum of `cents` where `archived_at IS NULL AND status = 'open'`
- `archived_total_cents`: Sum of `cents` where `archived_at IS NOT NULL`
- `all_time_total_cents`: Sum of all `cents`

You can test it with:
```bash
curl http://localhost:8000/report
```
or via the test client as shown earlier.

No changes were made to `models.py`, `templates/`, or `tests/` since the existing functionality remains intact and the new endpoint works independently. If you need to adjust tests or other files later, feel free to ask!