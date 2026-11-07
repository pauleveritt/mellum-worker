# E1 Reasoning Returned as Text, lesson check, 2026-10-30

Preregistered in
`docs/superpowers/research/2026-10-30-reasoning-as-text-check-prereg.md` at
`b7e538e`, run at `b7e538e` with `scripts/lesson-check.sh E1` on the LAN vLLM
host (vLLM `0.26.1rc1.dev1102+ge9d1398d9`, the 6-bit Mellum, model id
`mellum`), Pi 1.3.0. One session per arm, `--deadline 600 --stall 120`, no
`--grade`; the challenge's `record.json` caps `reasoning_as_text` at 0.

| Arm | Remedy | Hidden tests | `reasoning_as_text` | Result |
| --- | --- | --- | --- | --- |
| before | none | passed | 7 | **FAIL** (record) |
| after | `context/repair-think-tags` | passed | 0 | **PASS** |

**The lesson holds.** Each session's `run.json`, `layout.json` and
`leaked.json` are kept under `<arm>/`; traces are not in git.
