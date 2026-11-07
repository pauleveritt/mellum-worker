# E2 Reading More Than Fits, lesson check, 2026-10-30

Preregistered in
`docs/superpowers/research/2026-10-30-context-overflow-check-prereg.md` at
`687e7b3`, run at `687e7b3` with `scripts/lesson-check.sh E2` on the LAN vLLM
host (the 6-bit Mellum, `contextWindow` 65,536), Pi 1.3.0 with its default
compaction. One session per arm, `--deadline 900 --stall 180`, no `--grade`;
the challenge's `record.json` caps `compactions` at 0.

| Arm | Remedies | Hidden test | `compactions` | Peak context | Requests | Result |
| --- | --- | --- | --- | --- | --- | --- |
| before | `context/repair-think-tags` | failed | 13 | 50,720 | 99 | **FAIL** |
| after | + `context/trim-tool-output` | passed | 0 | 5,326 | 13 | **PASS** |

**The lesson holds.** Each session's `run.json`, `layout.json` and
`leaked.json` are kept under `<arm>/`; traces are not in git.
