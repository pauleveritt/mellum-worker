Work only in the current directory (the repo root). Make the failing tests in test_export.py pass. Do NOT modify test_export.py or exports_legacy.py.

The tests are the full specification:
1. test_export_without_totals: export_csv([[1, 2], [3, 4]]) == "1,2\n3,4"  (already passes; keep it passing)
2. test_column_totals_ignores_text_cells: column_totals([["a", 1], ["b", 2]]) == ["", 3]  (text cells must be skipped in the sum, not concatenated or raising)
3. test_render_marks_last_row_as_total: render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]  (add an optional mark_last parameter; when True, prefix the last rendered row with "TOTAL,")
4. test_export_appends_totals_row: export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"  (add an optional totals parameter; when True, append a totals row built from column_totals over all data rows, marked via render_rows mark_last)

Files involved: export.py, render.py, totals.py. Keep render_rows(rows) working with no extra args (test 1 must still pass), and make the totals-only computation use numeric cells only.

Run `.venv/bin/python -m pytest -q` and confirm all 4 tests pass before you finish. Report: the exact test command output summary and the final contents/diff of the three files you changed.