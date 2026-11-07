Task: rename the function `fetch_rows` to `load_rows` everywhere in this repository.

Repo root: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-mphauhc8/rung3

Known occurrences (verify yourself with grep, do not trust this list blindly):
- rows.py: `def fetch_rows(source):` -> `def load_rows(source):`
- report.py: `from rows import fetch_rows` -> `from rows import load_rows`
- report.py: call site `fetch_rows(source)` -> `load_rows(source)`
- test_report.py has no direct reference (imports `report`).

Requirements:
1. Rename the definition and ALL references/imports/call sites. Do not rename unrelated things or change any other behavior.
2. After editing, run `grep -rn "fetch_rows" . --include='*.py' --include='*.md' --include='*.toml'` and confirm it returns no matches.
3. Run the tests with `.venv/bin/python -m pytest -q` (or `uv run pytest -q` if that fails) and confirm they pass.
4. Do not touch anything under .venv, .git, or .pi.

Report back concisely: the files changed, the exact grep command and its (empty) output, and the exact test command and its pass/fail result.