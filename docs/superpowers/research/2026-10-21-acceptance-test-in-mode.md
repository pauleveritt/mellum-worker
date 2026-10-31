# `--acceptance-test` in Mode cracks rung 9 (0/3 → 3/3); `mellum-ncm.ts` is a dormant safety net

Date: 2026-10-21.

## What is measured

6-bit Mellum in **Mellum Mode** (`mellum-mode.ts`, with `mellum-guards.ts` and
`mellum-facts.ts` as it always runs them) on rung 9, n=3, with two mechanisms
added — named precisely, not lumped as "mediation":

- **`--acceptance-test`** — a `run_ladder` flag (now allowed in `--mode mode`)
  that places the frozen `test_phase4.py` in the workspace.
- **`mellum-ncm.ts`** — the NCM verify gate, loaded via `--pi-extension` (the
  mode runner now forwards extra extensions): at settle it re-runs the named
  test and, while red, sends the worker back on the unmet concepts.

| config (`--mode mode`, 6-bit) | rung 9 | `mellum-ncm.ts` fires |
|---|---|---|
| no `--acceptance-test`, no gate ([record](../../ladder/2026-10-21-shipped-mode-rung9/)) | **0/3** | n/a |
| `--acceptance-test` + `mellum-ncm.ts` ([record](../../ladder/2026-10-21-mode-ncm-rung9/)) | **3/3** (110/145/108s) | **0** |

## The finding — credit by name

**`--acceptance-test` is the lever: 0/3 → 3/3.** Placing the frozen test gives
the v7 prompt the one named target it is built for, and the 6-bit just makes it
pass. `mellum-mode.ts`, `mellum-guards.ts` and `mellum-facts.ts` were on in
*both* the 0/3 and the 3/3 runs, so they are not the differentiator.

**`mellum-ncm.ts` contributed nothing measurable here.** It fired **0 times**:
the 6-bit passes the frozen test on the first attempt, so the gate's re-run
finds it green and never sends the worker back. 3/3 holds with or without it
(it is non-regressing). On the 3-bit it fired 21 times and the run still failed
([halving-3bit](2026-10-21-halving-3bit.md)) — forcing retries does not rescue a
model that cannot do the work.

## Decision

Ship the two enabling changes — `--acceptance-test` in Mode and the mode runner
forwarding `--pi-extension` — so the frozen-test mechanism and `mellum-ncm.ts`
reach the shipped worker. The measured win is **`--acceptance-test` in Mode**;
`mellum-ncm.ts` is carried as a non-regressing safety net whose active value is
still unproven.

## What would falsify this / Risks

- **`mellum-ncm.ts`'s value is unproven:** it needs a case where a capable
  worker self-exits with the test red and the gate recovers it to a pass (the
  phase-4 `id` miss). Absent that A/B, it is insurance, not a measured lift.
- **Risks:** n=1 per config, one machine; `--acceptance-test` is the single
  moved variable (the gate is dormant), so the credit sits on it by name.
