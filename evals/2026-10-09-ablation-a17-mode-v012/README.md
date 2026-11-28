# A17: Mellum Mode as shipped in mellum-worker v0.1.2

**What is measured.** The A14 launch (mode, baseline profile, rungs 1–5,
three repeats, deadline 600) with the shipped extension
`~/.pi/agent/git/github.com/pauleveritt/mellum-worker/extensions/mellum-mode.ts`
(v0.1.2) in place of `.pi/mellum/mellum-mode.ts`, no separate guards
extension (the package's Mode runs its own guards), and the mirrored profile
with the mellum-worker package removed so the extension loads once. Driver:
a wrapper that monkeypatches `run_ladder.MODE_EXT`, `build_pi_mode_args`,
and `mirror_agent_dir`; the ladder itself still points at the repo copy.

**What is conjecture.** That the wall-time difference from A14 is server
and cache state, not the code: nothing on Mellum's request path changed
between the two extensions.

## Result

| | A14 (repo copy, 2026-10-09) | A17 (shipped v0.1.2) |
| --- | --- | --- |
| passes | 14/15 (miss on rung 4) | 14/15 (miss on rung 5, run 2) |
| requests per run, mean | 13.1 | 12.9 |
| wall s per run, mean | 70 | 44 |
| wall by rung | 24 / 76 / 31 / 99 / 122 | 12 / 42 / 24 / 75 / 66 |
| nudges, total (runs with one) | 7 (4) | 3 (2) |
| tool errors, total (runs with one) | 13 (7) | 12 (8) |

The one failure ended with the text "Now let's run the tests again." and a
`stop`: a final turn with words but no tool call, which the empty-final
nudge does not treat as empty. A14's miss was a different rung.

## What changed in the extension

v0.1.2 adds a per-span summary line, a commands list and a missing-file
flag to the handoff, a `/mellum off` notification, and a JSONL run record
written at deactivation. The request filter, prompt, tools and guards are
unchanged. In headless mode the record is never written (no `/mellum off`),
so this phase exercised the counters and the handoff path only.

## What would falsify this

A rerun of A14's exact launch today landing near 70 s would show the wall
difference is in the code, not the server. A second A17 landing near 70 s
would show the same the other way.

## Risks

- The ladder measures the repo copy by default; the shipped copy had
  diverged by 260 lines before this phase. Until the ladder points at the
  package, "measured" and "shipped" can drift again.
- One miss in fifteen is within what A14 and A10 already showed; this phase
  does not distinguish 14/15 from 15/15.

Raw traces, stdout and diffs: [`ablation-a17-mode-v012.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a17-mode-v012.tar.gz).
