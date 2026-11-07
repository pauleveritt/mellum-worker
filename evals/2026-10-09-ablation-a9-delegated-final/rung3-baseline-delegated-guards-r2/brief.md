Task: rename the Python function `fetch_rows` to `load_rows` everywhere in this repository.

Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-6m7hceza/rung3

Exact required changes (only these three lines):
1. rows.py line 1: `def fetch_rows(source):` -> `def load_rows(source):`
2. report.py line 1: `from rows import fetch_rows` -> `from rows import load_rows`
3. report.py line 5: `fetch_rows(source)` -> `load_rows(source)`

Constraints:
- Do NOT modify test_report.py or pyproject.toml.
- Do NOT rename anything else; leave the test function `test_report_joins_cells` alone.
- Change nothing else in the files.

When finished, run these commands and report their raw output:
- `git diff`
- `.venv/bin/python -m pytest -q`
- `grep -rn fetch_rows . --exclude-dir=.git --exclude-dir=.venv`

Report: files changed, exact diff, pytest output, and whether any `fetch_rows` reference remains.