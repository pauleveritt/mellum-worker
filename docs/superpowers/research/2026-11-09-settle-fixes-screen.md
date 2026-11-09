# Settle fixes on Easy, and Vanilla against Base on Medium

## For Andre

- **Two screens from the last hours of the held pod.** Base with the leak and cleanup fixes on Easy,
  with and without a send-back limit of 2; and Vanilla against the frozen Base on Medium.
- **The fixes close the leak's main route** and did not hurt the pass rate. They do not show a
  saving: the unfixed Base's own n = 6 screen cost the same.
- **The cleanup is unproven.** It never reported stopping anything in 12 sessions.
- **Limit 2 is the only lower number**, at n = 6, with one fewer strict pass.
- **What to look at:** Medium, where Base cost 3.3 times Vanilla and finished nothing.

**What is measured.** The tables below, n = 6 per Easy arm, n = 3 per Medium arm. Screens, so leads.

**What is conjecture.** That the median saving at limit 2 is real, and why port-held send-backs
disappeared. No run here separates either.

| Easy, n = 6 (Base), code | Strict | All 13 | Median requests | Median output tokens | Times Vanilla's 7,598.5 |
|---|---|---|---|---|---|
| Unfixed, [go-or-no-go](../../../evals/2026-11-08-easy-final-screen/table.md) | 5 | 6 | 35.5 | 15,578 | 2.05 |
| [Fixed](../../../evals/2026-11-09-easy-fixed-screen/table.md) | 5 | 6 | 38 | 15,878 | 2.09 |
| [Fixed, limit 2](../../../evals/2026-11-09-easy-fixed-max2-screen/table.md) | 4 | 5 | 28 | 13,803 | 1.82 |
| Unfixed, the count, n = 32 | 25 | 30 | 51.5 | 33,993.5 | 4.47 |

Output tokens are the budget proxy's charge, as in the count. The fixed arms are compared with the
unfixed n = 6 screen, not with the count: the same code gave 15,578 at n = 6 and 33,993.5 at n = 32,
so a six-session median says little about a 32-session one.

| [Medium](../../../evals/2026-11-09-medium-final-screen/table.md), n = 3, the frozen code | Vanilla | Base |
|---|---|---|
| Strict passes | 0 | 0 |
| Mean checks of 18 | 8.33 | 13.67 |
| Median requests | 123 | 331 |
| Median output tokens | 77,518 | 253,976 |
| Ended on the budget | 1 | 1 |

All three Base sessions on Medium missed the same four checks (complaint identity, the resolve and
reopen routes, board order). One Vanilla session's checks never ran: it left a syntax error.

What the Easy traces show about the fixes:

- No send-back named the copy's path (0 of 12 sessions; the unfixed screen's traces named it 231 times).
- No session reached the test's source, and none ran a command naming `/tmp` or the test. 187 stale
  copies from earlier runs were removed from the pod early in the screen.
- No send-back was for a held port (0, against 12 of 44 in the count). The "were stopped" line never
  appeared, and the traces show most backgrounded servers had already died or been killed by the
  model before settling. So the zero is not evidence for the cleanup.

## Ladder run

Pod A40 under its host card, one session at a time, as `mellum-session`, graded as `mellum-grade`.
Easy at `checkpoint-2026-11-09-settle-fixes`, arms in
[`easy-fixes-arms.json`](../../../scripts/pod/easy-fixes-arms.json), the limit-2 arm with
`MELLUM_MEDIATED_MAX=2` (recorded in each `run.json`), sessions interleaved. Medium at
`checkpoint-2026-11-08-easy-final`, budget 400 requests and 300,000 output tokens. The pod was
terminated after the results were copied.

## Persuasion → enforcement

Deleting the copy and removing its path are enforcement: the model is not told, and no file exists
while it can act. "This test is not in the project" is persuasion, added beside them. The limit
is enforcement. A hint in a prompt fragment would not have closed the route.

## What would falsify this / Risks

- The cleanup's `ps` detection is unit-tested on macOS only. It was not exercised on Linux, and a
  probe of it on the pod was invalid (the matching lines were the probe's own command).
- The harness's own hand-over copy stays readable, and its path is in `MELLUM_MEDIATED_TEST`, which
  the model's commands inherit. No session used it; this route is still open.
- n = 6 cannot separate limit 2's lower median from noise, and one strict pass is within noise too.
- Three sessions on one suite say little about Medium, beyond the same four checks recurring.

**Dated correction, 2026-11-09:** the same four Medium misses do not establish
four missing features. On retained Base r02/r03, three route/order checks fail
before their POST because the grader rejects valid `Status: Open` labels;
allowing that prefix in memory makes all six executions pass. The cross-path
ID invariant still fails and escapes mediated acceptance. Original scores stay
unchanged; F.7 owes versioned qualification. The
[combined review](2026-11-09-phase-worker-review.md) supersedes the interpretation
"finished nothing" while retaining zero observed strict passes.
