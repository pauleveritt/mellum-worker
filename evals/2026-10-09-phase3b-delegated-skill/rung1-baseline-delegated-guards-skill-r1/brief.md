Fix a bug in /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-atlpmm7y/rung1/calculator.js.

Bug: totalCents(items) sums item.priceCents and ignores item.quantity, so the cart total is wrong for quantities > 1.

Requirements:
- Each item contributes priceCents * quantity.
- Preserve behavior for empty baskets and zero quantity.
- Do not modify calculator.test.js.
- The existing tests are the spec. Run `node --test` in the working directory and confirm all tests pass.

Report the exact diff and the test output.