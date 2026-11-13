Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ql3n9x07/rung3

Task: rename the function `fetch_rows` to `load_rows` everywhere in this repo.

Known occurrences (verify by searching yourself, there may be more, e.g. in test_report.py, comments, or docs):
- rows.py: the `def fetch_rows(source)` definition
- report.py: the `from rows import fetch_rows` import and the call site `fetch_rows(source)`

Requirements:
1. Run `grep -rn fetch_rows .` (excluding .git) first and again after editing to confirm zero remaining occurrences.
2. Use the edit tool for changes. Do not rewrite whole files.
3. Do not change any other behavior, formatting, or naming.
4. Run `python -m pytest -q` (or `uv run pytest -q` if pytest is not directly available) and report the exact output.
5. Do not commit anything.

Report back: files changed with exact edits, final grep output, and exact pytest output.