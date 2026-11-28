Done. `mellum-worker` fixed the bug and I independently verified it.

**Change** (`calculator.js`, the only file touched):
```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * (item.quantity ?? 1), 0);
}
```
It now multiplies each item's unit price by its quantity; `?? 1` keeps items without an explicit quantity sane.

**Independent verification** — I re-read the file from disk and reran `npm test` myself:
```
✔ multiplies unit prices by quantity
✔ empty basket costs zero
✔ zero quantity contributes zero
pass 3, fail 0   (exit 0)
```
`git diff --stat` confirms only `calculator.js` changed (+1/-1) — `calculator.test.js` and `package.json` are untouched.