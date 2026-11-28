Work in the repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-nxx66yrf/rung4 (cwd). Make the failing tests in test_export.py pass WITHOUT changing test_export.py.

Current failures:
- totals.py::column_totals crashes on text cells; it must ignore non-numeric/text cells (treat them as absent) and return "" in that column position when no numeric values exist. Example: column_totals([["a", 1], ["b", 2]]) == ["", 3].
- render.py::render_rows(rows, mark_last=True) must render rows as comma-joined strings, and when mark_last is True prefix the LAST row with "TOTAL,". Example: render_rows([[1,2],[3,4]], mark_last=True) == ["1,2", "TOTAL,3,4"]. Default mark_last=False keeps current behavior: render_rows([[1,2],[3,4]]) == ["1,2","3,4"].
- export.py::export_csv(rows, totals=False) must pass totals through: when totals=True append a totals row computed with column_totals, rendered with mark_last=True. Example: export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6". When totals=False keep existing behavior: export_csv([[1,2],[3,4]]) == "1,2\n3,4".

A sensible implementation: render_rows should handle the total marker, and export_csv should build rows + totals row then render. Be careful that totals=False never adds a row.

Verify by running: uv run pytest -q
Do not modify test_export.py. When done, report the exact files changed and the pytest output.