In the repository at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ugd8rtvh/rung3, rename the function `fetch_rows` to `load_rows` everywhere.

Requirements:
- Edit rows.py: rename `def fetch_rows(...)` to `def load_rows(...)`. Keep the body identical.
- Edit report.py: change `from rows import fetch_rows` to `from rows import load_rows`, and update the call `fetch_rows(source)` to `load_rows(source)`.
- Do not change any other behavior, signatures, or files.
- Do not touch test_report.py (it implicitly tests via report()).

Verification (required, run and report exact output):
1. `grep -rn "fetch_rows" . --include="*.py"` must return nothing.
2. Run `python -m pytest -q` (or `.venv/bin/python -m pytest -q`) and report the result.

Return: the exact diff (git diff) and the exact pytest output. Keep the response concise.