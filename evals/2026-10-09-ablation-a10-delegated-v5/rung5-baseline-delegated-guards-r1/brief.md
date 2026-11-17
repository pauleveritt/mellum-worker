Repo root is the current working directory (a small Python project). Run tools/pytest with `.venv/bin/python -m pytest`.

BUG: The CSV export is missing the totals row. Three tests fail at baseline.

Current file contents:

export.py
    from render import render_rows


    def export_csv(rows):
        return "\n".join(render_rows(rows))

render.py
    def render_rows(rows):
        return [",".join(str(v) for v in r) for r in rows]

totals.py
    def column_totals(rows):
        if not rows:
            return []
        return [sum(r[i] for r in rows) for i in range(len(rows[0]))]

test_export.py (DO NOT MODIFY — it defines required behavior):
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

Required changes (minimal; keep default behavior unchanged):
1. totals.py — column_totals(rows) must sum only numeric cells; if a column contains any non-numeric (text) cell, return "" for that column. Empty rows -> [].
2. render.py — render_rows(rows, mark_last=False). When mark_last=True, the last rendered row is prefixed with "TOTAL": i.e. output becomes ["1,2", "TOTAL,3,4"]. Default mark_last=False must preserve current output.
3. export.py — export_csv(rows, totals=False). When totals=True, append a totals row built from column_totals(rows), rendering as "TOTAL," + comma-joined totals -> "TOTAL,4,6". Default totals=False must preserve current output.

HARD CONSTRAINTS:
- Do NOT modify test_export.py.
- Do NOT modify exports_legacy.py (legacy module, must stay byte-identical).
- Existing calls that omit the new keyword arguments must keep working.

DONE WHEN: `.venv/bin/python -m pytest -q` passes all 4 tests (0 failed).
REPORT BACK: the exact final pytest summary line, and the output of `git diff --stat`.