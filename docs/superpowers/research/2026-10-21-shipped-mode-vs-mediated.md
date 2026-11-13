# Shipped Mode vs direct+mediated on rung 9: the extensions aren't the lever

Date: 2026-10-21.

## What is measured

Rung 9 (AgentClinic phase 4), n=3, Mellum on oMLX:

| config | rung 9 | wall | turns |
|---|---|---|---|
| direct + **mediated** (v7 prompt, frozen `test_phase4.py`, `--redispatch 5 --effort-ramp`) — the [2026-10-20 win](2026-10-20-mediated-6-9-v7.md) | **3/3** | ~272s | ~20–30 |
| direct + mediated, **v6** prompt ([ablation Arm A](2026-10-20-v7-ablation.md)) | 3/3 | ~700s | — |
| **shipped Mode** (`--mode mode`: v7 + guards + facts + 7 tools), **no mediation** | **0/3** | 250 / 373 / 402s | 56 / 82 / 68 |

The shipped-Mode run was **verified correct** from its trace: system prompt is v7
(`<!-- mellum-worker prompt v7 -->`), the `mellum-facts.ts` block is injected
(the first user message carries `Project facts: … Test command: uv run python -m
pytest tests …`), guards are forced on, and the task is the native rung-9
`Implement specs/phase-4-resolve-reopen.md`. Record:
[`evals/2026-10-21-shipped-mode-rung9/`](../../ladder/2026-10-21-shipped-mode-rung9/).

## What is conjecture

- **Mechanism.** v7's system prompt ("make the one failing test pass — read the
  failing test, run only that test") mismatches Mode's native task, which places
  **no failing test**. The worker spends 56–82 turns hunting for one, then
  self-exits incomplete ("…perhaps we should consider the task complete…") — the
  phase-4 self-exit miss, back once the mediation is gone.
- **v7 regresses Mode** relative to the older v5 (A19 shipped v5 and got rung 9
  ≈ 1/3; v7 here → 0/3). Inferred from A19 plus the observed spin, not a
  v5-vs-v7 head-to-head in Mode.

## The finding

The 12/12 win is carried by the **mediation** — an external, complete, frozen
test plus verify-and-re-dispatch plus budget escalation — which is **direct-only**
in the ladder (`mode == "direct"`) and present in **none** of the shipped
extensions. With every extension engaged but no mediation, rung 9 is **0/3**. The
extensions (mode, guards, facts) are correctly loaded and are *not* the lever;
the mediation is.

## Decision

- **Do not ship v7 to Mode as-is.** Mode reads `prompts/mellum-worker.md`; v7 is
  coupled to a frozen test Mode does not provide, so shipping it regresses the
  product.
- **Next work:** bring the mediation to the Mode path (so a complete frozen test
  exists there and the exit is verified), and/or give Mode a task-shape-matched
  prompt. The extensions stay; the mediation must reach them.

## What would falsify this / Risks

- **Falsify:** Mode + a complete frozen test (mediation made reachable from Mode)
  cracks rung 9 → confirms the mediation, not the prompt, is the lever. Or a
  v5-in-Mode rung-9 run ≥ 1/3 while v7 = 0/3 → confirms v7 regresses Mode.
- **Risks:** n=3, one machine. Direct and Mode differ in more than the mediation
  (the v7 coupling, the 7-vs-5 tool set, in-session context), so this is a
  *stack* comparison, not a single-variable isolation of "mediation". The 0/3 is
  consistent with A19's rung-9 ≈ 1/3 floor, worsened by the v7 coupling.
