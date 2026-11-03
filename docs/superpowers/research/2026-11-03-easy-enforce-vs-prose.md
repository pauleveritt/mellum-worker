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

_(pending the run)_
