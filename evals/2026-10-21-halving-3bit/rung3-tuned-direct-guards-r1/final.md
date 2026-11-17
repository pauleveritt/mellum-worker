Rename `fetch_rows` to `load_rows` has been applied across the codebase:

- `rows.py` now defines `load_rows` function.
- `report.py` imports `load_rows` and uses it.
- `test_report.py` remains unchanged, testing the updated `report` function.

The test `test_report.py` now passes:

```
test_report.py .                                                         [100%]

============================== 1 passed in 0.00s ===============================
```

All requirements satisfied.