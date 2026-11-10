# Hard mediated arm: the n=1 screen

## What is measured / what is conjecture

**Measured.** One hard session, the `worker` arm with the new mediated acceptance
arm on, gating phases 1 and 4, `--verify-max 5`, `--grade`, `--deadline 3000`,
on the local llama.cpp Mellum 2.1 Q4 backend. Run
`runs/2026-11-10-hard-mediated-n1/20261110T152255Z-hard-d38838` (raw is
git-ignored; this is a screen, not a recorded rate).

**Conjecture.** Everything about whether mediation moves hard. The gates did not
fire a re-dispatch this run, so this measures the arm running correctly, not the
loop rescuing a phase.

## The result

| | value |
| --- | --- |
| Verdict | FAIL (3 hidden checks missed) |
| Acceptance gate, phase 1 | pass, 1 attempt, 0 re-dispatch |
| Acceptance gate, phase 4 | pass, 1 attempt, 0 re-dispatch |
| Hidden checks, phases 1-6 | all green (home, board, add, resolve/reopen, p5, p6) |
| Hidden checks missed | migrations 2/6, visits 1/2 |
| Turns / wall | 313 / 2956 s (deadline 3000, hit) |
| Tool errors | 75 |
| Quality | FAIL (an unused `sqlite_utils` import; pyrefly advisory) |

## What it says, and what it does not

The arm runs end to end on a real hard session: it dropped the two frozen tests
into the workspace, ran each from its canonical copy after its phase, and both
came back green on the first attempt. So the deep phase-4 id invariant, the one
hard normally misses, was right first try this run.

It did not pass hard, and it does not show mediation helping. Two reasons, both
plain:

- **The misses are in ungated phases.** Every check through phase 6 passed; the
  only misses were migrations (2 of 6) and one visits check. Neither phase has an
  acceptance gate, so the arm had nothing to catch them. The gate cannot move a
  phase it does not watch.
- **The gates never went red, so the loop never ran.** Phases 1 and 4 passed
  first try, so `--verify-max` bought nothing this run. Whether re-dispatch
  rescues a failing phase against the model is still unmeasured.

And a confound to name: this run reached phase 6 and missed only 3 checks, far
fewer than the roughly 21 the 0/3 baseline misses, but it ran to a 3000 s
deadline and hit it. The stronger showing could be the longer budget, the
mediation, or run-to-run variance. At n=1 the three cannot be told apart.

## What would falsify this / risks

- A second hard run under the same settings that misses many more checks would
  show the 3-miss run was variance or the budget, not the arm.
- The arm would earn a win only when a gate goes red and the re-dispatch turns it
  green, and a preregistered n=3 (mediated against the Baseline Worker, same
  model, same deadline) separates mediation from the budget.
- Risk: the deadline is doing work here. A fair comparison fixes the same
  deadline across both arms and reports turns and requests, not wall.

## Next

- Add acceptance gates for the phases where the misses now sit (migrations and
  visits, phases 5-7), so the arm watches the hard parts.
- Then preregister the n=3: mediated vs Baseline Worker, same deadline, scored by
  the hidden grader, deciding on checks missed and requests.
