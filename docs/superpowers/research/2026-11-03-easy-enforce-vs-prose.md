# Easy, cold: does enforcement beat prose?

- **What is measured:** on the easy suite, cold (no `AGENTS.md`), the `worker`
  arm, which single remedy lifts the 1/3 baseline — a hard guard, a mechanism
  tool, or two prose fragments.
- **What is conjecture (until this run):** that for a fixed small model, a
  mechanism or a guard beats a prose rule, because the model reads prose and
  ignores it (the warm-vs-cold run showed cold models read `AGENTS.md`'s "do not
  start servers" and hung anyway).

## Arms, n, rule

Local Mellum 2.1 Q4 on llama-server `:8001`, easy, `--arm worker`, cold,
`--repeat 3 --grade --deadline 600 --stall 180`. Baseline reused from the
warm-vs-cold run (worker cold = 1/3, same machine, same day).

| cell | `--remedy` |
|---|---|
| guard | `guard/foreground-server` |
| tool | `tool/background-long-commands` |
| prose | `prompt/name-the-layout,prompt/verify-the-spec` |

Judged on the hidden grader (`tests_passed`), with stalls and turns noted.

**Decision rule.** The dominant easy failure is the foreground hang. If the
guard or the tool lifts the baseline and cuts the stalls while the two prose
units do not, the easy stack should lead with enforcement and demote the prose
units to leads. If prose matches enforcement, the "reading ≠ obeying" claim is
wrong for this model and the prose units stay.

## What would falsify / risks

- **Falsifies "enforce, don't ask":** the prose cell lifts the baseline as much
  as the guard/tool cell.
- **Risk:** n=3 screen, one model, one backend; a lead, not a rate. The baseline
  is reused, not re-run in this batch, so same-day drift is uncontrolled.

## Result

Run 2026-11-03, cold, `--arm worker`, easy, n=3. Baseline reused (worker cold).

| cell | oracle | composite | stalled | turns~ |
|---|---|---|---|---|
| baseline | 1/3 | 1/3 | 2/3 | 23 |
| guard `foreground-server` | 1/3 | 1/3 | **0/3** | 20 |
| tool `background-long-commands` | 1/3 | 1/3 | **0/3** | 24 |
| prose `name-the-layout,verify-the-spec` | 1/3 | 1/3 | 2/3 | 22 |

**On the hang, enforcement wins and prose does nothing.** The guard (blocks the
foreground start) and the tool (reruns it in the background) both cut the stall
to 0/3; the two prose units left it at 2/3, the baseline rate — the model started
`uv run python app.py` and `uvicorn --reload` and hung, exactly as it did under
`AGENTS.md`'s ignored "do not start servers". For the foreground pathology,
"enforce, don't ask" holds: a guard or a tool fixes it, a prose rule does not.

**But no single unit lifts the pass rate** — every cell is 1/3, the baseline.
Eliminating the hang (guard/tool at 0 stalls) did not raise the oracle, because
easy cold fails in more than one way: stop the hang and the model still misses
the layout (`main.py`, `ModuleNotFoundError: app`) or writes a broken route. One
remedy fixes one failure mode; the pass needs them all. So the easy stack is not
prose bloat to strip — each unit covers a different mode — it is a stack because
the task has several modes, and a single unit cannot crack it.

**The honest limit.** This ablation cleanly tested only the *hang* mode, where
prose was never the right tool anyway (`name-the-layout` is about layout,
`verify-the-spec` about verification). It shows enforcement owns the hang and
prose is read-and-ignored for it — but it does not isolate whether a prose rule
or a hard guard is better for the *layout* mode. That needs its own test: a guard
that blocks a write outside the declared layout (the harness already tracks
`out_of_layout`) versus `name-the-layout`'s prose, scored on the layout checks.

**Decision.** Keep enforcement (the guard or the `background-long-commands` tool)
as the fix for the foreground hang — it is strictly better than the prose there.
Do not strip the prose units on this evidence: the pass rate is multi-modal and
single-unit ablation cannot rank the stack. The next run is a *stack* comparison
(an enforcement-led stack vs the current easy preset) and a layout-mode
enforce-vs-prose test — not more single units.

