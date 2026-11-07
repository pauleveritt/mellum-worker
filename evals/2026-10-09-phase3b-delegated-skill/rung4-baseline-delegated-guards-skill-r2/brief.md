OBJECTIVE
Make the currently failing tests pass in this repository by fixing the implementation (not the tests).

REPO / CWD
/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-w6mqh_qo/rung4
Work in place on branch main. Python interpreter is .venv/bin/python (project requires Python >=3.14).

CURRENT STATE (evidence)
Running `.venv/bin/python -m pytest -q` gives 3 failed, 1 passed:
- totals.py::column_totals raises TypeError: sum() over int and str for rows like [["a", 1], ["b", 2]]
- render.py::render_rows() got an unexpected keyword argument 'mark_last'
- export.py::export_csv() got an unexpected keyword argument 'totals'

FILES
- test_export.py  (the spec — DO NOT MODIFY)
- totals.py       (column_totals(rows))
- render.py       (render_rows(rows, mark_last=False))
- export.py       (export_csv(rows, totals=False))

REQUIRED BEHAVIOR (from test_export.py)
1. export_csv([[1, 2], [3, 4]]) == "1,2\n3,4"
2. column_totals([["a", 1], ["b", 2]]) == ["", 3]   (non-numeric cells contribute nothing; a column with no numbers sums to "")
3. render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]   (the last row is prefixed with "TOTAL"; marked row cells follow the same comma-joining)
4. export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"   (append a totals row computed from column_totals, rendered with the TOTAL marker)

AUTHORITY / EDIT BOUNDARY
- You may edit totals.py, render.py, and export.py only.
- Do NOT modify test_export.py or pyproject.toml.
- Keep changes minimal and idiomatic; preserve the existing plain-function style.

VALIDATION (must run and show output)
From the repo root run: `.venv/bin/python -m pytest -q`
Success = 4 passed.

REPORT BACK
- Files changed and the exact final implementation of each changed function.
- The full pytest summary line proving 4 passed.
- Any assumptions you made.

STOP / ASK
If a requirement is genuinely ambiguous or a test appears wrong, stop and report the question instead of editing the tests.