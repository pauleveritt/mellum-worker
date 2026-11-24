# easy — Mellum2.1 sft2 / sft3 tunes vs base (local llama.cpp, Q4_K_M)

Same harness and stack for every arm: `harness.py run --suite easy --arm vanilla
--remedy preset:easy --grade --repeat 6 --deadline 1800 --stall 120`, llama.cpp
build 12110, `backend.py serve` flags with `-m <gguf>` (`probe/serve-gguf.sh`),
Apple M5 Max 128 GiB, 2026-11-24. Only the served GGUF changes.

| arm | GGUF (HF snapshot) | pass | median req | at deadline | zero-tool exits | out-of-layout reps |
|---|---|---|---|---|---|---|
| base | JetBrains/…-GGUF Q4_K_M (`4159d68`) | **5/6** | 26 | 0 | 0 | 0 |
| sft3 | postrational/…-sft3-GGUF Q4_K_M (`000fa0c`) | **1/6** | 33 | 2 | 0 | 3 |
| sft2 | postrational/…-sft2-GGUF Q4_K_M (`0dba0e0`) | **1/6** | 107 | 4 | 0 | 4 |

| rep | base req/errs/wall | sft3 req/errs/wall | sft2 req/errs/wall |
|---|---|---|---|
| r0 | 18/2/63 PASS | 14/6/57 fail | 163/69/1801 fail |
| r1 | 25/3/82 fail | 35/10/91 PASS | 67/25/507 fail |
| r2 | 36/4/277 PASS | 104/51/1795 fail | 62/18/262 fail |
| r3 | 27/4/163 PASS | 31/9/105 fail | 102/55/1782 fail |
| r4 | 37/6/184 PASS | 28/10/239 fail | 112/59/1784 fail |
| r5 | 23/3/92 PASS | 108/49/1713 fail | 146/109/1763 PASS |

Tool-call probe (`probe/`, 3 single-turn cases × 5, profile sampling): base,
sft2 and sft3 each 15/15 parsed calls, `finish_reason: tool_calls`, none leaked
into content. Both tune GGUFs embed a chat template byte-identical to the base
(4,849 chars).

**Runs not recorded here**, all from contamination, all in `runs/` only:

- `…-sft2-easy`, `…-sft2-easy-rerun`: 0-request reps. A worker installed PyPI
  `pi` into the repo `.venv`, which shadowed the agent.
- `…-sft2-easy-b` (1/6): from r2 on, a worker had written `app.py` into
  `learn/code/suites/easy/base/`, which seeds every later workspace.
- `…-base-easy` (5/6): ran entirely on that polluted fixture. The clean rerun
  above also scored 5/6.

Conditions that still moved: sft2 r3–r5 ran after workers first removed, then
reinstalled, off-lockfile packages in the repo `.venv` (the venv was not
lockfile-exact before this session either). sft3 and base ran on the same
venv state.
