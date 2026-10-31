Done. `mellum-worker` made the fix and I verified it independently.

**Root cause (systematic-debugging Phase 1):** `totalCents` accumulated only `item.priceCents`; `quantity` was never read. Reproduced: expected `425`, actual `175`; the qty-0 item contributed `299` instead of `0`.

**Fix** — `calculator.js`, one line, minimal:
```js
return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Verification (parent-run, not the child's claim):** `npm test` → 3/3 pass, exit 0:
- ✔ multiplies unit prices by quantity
- ✔ empty basket costs zero
- ✔ zero quantity contributes zero

No test or `package.json` changes.