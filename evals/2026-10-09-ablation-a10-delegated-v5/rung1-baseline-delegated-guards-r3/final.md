Fixed and verified.

**Change** — `calculator.js`, one line:
```diff
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Delegation**: `mellum-worker` (local Mellum, bounded task) made the edit; uncommitted change is in the working tree.

**Independent verification** (run by me, not the child):
- `npm test` exits 0 — 3 pass / 0 fail.
- Before the fix the same suite failed: `175 !== 425` and `299 !== 0`.

The tests were the spec and were not modified. Note: `totalCents` now assumes every item has a numeric `quantity`; no test covers a missing quantity (`undefined` would yield `NaN`). Say the word if you want a default of `1` added for that case.