# Phase 0b: baseline profile, worker prompt v3

Date: 2026-10-08. Same server profile, launch, rungs, and repeats as
[phase 0](../phase0-baseline/README.md); the only change is the worker prompt,
v2 → v3. Run after the first interactive pi-subagents run; the prompt change
was committed before this ladder run.

Command:

```bash
uv run python -m ladder.run_ladder --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --repeat 3 --deadline 600 --out docs/research/ladder/phase0b-baseline-v3
```

## What changed in the prompt

v3 replaced the test-command section with facts and added two sentences:

- "A command named in the task is the command" moved first; "the command runs
  in the directory that holds that pyproject.toml or package.json" was added
  (the `node --test` rule was wrong from a repository root).
- **"The task is complete only when the test command exits 0."**
- Step 5: **"If it fails, read the failure, change the code, and run it again."**

Nothing else changed. No guard, no server setting, no sampling change.

## Result

| rung | phase 0 (v2) | phase 0b (v3) |
| --- | --- | --- |
| 1 | 3/3 | 3/3 |
| 2 | 3/3 | 3/3 |
| 3 | 3/3 | 3/3 |
| 4 | 2/3 | 3/3 |
| 5 | 0/3 | 3/3 |

15 of 15. Full columns in [table.md](table.md).

In phase 0 every rung-5 failure was an honest report of still-failing tests
after one edit cycle. The two added sentences are facts about when the task
ends, and the model now iterates: rung 5's three runs used 19, 27, and 17 requests
(mean across the phase 14.3, vs 13.3 in phase 0), and the largest prompt grew
to 76,248 chars (rung 5 r1) — still under the 200,000-char gate, but the
iterations cost context.

This matches the local-ai-pi finding that supplied facts change behaviour
where rules of conduct did not. It also means the baseline profile already
passes the whole ladder in direct mode; phase 1's question becomes whether
the tuned profile costs or buys anything, not whether it rescues failures.

## Non-zero pathology columns

| column | runs | note |
| --- | --- | --- |
| `write_existing` | 3 (2 r2, 4 r2, 5 r2) | all grew the file; `write_shrink` 0 |
| `empty_final` | 1 (3 r3) | the rename was complete and tests passed; the final turn had no visible text — a pass the parent could misread as nothing happened |
| `edit_anchor_failures` | 2 runs | recovered |
| `tool_errors` | 6 runs | failing-test bash exits plus the anchors above |
| `max_identical_streak` ≥ 5, `bash_file_mutations`, `deadline_hit`, `thinking_reentries` | 0 | |

## Caveat

All requests were sampled, not greedy: Pi sent `temperature 1`, `top_p 0.95`, `top_k 20`, `max_tokens 16384`, `presence_penalty 0` on every request, and oMLX gives request values precedence over the model profile. Three repeats per rung. The profile and prompt are fixed; the fixtures are small. This is a
gate, not an error rate.

Raw traces, stdout and diffs: [`phase0b-baseline-v3.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/phase0b-baseline-v3.tar.gz).
