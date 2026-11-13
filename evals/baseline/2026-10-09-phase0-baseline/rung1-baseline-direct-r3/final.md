Files changed:
- calculator.js: Updated the `totalCents` function to multiply `priceCents` by `quantity` when calculating the total.

Test output:
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.279209ms)
✔ empty basket costs zero (0.039792ms)
✔ zero quantity contributes zero (0.033666ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 55.059125
```

Everything is fixed.