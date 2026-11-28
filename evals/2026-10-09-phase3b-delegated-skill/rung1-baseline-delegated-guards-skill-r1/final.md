Done. `mellum-worker` fixed it, and I verified the result directly.

**Change** (`calculator.js`):
```diff
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Verification** (`node --test`, run by me):
```
✔ multiplies unit prices by quantity
✔ empty basket costs zero
✔ zero quantity contributes zero
tests 3 / pass 3 / fail 0
```
`calculator.test.js` was untouched.

One note: the run was marked `Mission: failed` with `Acceptance rejected: Structured acceptance report not found.` — that's the harness's structured-acceptance check not recognizing the worker's report, **not** a failure of the task. The diff and tests confirm the fix is real and passing.