Files changed:
- calculator.js

Test output:
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.273084ms)
✔ empty basket costs zero (0.039583ms)
✔ zero quantity contributes zero (0.033167ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 50.190875
```

Anything not done:
The fix successfully addresses the issue where cart total ignored quantity. No further action required.