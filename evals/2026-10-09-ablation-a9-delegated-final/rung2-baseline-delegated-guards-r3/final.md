Done via `mellum-worker`, and I independently verified the result.

**Changes** (rung2):
- `ledger.py`: added `balance(entries)` → `sum(entry.amount for entry in entries)`
- `test_ledger.py`: imports `balance`; `test_balance` covers a mixed sign case (`7`) and the empty case (`0`)

**Verification I ran myself:**
```
$ uv run --no-sync pytest -q
..  [100%]
2 passed in 0.00s
```

One minor note: the new `balance` definition isn't preceded by two blank lines (PEP 8 / ruff E302 if the project enforces it). Tests pass and the project has no ruff config enforced here; say the word if you want it tidied.