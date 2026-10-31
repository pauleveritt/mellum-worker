Renamed `fetch_rows` to `load_rows` in `rows.py` and updated its usage in `report.py`. All tests pass:

```bash
$ pytest -v
...
test_report.py::test_report_joins_cells PASSED
```

The change has been applied successfully.