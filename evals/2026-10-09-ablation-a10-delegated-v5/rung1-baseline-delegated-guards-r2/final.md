Delegated fix is in place and independently verified.

**Root cause** (`calculator.js`): the reducer summed `item.priceCents` and never used `item.quantity`, so the cart total was a count-of-lines sum instead of a quantity-weighted sum.

**Change** (only file touched: `calculator.js`):
```js
export function totalCents(items) {
  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
}
```

**Independent verification** (run by me, not the child):
```
$ npm test
✔ multiplies unit prices by quantity
✔ empty basket costs zero
✔ zero quantity contributes zero
ℹ tests 3   ℹ pass 3   ℹ fail 0        exit=0
```
`git diff --stat` confirms a 1-line change to `calculator.js`; no test or config files modified.

**One caveat, for honesty:** the subagent run itself came back with `Acceptance rejected: Structured acceptance report not found` and `Mission: ... (failed)`, even though the child's payload contained a valid acceptance report and the actual work is correct. That's a harness-level acceptance/bookkeeping failure in the run, not a code failure — I re-verified the file and tests directly. The work is done; the run record is mislabeled as failed.

Want me to commit this change?