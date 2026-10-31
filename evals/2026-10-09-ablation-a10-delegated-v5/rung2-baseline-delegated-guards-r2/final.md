Done — delegated to `mellum-worker`, then verified the result myself.

**Changes:**
- `ledger.py` — added `balance(entries)`, summing `entry.amount`
- `test_ledger.py` — added `test_balance` (`Entry("coffee", -3)`, `Entry("pay", 10)` → `7`)

**Verification:** `uv run --offline pytest -q` → `2 passed`. I also restored the trailing newline the worker dropped in both files.