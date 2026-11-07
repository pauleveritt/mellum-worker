Using systematic-debugging to fix the cart total ignoring quantity

**Phase 1: Root Cause Investigation**
- Read error messages: Tests failed because totalCents didn't use quantity
- Reproduced: `npm test` showed 2 failures initially
- Checked recent changes: Function totalCents was missing quantity multiplication
- Gathered evidence: Test cases revealed the bug directly

**Phase 2: Pattern Analysis**
- Found working pattern: Tests expected quantity multiplication
- Compared working vs broken code: Function only summed priceCents, ignored quantity

**Phase 3: Hypothesis and Testing**
- Hypothesis: totalCents function doesn't multiply by quantity, causing cart total to ignore quantity
- Test minimally: Ran tests after fix - all passed

**Phase 4: Implementation**
- Created failing test cases existed, so implemented fix directly
- Fixed calculator.js: Added `* item.quantity` to price calculation
- Verified before completion: Ran `npm test` again

**Verification Evidence:**
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.395167ms)
✔ empty basket costs zero (0.057583ms)
✔ zero quantity contributes zero (0.045708ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 60.803083
```

**Conclusion:** The cart total now correctly accounts for quantity. The fix is verified and complete.