Bounded rename task in cwd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-gbdv59f8/rung3.

Goal: rename the function `fetch_rows` to `load_rows` everywhere in this repo.

Known occurrences (verified before dispatch):
- rows.py line 1: `def fetch_rows(source):` -> `def load_rows(source):`
- report.py line 1: `from rows import fetch_rows` -> `from rows import load_rows`
- report.py line 5: `fetch_rows(source)` call -> `load_rows(source)`

Requirements:
1. Do not change any other behavior, names, formatting, or files.
2. Re-grep the repo (excluding .pi/) to confirm no `fetch_rows` occurrence remains.
3. Run `uv run pytest -q` and confirm it passes.
4. Do NOT git commit.

Return: exact files changed, the final grep result, the pytest output, and a `git diff` of the changes.