# The lesson check, 2026-10-29

The preregistered check (`docs/superpowers/research/2026-10-29-lesson-check-prereg.md`):
every lesson's Run it yourself commands at the page's own n and deadline,
with and without its remedy, on the pinned vLLM host (RTX A6000, Mellum 2.1
BF16, vLLM 0.32.0, Pi 1.3.0; vast.ai instance 58204861), `baseline.py
lessons --full`, 120 s stall cutoff, three sessions at a time, sharing the
host with the flow rerun. Reading:
`docs/superpowers/research/2026-10-29-lesson-check.md`.

- `first/`: the run started 06:46 UTC at `eb02a92`. Its SSH tunnel dropped
  at about 09:20 UTC; every session after that ended in seconds with no
  model. **Void and excluded:** all of `thinking-working-memory`, all of
  `prose-brief`, and `one-spec-per-phase`'s `--specs joined` arm.
- `rerun/`: those seven arms again from 09:24 UTC at `3100bce`, through a
  runner that reopens the tunnel before each command. Mid-run, the worker
  gained an extracted `narrowTools` and an exported `withFacts`
  (behaviour-identical, its tests unchanged) and the harness gained
  `--remedy`/`--extension` (inert when unused); neither changes a session.

Tables (`first/table.md`, `rerun/table.md`) label lessons with the track
numbers of 2026-10-29 afternoon; the preregistration used the morning's:

| Page | Preregistered | Now |
| --- | --- | --- |
| `baseline` | E1 | removed (E1 is Read the Failure) |
| `write-only-listed` | E2 | removed |
| `project-facts` | E3 | M1 |
| `short-prompt` | E4 | M2 |
| `thinking-working-memory` | M1 | M4 |
| `guards-for-empty-turns` | M2 | M3 |
| `one-spec-per-phase` | M3 | M8 |
| `prose-brief` | M4 | M9 |
| `primary-agent` | H1 | H1 |

Each session's `run.json` (and `stalled.json`, `layout.json`, `leaked.json`
where present) is kept; traces and workspaces are not in git.
