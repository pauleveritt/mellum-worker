Using systematic-debugging to fix cart total ignoring quantity

**Phase 1: Root Cause Investigation**
- Read error: totalCents ignored quantity field
- Reproduced via test failures before fix
- Checked recent changes: none relevant
- Gathered evidence: calculator.js line `sum + item.priceCents` missing `* item.quantity`

**Phase 2: Pattern Analysis**
- Found working pattern: price calculation should include quantity
- Compared against test cases showing expected multiplication

**Phase 3: Hypothesis and Testing**
- Hypothesis: Missing `* item.quantity` causes ignoring quantity
- Test minimally: changed one line, ran tests
- Verified: tests now pass with 3/3 passing

**Phase 4: Implementation**
- Created failing test case initially (already existed)
- Implemented single fix: `item.priceCents * item.quantity`
- Verified with fresh test run: `npm test` shows 3 passing tests, 0 failures

**Verification Before Completion Evidence:**
```
> test
> node --test calculator.test.js

✔ multiplies unit prices by quantity (0.321583ms)
✔ empty basket costs zero (0.045083ms)
✔ zero quantity contributes zero (0.037583ms)
ℹ tests 3
ℹ suites 0
ℹ pass 3
ℹ fail 0
```

Fix complete: cart total now correctly includes quantity.