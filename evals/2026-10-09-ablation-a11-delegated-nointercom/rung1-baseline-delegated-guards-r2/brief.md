Fix a cart-total bug in this repo (cwd is the repo root). Work only in this repo.

BUG: `totalCents` in calculator.js ignores quantity, so a cart total is wrong.
Evidence: calculator.test.js already contains a test `multiplies unit prices by quantity` that fails.

Do exactly this, in order:
1. Run `npm test` and capture the full output. Confirm the failing test. Do not edit the tests — they are correct.
2. Root cause: the reducer in `totalCents` adds `item.priceCents` and never uses `item.quantity`. Fix it at the source so the total is the sum of `priceCents * quantity`.
3. Re-run `npm test`. It must exit 0 with all three tests passing.
4. Reply with: (a) the file changed, (b) the exact diff of your change, (c) the final `npm test` output, (d) the exit status.

Constraints: make the minimal single-line-style change to calculator.js; do not modify calculator.test.js, package.json, or any other file; do not add dependencies. Run commands directly (e.g. `npm test`) — never use `rtk` or `il` prefixed commands.