Objective: rename the identifier `fetch_rows` to `load_rows` everywhere in this repository. Pure rename; no behavior change.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-8e2sei4r/rung3

Authority / edit boundary: you may edit any file in this cwd except `.pi/` and `.venv`/cache dirs. Do not add, delete, or reformat unrelated code. Do not rename other identifiers, do not touch test expectations, do not create new files.

Known occurrences to fix:
- rows.py: `def fetch_rows(source):` -> `def load_rows(source):`
- report.py line 1: `from rows import fetch_rows` -> `from rows import load_rows`
- report.py: call `fetch_rows(source)` -> `load_rows(source)`

Constraints:
- Do NOT do a blind repo-wide substring replace that could corrupt unrelated text; verify each occurrence you change is the identifier.
- Preserve surrounding formatting and the public behavior exactly.

Validation (must run and report raw output):
1. `grep -rn "fetch_rows" .` (ignore .pi and .venv) must return no matches. Exit status 1 / empty output is success.
2. `uv run pytest -q` must pass (1 test).
3. `git diff` must show only the rename.

Stop/ask conditions: if you find `fetch_rows` in a place where renaming would change externally visible API behavior beyond this repo, or if pytest fails for a reason unrelated to the rename, stop and report instead of guessing.

Expected output report: status; files changed with the exact diff; raw grep result; raw pytest result; any residual risk or uncertainty.