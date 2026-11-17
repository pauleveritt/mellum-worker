Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-zpla5i0j/rung2 (a git repo; only you are editing it).

Repo contents:
- ledger.py:
    from dataclasses import dataclass


    @dataclass(frozen=True)
    class Entry:
        memo: str
        amount: int


    def entries_from_lines(lines):
        out = []
        for line in lines:
            memo, amount = line.rsplit(",", 1)
            out.append(Entry(memo.strip(), int(amount)))
        return out
- test_ledger.py:
    from ledger import Entry, entries_from_lines


    def test_parses_lines():
        assert entries_from_lines(["coffee, -3", "pay, 10"]) == [
            Entry("coffee", -3),
            Entry("pay", 10),
        ]
- pytest is configured via pyproject.toml (testpaths = ["."]), environment managed by uv (`.venv` exists); Python 3.14.

TASK (requirements):
1. In ledger.py add a top-level function `balance(entries)` that returns the sum of the `amount` of each entry. It must accept an iterable of Entry objects (e.g. the list returned by entries_from_lines) and must return `0` for an empty iterable. Keep it simple and typed-free in the existing style; do not modify Entry or entries_from_lines.
2. In test_ledger.py add a test `test_balance_sums_entries` that builds entries via `entries_from_lines(["coffee, -3", "pay, 10"])` and asserts `balance(...) == 7`; also assert `balance([]) == 0` in the same test or a second test named `test_balance_of_nothing_is_zero`. Update the import to include `balance`.
3. Run the test suite with `uv run pytest -q` (do not use rtk/il commands) and make sure all tests pass; if a failure occurs, fix your code and re-run until green.

Do not create new files beyond edits to these two, do not touch .git or commit, and do not change pyproject.toml.

FINAL REPORT: exact files changed, the final content of balance(), the command you ran, and the pytest summary line (pass/fail counts).