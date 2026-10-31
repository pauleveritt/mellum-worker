Done. `mellum-worker` applied the one-line fix and I verified it independently.

**Fix** — `calculator.js`:
```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
}
```

**Verification** — `npm test` in the repo:
```
✔ multiplies unit prices by quantity
✔ empty basket costs zero
✔ zero quantity contributes zero
tests 3 | pass 3 | fail 0
```

All three tests pass, including the previously failing `425` case. Test spec (`calculator.test.js`) was left untouched.