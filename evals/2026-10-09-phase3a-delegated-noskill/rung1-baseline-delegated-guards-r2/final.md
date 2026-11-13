Done. Here's the honest picture.

## Result: fix is in place and verified

**Change** (`calculator.js`) — the only modified file:
```diff
 export function totalCents(items) {
-  return items.reduce((sum, item) => sum + item.priceCents, 0);
+  return items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);
 }
```

**Verification** (I ran this myself, per the agent's contract):
```
ℹ tests 3
ℹ pass 3
ℹ fail 0
```
Baseline before the fix was 2 failing tests (`175 !== 425`); now `multiplies unit prices by quantity`, `empty basket costs zero`, and `zero quantity contributes zero` all pass. `git status` shows only `M calculator.js` (plus the pre-existing untracked `.pi/`), so no stray files and the test file is untouched.

## Caveat on the delegated run

The `mellum-worker` run was flagged **failed** (`exitCode: 1`, "produced no output"), but that reflects a missing final text reply, not a missing fix. Evidence from the artifact directory:

- Run `0aa94441`, window 20:38:35–20:38:45, issued the `edit` call with exactly the diff above.
- `calculator.js` mtime is 20:38:43, inside that window.
- The child is configured to nudge once on an empty final turn (`emptyFinalNudge: 1`); it did its work, then still ended without a closing message, so the harness called the run failed.

This matches the pathology documented in `.pi/extensions/mellum-guards.ts` ("5 of 45 v3 runs, every failure"). I did **not** retry, because the artifact is verifiably correct and the parent verification (tests) passes — a same-protocol retry would only be to obtain a clean final message, at the risk of a different edit. Say the word if you want a clean re-run for the record.