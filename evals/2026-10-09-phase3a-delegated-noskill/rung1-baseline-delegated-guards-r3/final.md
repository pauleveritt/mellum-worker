Fixed and independently verified.

**Root cause** (`calculator.js`): `totalCents` reduced over `item.priceCents` only, so each line's unit price was counted once regardless of `quantity`.

**Fix** (one line, by `mellum-worker`):
```js
return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Verification I ran directly** (`node --test calculator.test.js`):
```
✔ multiplies unit prices by quantity
✔ empty basket costs zero
✔ zero quantity contributes zero
ℹ pass 3  ℹ fail 0
```

Two notes:
- The child run's status showed "failed" — that was only the harness rejecting an acceptance report schema mismatch (the `mellum-worker` agent declares `Acceptance: none`); the test **gate** ran and the file diff is minimal. I re-ran the tests myself above because the child's structured summary is not evidence on its own.
- Minor residual risk (out of scope): an item with `quantity: undefined` now yields `NaN`. Not covered by the tests; say the word and I'll have it default to 1 or 0.