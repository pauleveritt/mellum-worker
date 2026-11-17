Bug: `totalCents` in calculator.js ignores item quantity. It currently returns `items.reduce((sum, item) => sum + item.priceCents, 0)`.

Fix calculator.js so the cart total multiplies each item's priceCents by its quantity (missing quantity should presumably default to 1 — but only if the existing tests require it; do not over-engineer).

Constraints:
- Only edit calculator.js. Do NOT edit calculator.test.js (the tests are the spec).
- Run `node --test` (or `node --test calculator.test.js`) from the repo root and paste the full output as evidence.
- Report: the exact change made, the test command, and the observed pass/fail output. Do not claim success without the command output.
