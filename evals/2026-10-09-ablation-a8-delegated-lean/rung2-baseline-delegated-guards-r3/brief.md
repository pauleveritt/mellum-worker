Objective: add a `balance(entries)` function to `ledger.py` that returns the sum of the `amount` fields of the given `Entry` objects (return 0 for an empty list), and add tests for it in `test_ledger.py`.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-e72aiilc/rung2 (git, baseline commit dad44b3).

Authority boundary: edit ONLY `ledger.py` and `test_ledger.py`. Do not touch pyproject.toml, uv.lock, or anything else.

Existing contract to respect:
- `Entry` is a frozen dataclass with `memo: str` and `amount: int`.
- `entries_from_lines(lines)` already exists; do not change it.
- Keep the simple functional style already in the file (no classes, no new dependencies).

Success/acceptance criteria:
- `from ledger import balance` works.
- `balance([]) == 0`.
- `balance(entries_from_lines(["coffee, -3", "pay, 10"])) == 7`.
- New tests in `test_ledger.py` cover both a multi-entry sum and the empty case, using the existing pytest style.
- Full test suite passes.

Validation: run `uv run pytest -q` from the repo root and capture the exact output.

Expected output: report (1) files changed, (2) the final diff (`git diff`), (3) the exact test command and its output, (4) any blocker.

Stop/ask: if the files don't match the description above or tests can't run, stop and report the blocker instead of guessing. Do not commit.