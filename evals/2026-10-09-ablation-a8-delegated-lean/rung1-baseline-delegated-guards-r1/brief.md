Repository: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-f3l6j8hu/rung1

Bug: the cart total ignores quantity. `calculator.js` currently reads:

    export function totalCents(items) {
      return items.reduce((sum, item) => sum + item.priceCents, 0);
    }

Each item contributes only its unit price; `quantity` is ignored.

Required behavior: each item contributes `priceCents * quantity`, so
`totalCents([{priceCents:125,quantity:3},{priceCents:50,quantity:1}])` must equal `425`.

Fix `calculator.js` only. Do NOT modify `calculator.test.js`.

Test command (run from the repository root):
node --test calculator.test.js

The task is complete only when that command exits 0. Run it, read any failure, adjust the code, and run it again until it passes. Reply with the file changed and the test output.