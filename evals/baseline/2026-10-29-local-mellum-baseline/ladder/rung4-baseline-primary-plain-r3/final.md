The failing test has been fixed. All tests pass:

```
$ pytest -v
...
test_export.py::test_export_without_totals PASSED
test_export.py::test_column_totals_ignores_text_cells PASSED
test_export.py::test_render_marks_last_row_as_total PASSED
test_export.py::test_export_appends_totals_row PASSED
```