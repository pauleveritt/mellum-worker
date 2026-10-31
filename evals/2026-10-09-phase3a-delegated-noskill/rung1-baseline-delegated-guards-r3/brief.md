Bounded bug fix in this repo (cwd is the repo root).

FILE: calculator.js

CURRENT CODE:
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents, 0);
}

BUG: the cart total ignores `quantity`; it adds each line's unit price once.

REQUIRED FIX: totalCents must sum priceCents * quantity for every item, so
[{priceCents:125,quantity:3},{priceCents:50,quantity:1}] returns 425, an empty
array returns 0, and zero quantity contributes 0. Keep the exported function
name/signature and the reduce-based style; do not change any other file.

VERIFY: run `node --test calculator.test.js` (or `npm test`) and confirm all
three tests pass. If any test fails, fix your change and re-run until green.

REPORT BACK: the final content of calculator.js (or the exact diff), the exact
test command you ran, and its full pass/fail output. Do not claim success
without pasted test output. Do not use rtk/il commands.