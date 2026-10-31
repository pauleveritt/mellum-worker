Fix a bug in the file calculator.js in the current working directory.

Bug: totalCents() sums item.priceCents and ignores item.quantity, so the running total is wrong for any item with quantity != 1.

Evidence of the bug: run `npm test` (i.e. `node --test calculator.test.js`). The test "multiplies unit prices by quantity" fails: totalCents([{priceCents:125,quantity:3},{priceCents:50,quantity:1}]) returns 175 instead of 425.

Required change (bounded, minimal):
- Edit calculator.js only. Change the reducer so each item contributes priceCents * quantity.
- Do not change calculator.test.js and do not add files.
- Keep the existing export name totalCents and the module style (ESM).

Verification you must run and report: `npm test` in the current working directory, with the exact command and its full output. All three tests must pass. Report the final contents of calculator.js and the verified test output. Do not claim success without that output.