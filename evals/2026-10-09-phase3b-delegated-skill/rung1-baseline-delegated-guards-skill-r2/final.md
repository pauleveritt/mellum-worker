Fixed via `mellum-worker` (agent executable, run completed).

**Change** — `calculator.js:2`:
```diff
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Verified myself** (not just the child's report): `git diff` shows only that one line changed, and `npm test` → 3 pass / 0 fail, including `multiplies unit prices by quantity` (125×3 + 50×1 = 425).

No test or other files touched.