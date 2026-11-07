Done — delegated to `mellum-worker` and independently verified.

**Root cause:** `totalCents` summed `item.priceCents` only; quantity was never applied.

**Fix** (`calculator.js`, 1 line):
```diff
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**My own verification** (not just the worker's report):
- `npm test` → 3 pass / 0 fail, including `multiplies unit prices by quantity` (425 cents).
- `git diff --stat` → only `calculator.js` changed (1 insertion, 1 deletion); `calculator.test.js` untouched.

Out of scope / not done: no commit. Left the change uncommitted in the working tree.