Objective: make the cart total respect item quantity.

Repo/cwd: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-320_5a0y/rung1 (work there).

Bug: totalCents(items) in calculator.js sums each item's priceCents and ignores its quantity, so the total is wrong whenever quantity > 1.

Required behavior: the total (in cents) must be the sum of priceCents * quantity for every item.

Authority: edit ONLY calculator.js. Do NOT modify calculator.test.js.

Test command (run in the cwd above): node --test calculator.test.js
The task is complete only when that command exits 0.

If calculator.js or calculator.test.js cannot be found, reply with what is missing and stop. Otherwise, when the tests pass, reply with the files changed and the exact test output.