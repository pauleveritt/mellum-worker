Done — delegated to `mellum-worker` and verified independently.

**Fix** (`calculator.js`):
```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
}
```

Each item now contributes `priceCents * quantity`. Only `calculator.js` changed (1 line); `calculator.test.js` untouched.

**Verification (my own run, not just the child's):** `npm test` → 3 pass, 0 fail.
- ✔ multiplies unit prices by quantity
- ✔ empty basket costs zero
- ✔ zero quantity contributes zero

Run ID: mission `56040687-cb7b-41eb-9b0f-00a03e60ebd0`. Changes are unstaged; say the word if you want a commit.