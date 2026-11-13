Renamed `fetch_rows` to `load_rows` in all occurrences:
- Updated `rows.py`: changed function definition from `fetch_rows` to `load_rows`
- Updated `report.py`: changed import from `fetch_rows` to `load_rows` and function call from `fetch_rows(source)` to `load_rows(source)`

Ran tests successfully:
```
.                                                                     [100%]
1 passed in 0.00s
```

All done.