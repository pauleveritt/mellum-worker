# Phase 3b: delegated mode with the `delegate-to-mellum` skill available

Date: 2026-10-08. *The skill was removed in the lean-down pass (ablation A7, 2026-10-09) on this record's evidence; it is in git history before commit `aa0995f`.* Identical to [phase 3a](../phase3a-delegated-noskill/README.md)
except that the scratch workspace carries `.pi/skills/delegate-to-mellum/SKILL.md`,
which Pi lists in the parent's skills catalog. Nothing forces the parent to
read it. Three repeats per rung.

Command (historical: `--skill` and the skill were removed in the lean-down; rerun from a checkout before `e9ab783`):

```bash
uv run python -m ladder.run_ladder --mode delegated --skill --profile baseline --guards --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 900 --out docs/research/ladder/phase3b-delegated-skill
```

## Result

| rung | 3a, no skill | 3b, skill available |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 3/3 | 3/3 |
| 5 | 3/3 | 3/3 |

| measure (15 runs each) | 3a | 3b |
| --- | --- | --- |
| parent read `SKILL.md` | — | **2** |
| brief in the skill's template (`Files:`/`Change:`/`Test command:`/`Done when:`) | 0 | 3 |
| brief length, mean chars | 1,260 | 1,148 |
| child requests per run, mean | 11.0 | 13.2 |
| parent messages per run, mean | 6.6 | 6.9 |
| re-dispatch (`subagent` called twice) | 0 | 1 (4 r3) |
| nudges | 0 | 0 |
| parent ran the tests itself | 15 | 15 |

## Reading

**The skill was available in 15 runs and read in 2.** In those two
(2 r1, 5 r3) the brief followed the template; one more brief (5 r1) used the
template without a recorded read of the file. In the other twelve the parent
did what it did in 3a: scoped the task from the code, wrote its own brief,
verified with its own test run. The pass rate had no room to move and did
not.

So 3b does not measure what the skill does; it measures how often a frontier
parent that already scopes natively chooses to open an optional skill when
the request merely names the worker — about one time in seven. That is the
finding, and it is about the delivery mechanism, not the content. A skill
whose effect matters has to reach the parent unconditionally: the worker's
advertised description, or a project `AGENTS.md` line. Measuring the skill
itself is backlog item 3c.

The one re-dispatch (4 r3) is also the one run the loop breaker would have
touched: the child's first attempt took 30 requests and one call would have
been refused; the parent re-dispatched once and the run passed. That is the
skill's "re-dispatch once" rule working in the single run where the parent
had read it — n = 1, worth noting, not a result.

## What phase 3 establishes

- In delegated mode the recipe passes all five rungs, both with and without
  the skill, because the parent performs scoping and verification natively.
  The child never sees the user's sentence.
- The "B before A" ordering in the spec collapses here: a frontier parent is
  A by default. The direct-mode ladder (phases 0–2) remains the measurement
  of the worker on its own.
- The skill, as an optional project skill, is rarely read. Its content is
  untested at scale.

Caveats as in 3a: three repeats, a hosted parent whose behaviour can change,
sampled decoding throughout.

Raw traces, stdout and diffs: [`phase3b-delegated-skill.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase3b-delegated-skill.tar.gz).
