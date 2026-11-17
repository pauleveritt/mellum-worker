Objective: Make the failing pytest tests pass in the repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-3l_abvtd/rung4 (git repo, branch: baseline commit 7f418cf). This is the ONLY writer — do not create worktrees.

Context:
- Files: export.py, render.py, totals.py, test_export.py, pyproject.toml.
- Run tests with: .venv/bin/python -m pytest -q
- Currently 3 failures:
  1. test_column_totals_ignores_text_cells -> column_totals([["a",1],["b",2]]) must == ["",3]; today it crashes summing int+str.
  2. test_render_marks_last_row_as_total -> render_rows([[1,2],[3,4]], mark_last=True) must == ["1,2","TOTAL,3,4"].
  3. test_export_appends_totals_row -> export_csv([[1,2],[3,4]], totals=True) must == "1,2\n3,4\nTOTAL,4,6".
- test_export_without_totals already passes and must keep passing: export_csv([[1,2],[3,4]]) == "1,2\n3,4".

Constraints:
- Keep the existing function signatures backward compatible (default behavior unchanged when new kwargs are omitted).
- Match the exact expected strings above (TOTAL marker is the literal "TOTAL" prefixed as an extra leading cell in the totals row).
- Do not edit test_export.py.

Acceptance criteria / validation:
- Run `.venv/bin/python -m pytest -q` and confirm all 4 tests pass. Do not claim success without this output.
- Report: files changed, the exact final pytest output line (e.g. "4 passed"), and any residual uncertainty.

Stop/ask: if the environment is broken (no .venv, pytest missing) or the task is ambiguous, stop and report the blocker instead of guessing.