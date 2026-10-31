Make the failing tests pass.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-qrigle9y/rung4
Test command (run from that directory): uv run --offline pytest -q
Success criterion: the command exits 0 (all tests in test_export.py pass).

Relevant files (do NOT modify test_export.py — it is the spec):
- export.py: export_csv(rows)
- totals.py: column_totals(rows)
- render.py: render_rows(rows)

Behavior the tests require:
- export_csv([[1, 2], [3, 4]]) == "1,2\n3,4"  (no totals row by default)
- column_totals([["a", 1], ["b", 2]]) == ["", 3]  (non-numeric cells are ignored; an all-text column totals to "")
- render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]
- export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"

Edit boundary: only export.py, totals.py, render.py. Keep changes minimal and consistent with the existing style.

After editing, run the test command and confirm exit 0. Report which files changed and the final test summary line.