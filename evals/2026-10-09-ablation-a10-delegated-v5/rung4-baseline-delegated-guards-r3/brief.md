Goal: make the FAILING tests in this repo pass.

Repo (cwd): /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-67cpamtd/rung4

Current state: `python -m pytest -q` → 3 failed, 1 passed. Failures:
- totals.py::column_totals raises TypeError on text cells; test expects column_totals([["a",1],["b",2]]) == ["", 3]
- render.py::render_rows does not accept keyword `mark_last`; test expects render_rows([[1,2],[3,4]], mark_last=True) == ["1,2","TOTAL,3,4"]
- export.py::export_csv does not accept keyword `totals`; test expects export_csv([[1,2],[3,4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"

Constraints:
- Do NOT modify test_export.py. The tests are the spec.
- Minimal change: edit only export.py, render.py, totals.py.
- Keep existing default behavior: export_csv([[1,2],[3,4]]) == "1,2\n3,4" (no totals row) and render_rows([[1,2]]) == ["1,2"].
- Use the repo venv: `.venv/bin/python -m pytest -q` (pyproject requires-python >=3.14).

Steps: read the files, run pytest to see the failures, implement the minimal fix, then run `.venv/bin/python -m pytest -q` until it reports 4 passed.

Report back exactly: files changed, the final pytest summary line, and any uncertainty. Do not claim success without the pytest output.