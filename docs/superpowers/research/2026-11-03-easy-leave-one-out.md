# Easy stack, cold: which unit pulls its weight?

- **What is measured:** on easy, cold, `--arm worker`, the pass rate of the full
  easy preset and of the preset with one unit dropped — a leave-one-out ablation.
- **What is conjecture (until this run):** that each unit covers a different
  failure mode, so dropping the guard brings back the hang, dropping
  `name-the-layout` brings back the layout misses, and dropping either prose unit
  that re-states ignored guidance costs little.

## Why this run

The single-unit ablation showed no one unit cracks easy (all 1/3) and that
enforcement, not prose, owns the hang. It could not rank the units inside the
stack. Leave-one-out does: a unit that pulls weight drops the rate when removed.

## Arms, n, rule

Local Mellum 2.1 Q4 on `:8001`, easy, `--arm worker`, cold,
`--repeat 3 --grade --deadline 600 --stall 180`. Preset:
`prompt/name-the-layout, prompt/python-developer, guard/foreground-server,
prompt/verify-the-spec`.

| cell | `--remedy` |
|---|---|
| full | `preset:easy` |
| drop-layout | the preset without `prompt/name-the-layout` |
| drop-developer | without `prompt/python-developer` |
| drop-verify | without `prompt/verify-the-spec` |
| drop-guard | without `guard/foreground-server` |

Judged on the hidden grader (`tests_passed`), with stalls noted.

**Decision rule.** A unit whose removal drops the pass rate (or, for the guard,
brings back the stall) stays. A prose unit whose removal costs nothing is a
candidate to drop or replace with enforcement — and `name-the-layout` is the one
to then test against a layout-blocking guard.

## What would falsify / risks

- **Falsifies "each unit a different mode":** dropping any unit leaves the rate
  unchanged (the stack is redundant), or dropping a prose unit tanks it (prose
  pulls real weight after all).
- **Risk:** n=3, one model, one backend; a screen. Easy's rate is low and noisy,
  so a one-session swing can move a cell — read the stalls and the failure modes,
  not only the count.

## Result

_(pending the run)_
