Done. `mellum-worker` fixed the bug and I verified it independently.

- **Bug:** `totalCents` summed `item.priceCents` and ignored `item.quantity`.
- **Fix** (`calculator.js`, 1 line): `sum + item.priceCents * item.quantity`.
- **Scope:** `git diff --stat` shows only `calculator.js` changed (1 insertion, 1 deletion); tests and `package.json` untouched.
- **Verification:** I reran `npm test` myself — 3/3 passing, including `multiplies unit prices by quantity` (125×3 + 50×1 = 425).

The change is unstaged and uncommitted.