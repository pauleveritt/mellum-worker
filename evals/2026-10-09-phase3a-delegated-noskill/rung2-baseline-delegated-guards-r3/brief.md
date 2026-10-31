Working directory: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ritrcpek/rung2

Existing file ledger.py contains:

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

Existing file test_ledger.py contains one test, test_parses_lines.

TASK (bounded, do exactly this and nothing more):
1. In ledger.py, add a function:

       def balance(entries):
           ...

   It must take an iterable of Entry and return the sum of all entry.amount values. For an empty iterable it must return 0. Keep the existing code unchanged and match the existing style (plain functions, no type hints required).
2. In test_ledger.py, add exactly one new test named test_balance that builds entries (include at least one negative and one positive amount) and asserts balance() returns the correct total. Keep the existing test unchanged.

CONSTRAINTS:
- Only modify ledger.py and test_ledger.py. Do not create other files, do not touch .venv, pyproject.toml, uv.lock, or git state.
- Do not refactor or rename existing functions.

VERIFY before finishing:
Run exactly: .venv/bin/pytest -q
from the working directory above. Both tests must pass.

REPORT back, concisely:
- STATUS: done or blocked
- Files changed with the exact diff of your changes
- The exact command you ran and its full output (pass/fail counts)
- Any deviation from the task