Fix the cart total in calculator.js.

Bug: `totalCents(items)` is defined as:

    export function totalCents(items) {
      return items.reduce((sum, item) => sum + item.priceCents, 0);
    }

It adds each line's `priceCents` once and ignores the line's `quantity`, so a line like `{priceCents: 125, quantity: 3}` contributes 125 instead of 375.

Required behavior: each line contributes `priceCents * quantity`, summed across all lines. Keep the existing export name and file. Note `quantity` may be 0, and an empty array must total 0.

Verify with this exact command from the repository root:

    node --test calculator.test.js

The task is complete only when that command exits 0. If it fails, read the failure, change the code, and run it again. Report the final diff and the test command output.