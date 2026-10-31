The cart total now correctly multiplies prices by quantity. The fix was applied to `calculator.js`:

```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
}
```

All tests pass.