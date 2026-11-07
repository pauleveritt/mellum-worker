Rename the identifier `fetch_rows` to `load_rows` everywhere in this repository (working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-wd57o_cq/rung3).

Steps:
1. Find every occurrence: `grep -rn "fetch_rows" .` (exclude .git, .venv, node_modules, and any vendored/cache dirs).
2. For each occurrence — source files, tests, docs, configs — apply the rename to `load_rows`. Update definitions, call sites, imports, re-exports, string references, and docs. Do not rename unrelated identifiers that merely contain the substring (only exact `fetch_rows` token).
3. Re-run the grep to confirm zero occurrences of `fetch_rows` remain (report the exact command and its output; empty output is the success signal).
4. Run the project's test suite (e.g. `pytest -q`) and report the exact command and result. Also run `ruff check .` if ruff is configured.
5. Do not use `rtk` or `il` commands; run `pytest`, `ruff`, `git`, `grep` directly.

Report back: files changed (path + line counts), the verification grep command with its output, the test/lint commands with their results, and any occurrence you intentionally left alone with the reason.