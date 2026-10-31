Fix a bug in this repository.

File: calculator.js
Function: totalCents(items)

Bug: it sums item.priceCents and ignores item.quantity, so the cart total is wrong whenever quantity is not 1.

Required behavior: each item contributes its unit price multiplied by its quantity. An empty list totals 0.

Do not change calculator.test.js. The tests are the specification.

Test command (run it in this directory, it must exit 0):
node --test calculator.test.js

When the tests pass, reply with: the file(s) changed and the final test command output.