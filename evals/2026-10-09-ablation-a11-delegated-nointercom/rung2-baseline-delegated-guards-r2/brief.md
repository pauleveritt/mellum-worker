Bounded coding task in cwd /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ic_yc71c/rung2 (repo root; files ledger.py, test_ledger.py; run pytest via `uv run pytest`).

Goal: add a `balance()` function that sums the entries, with a test.

Exact scope — only these two files:
1. ledger.py: add a module-level function `def balance(entries):` that returns the sum of `entry.amount` for every `Entry` in `entries`. Summing an empty list must return 0. Keep existing code (`Entry`, `entries_from_lines`) unchanged. Follow the existing simple style; no type annotations required.
2. test_ledger.py: add a test named `test_balance` that imports `balance` alongside the existing imports and asserts a known sum, e.g. `balance([Entry("coffee", -3), Entry("pay", 10)]) == 7`. Also assert `balance([]) == 0`.

Do not touch any other file. Do not refactor existing code or tests.

Run `uv run pytest` from the repo root and include the full command output in your report. Finish only when pytest exits 0. Report: files changed, the exact pytest command and its output, and any deviation from these instructions.