In this repository, fix the bug that the cart total ignores item quantity.

File: calculator.js
Function: totalCents(items)
Current behavior: it sums `item.priceCents` for each item, ignoring `item.quantity`. So quantity 3 at 125 cents yields 125 instead of 375.
Required behavior: each item must contribute `item.priceCents * item.quantity`.

Make the minimal change to totalCents so each line item's contribution is unit price times quantity. Do not change the test file or package.json. Keep the export and function signature unchanged.

Verify with the repository test command:
npm test
which runs `node --test calculator.test.js`.

The task is complete only when `npm test` exits 0. If it fails, read the failure, adjust calculator.js, and run it again.