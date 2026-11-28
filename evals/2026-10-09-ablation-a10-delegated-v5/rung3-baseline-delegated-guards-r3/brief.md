Task: Rename the function `fetch_rows` to `load_rows` everywhere in this repository (cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-9ugm831w/rung3).

Known occurrences (verify with grep before/after):
- rows.py line 1: `def fetch_rows(source):` -> `def load_rows(source):`
- report.py line 1: `from rows import fetch_rows` -> `from rows import load_rows`
- report.py line 5: call `fetch_rows(source)` -> `load_rows(source)`

Steps:
1. Run `grep -rn "fetch_rows" .` to find ALL occurrences.
2. Use the edit tool to rename each occurrence to `load_rows`. Do not change anything else.
3. Run `grep -rn "fetch_rows" .` again and confirm it returns nothing.
4. Run the test suite with `uv run pytest -q` (fall back to `.venv/bin/python -m pytest -q` if uv is unavailable) and report the exact result.

Report exactly: files changed, the final grep output, and the test command + its output.