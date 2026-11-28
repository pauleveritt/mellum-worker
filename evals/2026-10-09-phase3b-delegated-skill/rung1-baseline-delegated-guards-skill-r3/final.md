Fixed and independently verified.

**Root cause:** `totalCents` summed `item.priceCents` only, ignoring `item.quantity`, so every line counted as exactly one unit.

**Change** (`calculator.js`, 1 line — only file modified; tests untouched):
```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
}
```

**Verification** (`npm test` → `node --test calculator.test.js`): 3/3 pass — quantity multiplication (3×125 + 1×50 = 425), empty basket → 0, zero quantity → 0. Baseline before the fix failed the quantity and zero-quantity cases.

Delegated to `mellum-worker` as requested; the child's report matched the committed state on independent re-run.