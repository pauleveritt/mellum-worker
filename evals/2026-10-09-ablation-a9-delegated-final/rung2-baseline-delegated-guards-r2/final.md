Done — verified independently.

**Delegated to:** `mellum-worker` (project agent, run `2820f97e`, 30.1s, completed)

**Changes** (both in `/private/var/folders/.../rung2`):

`ledger.py`
```python
def balance(entries):
    return sum(e.amount for e in entries)
```

`test_ledger.py` — added `balance` to the import and:
```python
def test_balance():
    assert balance([]) == 0
    assert balance([Entry("a", 1), Entry("b", -2), Entry("c", 3)]) == 2
```

**Verification I ran myself:** `.venv/bin/python -m pytest -q` → `2 passed in 0.00s`, and the `git diff` matches what the worker reported.

Minor cleanup the worker didn't do (I left it alone to stay within the brief): PEP 8 wants two blank lines before `balance`, but the diff only has one. Say the word if you want it tidied or committed.