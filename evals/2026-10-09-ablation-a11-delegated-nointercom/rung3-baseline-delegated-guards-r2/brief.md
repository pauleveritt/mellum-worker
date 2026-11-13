In the current working directory, rename the function `fetch_rows` to `load_rows` everywhere in the project source.

Steps:
1. Find every occurrence of `fetch_rows` in all files (Python sources, tests, docs, configs).
2. Replace each occurrence with `load_rows`. This includes the definition in rows.py, the import and call sites in report.py, and any test references in test_report.py.
3. Do not change any other behavior, formatting, or identifier.
4. Verify with: grep -rn "fetch_rows" . (expect no matches) and grep -rn "load_rows" .
5. Run the test suite with `uv run pytest -q` and report the exact output.

Report: files changed, the verification grep output, and the pytest output. If anything fails, report the exact error rather than guessing.