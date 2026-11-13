Done — and independently verified.

**Worker:** `mellum-worker` (local Mellum, executable, foreground)
**Change:** `calculator.js` only — the reducer now uses quantity:

```diff
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**My verification** (not the child's claim):
- `git diff` → one line changed in `calculator.js`; tests/`package.json` untouched
- `npm test` → 3 pass, 0 fail, `EXIT=0`

Note: the child's diff block showed leading spaces (`- export ...`); the actual file diff is the clean two-line change above. The untracked `.pi/` dir (guard config) predates this run.