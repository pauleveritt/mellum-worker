Fix a bug in the file calculator.js in the current working directory (a small ESM Node project).

Bug: totalCents(items) ignores item.quantity and sums only item.priceCents. It must sum priceCents * quantity for each item.

Current calculator.js:
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents, 0);
}

Required:
- Edit ONLY calculator.js. Do not touch calculator.test.js or package.json.
- Keep the export name totalCents and the single-array argument signature.
- Multiply each item's priceCents by its quantity before summing.
- Run `npm test` in the current directory and confirm all tests pass.

Report: the exact final content of calculator.js, the exact command you ran, and its raw output.