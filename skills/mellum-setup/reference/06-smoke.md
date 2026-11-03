# Phase 7: Smoke test

A disposable copy of a three-test calculator whose total ignores quantity.

```bash
SMOKE="$(mktemp -d)/calculator"
cp -R "$PKG/skills/mellum-setup/smoke/calculator" "$SMOKE"
cd "$SMOKE" && node --test calculator.test.js; echo "exit $?"   # expect 1 (failing)
```

Then run the worker on it, from inside `$SMOKE`:

- Pi, Worker: start `pi` in `$SMOKE` and say
  "Use mellum-worker to do this: the cart total ignores quantity, fix it.
  Test command: node --test calculator.test.js"
- Pi, Mode: start `pi` in `$SMOKE` and type
  `/mellum the cart total ignores quantity, fix it. Test command: node --test calculator.test.js`

Check: `cd "$SMOKE" && node --test calculator.test.js` exits 0 and
`calculator.js` multiplies `priceCents` by `quantity`. Typical time on an
M-series Mac is under a minute.

Last, once the fixture passes, check the server and provider against the
measured profile (it only reads):

```bash
node "$PKG"/scripts/mellum.mjs check --host pi
```

Show its output. In Pi Mode, `/mellum check` does the same. Any `FAIL` line is a
setup problem to fix before reporting success; a `WARN` or `INFO` line is shown
as is.

If it fails: confirm phase 3's server answers, that the host picked
`omlx/Mellum2.1-12B-A2.5B-Thinking-6bit` (Pi shows it in the status line), and
that the brief named the test command. Report what you saw; do not loosen any
setting to make it pass.
