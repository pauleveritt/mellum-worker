Fixed calculator.js to multiply priceCents by quantity in totalCents function.

Test output:
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.273833ms)
✔ empty basket costs zero (0.038291ms)
✔ zero quantity contributes zero (0.0325ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 51.1845
```

All tests pass.