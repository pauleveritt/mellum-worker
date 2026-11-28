In the repository at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-_w1ubvc0/rung3, rename the function `fetch_rows` to `load_rows` everywhere it appears — its definition and every call site and import/reference, across all source and test files (e.g. rows.py, report.py, test_report.py).

Steps:
1. Use grep/find to locate every occurrence of `fetch_rows` (including inside strings, comments, and docs).
2. Apply the rename with edit.
3. Re-grep to confirm zero occurrences of `fetch_rows` remain and that `load_rows` appears in all the expected places.
4. Run the test suite (`.venv/bin/pytest -q` or `uv run pytest -q`) and report the result.

Constraints: rename only; make no other behavioral changes. Do not rename unrelated identifiers.

Report back: the exact files/line numbers changed, grep proof that no `fetch_rows` remains, and the pytest output.