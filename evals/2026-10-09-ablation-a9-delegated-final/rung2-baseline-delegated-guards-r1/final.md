Done. `mellum-worker` added the function and test; I verified and fixed two lint issues (import order, blank lines).

**`ledger.py`**
```python
def balance(entries):
    return sum(entry.amount for entry in entries)
```

**`test_ledger.py`**
```python
def test_balance_sums_entries():
    entries = entries_from_lines(["coffee, -3", "pay", 10])  # actual: ["coffee, -3", "pay, 10"]
    assert balance(entries) == 7
    assert balance([]) == 0
```

Verification (ran in repo):
- `ruff check .` → All checks passed!
- `.venv/bin/pytest -q` → `2 passed in 0.00s`

One note: the subagent's final report showed a garbled test diff, so I inspected the real files and re-ran the tests rather than trusting the summary.