Fixed and independently verified.

**Change** (`calculator.js`):
```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
}
```
Each line item now contributes `priceCents * quantity`, so `[{125,×3},{50,×1}]` → `425`.

**Verification** (run by me, not the child): `node --test calculator.test.js` → 3 pass / 0 fail, exit 0. `calculator.test.js` was not modified.

Done via `mellum-worker` (single bounded child, synchronous), with parent-side test verification per its acceptance contract.