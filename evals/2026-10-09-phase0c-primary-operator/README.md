# Phase 0c (operator): Mellum as the primary agent in the operator's own profile

Date: 2026-10-08. The baseline the worker recipe is measured against: what
happens if you skip the recipe and just select Mellum as the model in your
normal Pi. The operator's `~/.pi/agent` is mirrored into a temporary agent
directory (Superpowers, pi-subagents, context7, the `~/.agents/skills`
catalog, Superpowers' bootstrap active), the model is Mellum, and the raw
rung sentence is the prompt. No worker exists in the workspace. The
ladder's recorder is the only addition. Sampled at Pi's defaults
(`temperature 1, top_p 0.95, top_k 20, max_tokens 16384`), which is what
the operator's `models.json` sends. Three repeats, 600 s deadline.

```bash
uv run python -m ladder.run_ladder --mode primary --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase0c-primary-operator
```

## Result

| rung | primary, operator profile | worker alone (direct, 1d) | via your Pi (delegated, 3a) |
| --- | --- | --- | --- |
| 1 | 3/3 | 3/3 | 3/3 |
| 2 | 2/3 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 | 3/3 |
| 4 | 2/3 | 2/3 | 3/3 |
| 5 | 0/3 | 3/3 | 3/3 |
| total | 10/15 | 14/15 | 15/15 |

| measure (15 runs) | value |
| --- | --- |
| system prompt, chars | 17,091 (direct mode: 4,572; the child: 3,580) |
| largest prompt, chars | 129,952 (about 32k tokens; the context window is 56k) |
| requests per run, mean | 13.7 |
| tool errors (runs with any) | 10 (8) |
| skill files read, total | 18 across 15 runs |
| finals that announce a Superpowers skill ("Using …") | 6 |
| empty final text | 2 |
| wall seconds per run, mean (untrusted) | 72 |

## What happened

The recovery report's failure did not reproduce. In this harness and
version (Pi 1.0.2, Superpowers as installed on 2026-10-08) Mellum reads
the skill files Superpowers' bootstrap points it to and follows them: it
announced `systematic-debugging`, `verification-before-completion`, and
`brainstorming` by name, ran their steps, and ran the tests itself before
reporting. Ten of fifteen tasks passed this way, including two of three
three-file fixes with a named failing test.

The five failures, by cause:

- **Brainstorming gate, 2 (rung 2 r2, rung 5 r1).** The model classified
  the task as "bounded", asked one clarifying question as the skill
  instructs, and stopped. In a headless run nobody answers. In an
  interactive session the user would, and the run might then pass; the
  ladder cannot say.
- **Empty turn, 2 (rung 4 r3, rung 5 r2).** Thinking ends with "Let's
  edit" or "Use find for .py files", the text block is empty, the turn
  stops. The same pathology as the worker's one residual failure in direct
  mode (1d rung 4 r3). Nothing in the operator profile nudges it.
- **Honest partial, 1 (rung 5 r3).** Twenty-four requests under
  `systematic-debugging`, one of the three failing tests fixed, the rest
  reported as remaining.

## Reading

**As the primary agent on these fixtures, Mellum is usable up to rung 4 and
fails rung 5.** The worker is not an escape from a broken primary mode; it
is an improvement at the top of the ladder: 0/3 → 3/3 on rung 5 (direct,
1d) and the delegated recipe is 15/15 because the parent scopes rung 5
before the child sees it.

**Where the four extra passes come from.** Two are the brainstorming gate,
which the worker never triggers because it has no skills. Two are rung 5
scoping, which the worker's prompt facts cover ("the task is complete only
when the test command exits 0; if it fails, read, change, run again") and
the delegated parent covers by briefing. The empty-turn pathology is shared
and is the subject of phase 2b.

**Cost.** The operator profile's system prompt is 3.7× the worker's and the
conversations reach 130k characters, within the 56k-token window but with
no room for a larger repository; the worker's largest prompt in 1d was
60k characters.

**What this does not say.** That the recovery report was wrong at the time:
it was recorded under a different harness and build. That an interactive
user would see 10/15: they would answer the brainstorming question and
might see 12/15. That Mellum in the operator profile handles anything
larger than these fixtures.

## Caveats

Three repeats; sampled decoding; one Superpowers version, whose bootstrap
prompt changes between releases and is the largest single input here.
Phase 0c plain (no extensions, skills, or context files) separates
Superpowers' effect from Pi's base prompt.

Raw traces, stdout and diffs: [`phase0c-primary-operator.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase0c-primary-operator.tar.gz).
