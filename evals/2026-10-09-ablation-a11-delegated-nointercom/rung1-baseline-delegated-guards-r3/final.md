Done and independently verified.

**Root cause:** `totalCents` summed `item.priceCents` per line item, ignoring `item.quantity`.

**Fix** (`calculator.js`, the only file changed):
```js
return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Verification (run by me, not the child):**
- `node --test calculator.test.js` → 3 pass / 0 fail, exit 0
- `git diff` confirms `calculator.test.js` is untouched and no other files changed

`mellum-worker` did the edit; I ran the test suite and inspected the diff as required by its `acceptance: none` contract.