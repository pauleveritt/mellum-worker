Files: totals.py
render.py
export.py

Change:
- totals.py: column_totals(rows) must sum only the numeric cells in each column and return "" for a column whose cells are all non-numeric. For [[1,2],[3,4]] it returns [4,6]. For [["a",1],["b",2]] it returns ["",3].
- render.py: render_rows(rows, mark_last=False) gains a keyword argument mark_last; when mark_last is True, prefix the last rendered row with "TOTAL,". render_rows([[1,2],[3,4]], mark_last=True) returns ["1,2","TOTAL,3,4"], and render_rows([[1,2],[3,4]]) still returns ["1,2","3,4"].
- export.py: export_csv(rows, totals=False) gains a keyword argument totals. When totals is True, append the column_totals(rows) row to rows and render the combined rows with mark_last=True; when totals is False, behaviour is unchanged. export_csv([[1,2],[3,4]], totals=True) returns "1,2\n3,4\nTOTAL,4,6".

Test command: uv run --offline pytest -q (run from the working directory)

Do not change: test_export.py, exports_legacy.py

Done when: the test command exits 0 and you have replied with the files changed and the test output.