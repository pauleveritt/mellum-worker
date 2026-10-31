Bug: `totalCents` in /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-nhnfpzjh/rung1/calculator.js ignores item quantity. It currently returns the sum of priceCents only.

Current implementation:
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents, 0);
}

Expected behavior (from calculator.test.js):
- totalCents([{priceCents:125,quantity:3},{priceCents:50,quantity:1}]) === 425
- totalCents([]) === 0
- totalCents([{priceCents:299,quantity:0}]) === 0

Task:
1. Edit calculator.js so each item contributes priceCents * quantity.
2. Do NOT modify calculator.test.js.
3. Run `npm test` in that directory and confirm all 3 tests pass.
4. Report: the exact final contents of calculator.js and the raw test output (pass/fail counts). If any test fails, say so explicitly rather than claiming success.