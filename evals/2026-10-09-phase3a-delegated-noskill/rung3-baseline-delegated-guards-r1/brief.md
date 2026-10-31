In the repo at /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-l6_kobgq/rung3, rename the function `fetch_rows` to `load_rows` everywhere.

Scope:
- rows.py: rename the `def fetch_rows(source)` definition to `def load_rows(source)`.
- report.py: update the import and all call sites.
- test_report.py and any other file (including docs/comments/strings) that references `fetch_rows` must be updated too.
- Do not change any behavior, signatures, or formatting beyond the rename.

Steps:
1. Run `rg -n fetch_rows` to find every occurrence.
2. Make the edits.
3. Run `rg -n fetch_rows` again — it must return no matches.
4. Run the test suite (`uv run pytest -q`) and report the exact result.

Reply with: files changed, the final rg output (or "no matches"), and the pytest output summary.