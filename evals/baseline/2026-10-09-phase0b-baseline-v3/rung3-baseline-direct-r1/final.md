Renamed `fetch_rows` to `load_rows` in all occurrences:

- Updated `rows.py`: changed function name from `fetch_rows` to `load_rows`.
- Updated `report.py`: changed import from `fetch_rows` to `load_rows` and updated function call accordingly.

Verification:
- No remaining `fetch_rows` references found (grep reported "No matches found").
- Tests pass: `uv run --offline pytest -q` output:
```
.                                                                        [100%]
1 passed in 0.00s
```

The task is complete.