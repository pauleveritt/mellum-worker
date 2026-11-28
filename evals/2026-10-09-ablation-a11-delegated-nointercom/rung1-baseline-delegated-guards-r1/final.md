Fixed and independently verified.

**Change** (`calculator.js`):
```js
return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

Previously the reducer added `item.priceCents` only, ignoring quantity. Now each line contributes unit price × quantity.

**Verification** (run by me, not just the worker): `node --test calculator.test.js` → 3 pass / 0 fail, covering quantity multiplication, empty basket, and zero quantity. Diff is one line in `calculator.js`; the test file was left untouched.

One note for later: the worker's test output quoted above matches my rerun. Nothing to fix.