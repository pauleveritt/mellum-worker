Files: totals.py
render.py
export.py
Change:
- totals.py: in column_totals, ignore non-numeric cells. For each column, sum only the int/float values and return "" when a column has no numeric values. So column_totals([["a", 1], ["b", 2]]) must be ["", 3].
- render.py: give render_rows a keyword parameter mark_last=False. When mark_last is True, prefix the final rendered row with "TOTAL," so render_rows([[1, 2], [3, 4]], mark_last=True) is ["1,2", "TOTAL,3,4"]. Leave the default behaviour unchanged.
- export.py: give export_csv a keyword parameter totals=False. When totals is True, append a final row containing column_totals(rows) and render it marked as the total row, so export_csv([[1, 2], [3, 4]], totals=True) is "1,2\n3,4\nTOTAL,4,6" and export_csv([[1, 2], [3, 4]]) stays "1,2\n3,4".
Test command: uv run --offline pytest -q
Do not change: exports_legacy.py, test_export.py, pyproject.toml, or anything else.
Done when: the test command exits 0 and you have replied with the files changed and the test output.