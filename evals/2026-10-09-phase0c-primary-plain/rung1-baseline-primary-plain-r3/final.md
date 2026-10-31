The cart total now correctly accounts for quantity. The fix was applied to `calculator.js`, updating the reduce logic to multiply `priceCents` by `item.quantity`. All tests pass:

```
✔ multiplies unit prices by quantity
✔ empty basket costs zero
✔ zero quantity contributes zero
```

Let me know if you need further adjustments!