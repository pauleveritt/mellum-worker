Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-35fmopef/rung3

Bounded task: rename the function `fetch_rows` to `load_rows` everywhere in this repository.

Known occurrences (verify yourself with grep):
- rows.py:1 — the function definition `def fetch_rows(source):`
- report.py:1 — `from rows import fetch_rows`
- report.py:5 — the call `fetch_rows(source)`
- test_report.py imports `report` only, but check for `fetch_rows` there too.

Constraints:
- Change only the identifier `fetch_rows` -> `load_rows`. Do not change behavior, formatting, or anything else.
- Do not rename unrelated names, do not create new files, do not commit.
- Use grep (e.g. `grep -rn "fetch_rows" .`) before and after; the after-check must return no matches.

Verification (required, run it and report the exact command + output):
1. `grep -rn "fetch_rows" .` → must print nothing (exit 1).
2. `python -m pytest -q` (or `uv run pytest -q` if plain pytest lacks deps) → tests must pass. If the venv is needed, `.venv/bin/python -m pytest -q`.

Report back concisely: files changed, the exact verification commands with their output, and any residual risk or blocker.