Bounded coding task in the current working directory (cwd is already the repo root). Work only in this repo; do not use git commit or push.

Bug report: "the cart total ignores quantity."

Files of interest:
- calculator.js exports `totalCents(items)`.
- calculator.test.js has an existing test: totalCents([{priceCents:125,quantity:3},{priceCents:50,quantity:1}]) === 425.

Required procedure:
1. Reproduce: run `npm test` and capture the exact failing assertion output.
2. Root cause: state in one sentence why the total is wrong (hint: check how `totalCents` combines `priceCents` and `quantity`).
3. Fix `calculator.js` so a line item contributes `priceCents * quantity`. Do NOT modify calculator.test.js and do not change the exported signature. Keep the change minimal — one edit, no unrelated refactors.
4. Verify: run `npm test` again and report the full output (all tests must pass, 0 failures).
5. Report back concisely: root cause, the exact diff (old line -> new line), and the final `npm test` output. If a command fails, report the raw error instead of guessing.