Fixed and independently verified.

**Change** (`calculator.js`):
```diff
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

Each line now contributes `priceCents * quantity` before summing, so the cart total respects quantity.

**Verification** (run by me in the parent session, not just reported by the worker): `node --test calculator.test.js` → 3 pass, 0 fail, exit 0.

- `125*3 + 50*1 = 425` ✔
- empty basket → 0 ✔
- zero quantity → 0 ✔

Only the one-line logic change was made (no test or config edits).