Renamed `fetch_rows` to `load_rows` in all occurrences:

- Updated `rows.py`: function definition changed from `fetch_rows` to `load_rows`.
- Updated `report.py`: import statement changed from `from rows import fetch_rows` to `from rows import load_rows`, and all calls to `fetch_rows(...)` were changed to `load_rows(...)`.

No other files contain the term `fetch_rows`. The changes are complete.