Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-7b742u5k/rung3

Task: Rename the function `fetch_rows` to `load_rows` everywhere in this project.

Exact known occurrences (verify by grepping first):
- rows.py:1 — `def fetch_rows(source):` → `def load_rows(source):`
- report.py:1 — `from rows import fetch_rows` → `from rows import load_rows`
- report.py:5 — `fetch_rows(source)` → `load_rows(source)`

Steps:
1. Run `grep -rn "fetch_rows" . --include='*.py'` to confirm the full set of occurrences; note anything beyond the three above.
2. Make the edits in rows.py and report.py. Do not change behavior, signatures, or anything else.
3. Re-run the grep and confirm zero remaining `fetch_rows` matches (ignore .venv).
4. Run the test suite with `pytest -q` and paste the exact output.

Report back: files changed, the final grep result, and the exact pytest output. Do not mark complete if pytest fails — report the failure instead.