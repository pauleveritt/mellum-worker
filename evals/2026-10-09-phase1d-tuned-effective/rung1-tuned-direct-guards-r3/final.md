Fixed the cart total calculation to include quantity.

**Files changed:**
- calculator.js: Updated `totalCents` to multiply `priceCents` by `quantity`.

**Test output:**
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.319667ms)
✔ empty basket costs zero (0.043542ms)
✔ zero quantity contributes zero (0.037ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 58.614542
```

All tests pass, so the issue is resolved.