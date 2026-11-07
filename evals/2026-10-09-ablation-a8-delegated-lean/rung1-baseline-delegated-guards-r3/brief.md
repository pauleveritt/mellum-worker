Fix a bug in /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ksxu7p9p/rung1/calculator.js.

Bug: `totalCents(items)` ignores each item's quantity. It currently sums `item.priceCents` only, so a line item with quantity 3 is charged for 1.

Required change: make the total account for quantity, i.e. sum `priceCents * quantity` per item. Keep the function name, signature, and CommonJS/ESM style unchanged (the file uses ESM `export function`).

Do not modify /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-ksxu7p9p/rung1/calculator.test.js — it is the spec. Expected behavior from the tests:
- totalCents([{priceCents:125,quantity:3},{priceCents:50,quantity:1}]) === 425
- totalCents([]) === 0
- totalCents([{priceCents:299,quantity:0}]) === 0

Run `npm test` in that directory and confirm all tests pass. Report the exact command and output.