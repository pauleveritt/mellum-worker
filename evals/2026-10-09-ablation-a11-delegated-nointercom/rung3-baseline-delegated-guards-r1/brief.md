In the repository at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-9rnrbg56/rung3, rename the function `fetch_rows` to `load_rows` everywhere.

Known occurrences:
- rows.py: definition `def fetch_rows(source):`
- report.py: import `from rows import fetch_rows` and call site `fetch_rows(source)`

Requirements:
- Update every occurrence across all Python files (do not touch .venv or .git).
- Do not change any other behavior, signatures, or formatting.
- After editing, run `grep -rn "fetch_rows" . --exclude-dir=.venv --exclude-dir=.git` and confirm there are zero matches.
- Run the test suite with `pytest -q` (or `python -m pytest -q` if pytest isn't on PATH) and confirm it passes.

Report back: files changed, exact edits made, the grep result, and the pytest output.