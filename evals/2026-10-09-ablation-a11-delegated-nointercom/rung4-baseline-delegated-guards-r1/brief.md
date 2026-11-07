Bounded coding task in the repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-dp3opego/rung4

GOAL: Make every test in test_export.py pass. Do NOT edit test_export.py, pyproject.toml, or uv.lock. Only edit the implementation modules: export.py, render.py, totals.py.

Current test run has 3 failures (1 passes). Run this to see them:
  .venv/bin/python -m pytest -q

Here is the full content of test_export.py (this is the specification — satisfy it exactly):

  from export import export_csv
  from render import render_rows
  from totals import column_totals


  def test_export_without_totals():
      assert export_csv([[1, 2], [3, 4]]) == "1,2\n3,4"


  def test_column_totals_ignores_text_cells():
      assert column_totals([["a", 1], ["b", 2]]) == ["", 3]


  def test_render_marks_last_row_as_total():
      assert render_rows([[1, 2], [3, 4]], mark_last=True) == ["1,2", "TOTAL,3,4"]


  def test_export_appends_totals_row():
      assert export_csv([[1, 2], [3, 4]], totals=True) == "1,2\n3,4\nTOTAL,4,6"

Required behavior:
1. render_rows(rows, mark_last=False) -> list[str].
   - Default: each row becomes a comma-joined string: "1,2".
   - If mark_last=True: render every row the same way, but the LAST row's string is prefixed with "TOTAL,". So [[1,2],[3,4]] -> ["1,2", "TOTAL,3,4"]. Empty rows -> [].
2. column_totals(rows) -> list where each entry is the sum of the NUMERIC cells in that column. Non-numeric cells (e.g. strings) are ignored. If a column has no numeric cells, its entry is the empty string "". Example: [["a",1],["b",2]] -> ["", 3]. Empty rows -> [].
   - Use numbers (int/float) as numeric; exclude bool. Keep it simple.
3. export_csv(rows, totals=False) -> str joined by "\n".
   - Default: just the rendered data rows (no total): [[1,2],[3,4]] -> "1,2\n3,4".
   - If totals=True: append one final line built as "TOTAL," + comma-joined column_totals(rows). Example: [[1,2],[3,4]] -> "1,2\n3,4\nTOTAL,4,6". (Do not use mark_last for this — the totals line is an extra appended row.)

Steps:
- Read export.py, render.py, totals.py first.
- Make the minimal edits to those three files.
- Run `.venv/bin/python -m pytest -q` and confirm "4 passed". If not, fix and rerun.
- Do not add new dependencies.

Report back: the exact final pytest output (the summary line), the files you changed, and the final content diff/changes. If you get stuck, report the exact error and what you tried.