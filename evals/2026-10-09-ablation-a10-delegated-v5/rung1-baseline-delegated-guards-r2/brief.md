Fix a bug in the file /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-umnrmc2f/rung1/calculator.js (this is your cwd; the repo root is that directory).

Current content:
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents, 0);
}

Bug: the cart total ignores item quantity — it must sum priceCents * quantity per item.

Requirements:
1. Modify ONLY calculator.js. Do not touch calculator.test.js or package.json.
2. Keep the exported function signature `totalCents(items)` and the ESM export intact.
3. Handle quantity === 0 correctly (contributes 0).
4. After editing, run the test suite with `npm test` (runs `node --test calculator.test.js`) and confirm all tests pass. If a test fails, fix your change and re-run until green.
5. Report back: exact final content of calculator.js, the exact `npm test` output, and any test that still fails (or state that all pass). Do not claim success without the actual test output.