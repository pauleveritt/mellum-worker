Delegated to `mellum-worker` (single bounded child, no worktree needed — one writer). I then verified the result independently in the parent.

**Changes** (`rung2/`):

`ledger.py` — added:
```python
def balance(entries):
    total = 0
    for entry in entries:
        total += entry.amount
    return total
```

`test_ledger.py` — added `test_balance`, covering the sum (`-3 + 10 == 7`) and the empty case (`balance([]) == 0`).

**Evidence**
- Child's RED run: `ImportError: cannot import name 'balance'`, `1 failed, 1 passed` (test written before the implementation).
- Child's GREEN run: `2 passed`.
- My own verification in the parent: `2 passed in 0.00s`; `git status` shows only `ledger.py` and `test_ledger.py` modified (plus pre-existing untracked `.pi/`).

**Notes**
- Nothing committed.
- Minor style nit only: `test_balance` imports `balance` inside the function rather than at module level. Behavior and contract (`Entry`/`entries_from_lines` unchanged, empty iterable → `0`) are correct, so I left it.