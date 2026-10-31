The cart total now correctly multiplies prices by quantity. ✅

Changes made:
- Updated `calculator.js` to use `item.priceCents * item.quantity` in the reduction logic.

Tests pass:
```
TAP version 13
ok 1 - multiplies unit prices by quantity
ok 2 - empty basket costs zero
ok 3 - zero quantity contributes zero
```