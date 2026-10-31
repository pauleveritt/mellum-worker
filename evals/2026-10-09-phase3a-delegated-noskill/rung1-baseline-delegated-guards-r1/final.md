Fixed via `mellum-worker` and independently verified.

**Root cause:** `calculator.js` summed `item.priceCents` without multiplying by `item.quantity`.

**Fix:**
```js
return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
```

**Verification (my own run of `npm test`):** 3 pass, 0 fail — quantity multiplication, empty basket, and zero quantity all pass. Tests were not modified.