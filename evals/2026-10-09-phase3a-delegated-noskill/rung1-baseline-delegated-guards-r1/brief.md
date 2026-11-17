Fix the bug in calculator.js: `totalCents` ignores `quantity`, summing only `item.priceCents`.

Requirements:
- `totalCents(items)` must sum `item.priceCents * item.quantity` for each item.
- Handle `quantity` correctly: zero quantity contributes 0; empty array returns 0.
- Do NOT change calculator.test.js — the tests already encode the correct behavior.
- Run `node --test calculator.test.js` (or `npm test`) and confirm all 3 tests pass before finishing.

Report: the exact diff you made, the test command, and the full pass/fail output.