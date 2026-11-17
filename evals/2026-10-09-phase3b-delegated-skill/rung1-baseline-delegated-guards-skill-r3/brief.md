Repo: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-1zzhf3cn/rung1

Bug: `totalCents(items)` in `calculator.js` ignores each item's `quantity`, so the cart total is wrong (e.g. 3 x 125c returns 125 instead of 375).

Task:
1. Read `calculator.js` and `calculator.test.js` to confirm the expected contract.
2. Fix `totalCents` so each line contributes `priceCents * quantity`, summed. Keep it a minimal, idiomatic change; do not change the function signature or exports.
3. Do NOT edit `calculator.test.js` (tests are the acceptance oracle).
4. Run `npm test` in that directory and confirm all 3 tests pass.
5. Report exactly: the final content of `calculator.js`, the test command run, and the pass/fail summary. If normal quantities are assumed non-negative integers, say so; do not add speculative validation or extra features.