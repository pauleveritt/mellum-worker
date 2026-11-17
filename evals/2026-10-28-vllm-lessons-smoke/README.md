# Lesson smoke run on vLLM, 2026-10-28

`scripts/baseline/baseline.py lessons` at commit `75b8761`: every lesson's
"Run it yourself" commands once per arm (n = 1), deadlines capped at 900 s,
120 s stall cutoff, three sessions at a time, on the pinned vLLM host (RTX
A6000, Mellum 2.1 BF16, vLLM 0.32.0, Pi 1.3.0; vast.ai instance 58114859).
It shows each command runs and grades; at n = 1 it says nothing about a
lesson's claim. The claim check is the preregistered `--full` run
(`docs/superpowers/research/2026-10-29-lesson-check-prereg.md`).

- `table.md`: one row per lesson, suite and arm, from each session's `run.json`.
- `<page>/<session>/`: `run.json`, and `stalled.json`, `layout.json` or
  `leaked.json` where present. `summary.md` is the command's own summary
  (its last-line column is uninformative; read `table.md`).

Raw traces, workspaces and profiles are not in git. H2 has no command.
