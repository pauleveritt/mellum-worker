Using verification-before-completion to verify the fix:

**Verification command:** `npm test`

**Full output:**
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.31975ms)
✔ empty basket costs zero (0.044875ms)
✔ zero quantity contributes zero (0.037791ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 57.131167
```

**Evidence:** All 3 tests pass with 0 failures, exit code 0.

**Claim:** The `totalCents` function now correctly multiplies item prices by quantity, fixing the cart total that was ignoring quantity. The fix was implemented in `calculator.js` by changing `sum + item.priceCents` to `sum + item.priceCents * item.quantity`.

The issue is resolved.