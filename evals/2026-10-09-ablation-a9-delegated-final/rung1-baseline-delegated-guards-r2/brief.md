Bug fix in the current working directory (/private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-2jcgrybq/rung1).

Bug: `totalCents(items)` in calculator.js ignores each item's quantity, so the cart total is wrong. It currently does:
`items.reduce((sum, item) => sum + item.priceCents, 0)`

Required fix: multiply priceCents by quantity (treat a missing/undefined quantity as 1 only if needed for the existing tests; the tests all supply quantity). Keep the named export `totalCents` and the same signature.

Constraints:
- Only edit calculator.js. Do not modify calculator.test.js.
- Do not add dependencies or change package.json.

Verification (run this and include the exact output in your report):
`npm test`

Report back: the final contents of calculator.js, the exact `npm test` output, and confirmation that all 3 tests pass. If a test fails, report the failure rather than claiming success.