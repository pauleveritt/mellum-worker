Renamed `fetch_rows` to `load_rows` in `rows.py` and updated all references in `report.py`.

**Changed files:**
- `rows.py`: function `fetch_rows` renamed to `load_rows`.
- `report.py`: import changed from `fetch_rows` to `load_rows`, and call updated from `fetch_rows(source)` to `load_rows(source)`.

**Test output:**
```
.                                                                        [100%]
1 passed in 0.00s
```