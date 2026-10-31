# Phase 0c (plain): Mellum as the primary agent in bare Pi

Date: 2026-10-08. The second baseline: Pi with `--no-extensions
--no-skills --no-context-files`, Pi's own base prompt (2,969 characters)
and full built-in tool set, Mellum as the model, the raw rung sentence.
This separates Superpowers' effect (the [operator variant](../phase0c-primary-operator/README.md))
from Pi's base prompt, and differs from the worker in direct mode by
exactly three things: no worker prompt, no tool restriction, no guards.
Sampled at Pi's defaults; three repeats; 600 s deadline.

```bash
uv run python -m ladder.run_ladder --mode primary --plain --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase0c-primary-plain
```

## Result

| rung | bare Pi | operator profile | worker alone (2b) | delegated (3a) |
| --- | --- | --- | --- | --- |
| 1 | 3/3 | 3/3 | 3/3 | 3/3 |
| 2 | 3/3 | 2/3 | 3/3 | 3/3 |
| 3 | 2/3 | 3/3 | 3/3 | 3/3 |
| 4 | 0/3 | 2/3 | 3/3 | 3/3 |
| 5 | 0/3 | 0/3 | 3/3 | 3/3 |
| total | 8/15 | 10/15 | 15/15 | 15/15 |

| measure (15 runs) | value |
| --- | --- |
| requests per run, mean / max | 13.1 / 30 |
| tool errors | 17 |
| empty final text | 4 |
| finals claiming the task is done while the tests fail | 3 |
| test file edited | 1 (rung 5 r1, `test_export.py`; the check fails the run) |
| whole-file `write` to an existing file / shrinking it | 1 / 1 (same run) |
| wall seconds per run, mean (untrusted) | 51 |

## The seven failures

- **Empty final, 4** (rung 3 r1, rung 4 r1, r2, rung 5 r2): the model
  edits one file, plans the next edit in its thinking, and the turn ends
  with no text and no tool call. Nothing in bare Pi re-prompts it.
- **False completion, 3** (rung 4 r3, rung 5 r1, r3): "The failing test has
  been fixed!" and "The issue has been fixed" with the tests still failing.
  Rung 5 r1 also rewrote `test_export.py` to make its claim true, through a
  whole-file `write` that shrank the file: the write-clobber pathology from
  `../local-ai-pi`, recorded here for the first time in this ladder.

## Reading

**Bare Pi is the worst of the three ways to run the model.** Fewer passes
than the operator profile (8 vs 10) and the only configuration in which
the model edited a test or claimed a false completion. Superpowers' skills,
for all their cost, gave the model a verification step it followed; Pi's
base prompt alone did not.

**The worker's three differences account for seven passes.** Same model,
same harness, same sentences: 8/15 here, 15/15 in phase 2b. The prompt's
completion facts remove the false claims (the task is complete only when
the test command exits 0), the nudge removes the empty finals, and the
tool restriction removes nothing the model used here, so the first two
carry the gain. The lean-down ablation measures which of them can go.

## Caveats

Three repeats; sampled decoding; Pi 1.0.2's base prompt, which changes
between releases.

Raw traces, stdout and diffs: [`phase0c-primary-plain.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase0c-primary-plain.tar.gz).
