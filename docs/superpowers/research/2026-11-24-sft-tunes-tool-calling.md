# Mellum2.1 sft2 and sft3 tunes: tool calling survives, pass rate does not (screen)

**What is measured.** Three easy-suite screens at n=6 on one machine on one day.
Every arm used the same harness, the same stack (`--arm vanilla --remedy
preset:easy`) and the same llama.cpp serve flags. Only the GGUF changes. Each
GGUF also got a single-turn tool-call probe. Record:
[`evals/2026-11-24-sft-tunes-easy/`](../../../evals/2026-11-24-sft-tunes-easy/table.md).

**What is conjecture.** Why the tunes lose ("Reading the traces" below) comes from
reading the traces, not from a measured cause.

## Question

Earlier Mellum tunes broke tool calling: zero-tool-call exits and collapse
([fine-tune note](2026-11-10-mellum-adherence-finetune.md)). Do the two new
Mellum2.1 tunes, `postrational/Mellum2.1-12B-A2.5B-Thinking-sft2` and `-sft3`
(Unsloth Q4_K_M GGUFs), keep tool calling in the worker loop?

## Result

| arm | pass | median requests | reps at 30-min deadline | zero-tool exits | probe |
|---|---|---|---|---|---|
| base (JetBrains Q4_K_M) | **5/6** | 26 | 0 | 0 | 15/15 |
| sft3 | **1/6** | 33 | 2 | 0 | 15/15 |
| sft2 | **1/6** | 107 | 4 | 0 | 15/15 |

- **Tool calling survives in both tunes.** Every rep in every arm called tools
  (minimum 11 calls). No run exited without one, and the probe parsed 15/15 for
  each GGUF. Both tunes embed the base chat template byte for byte. The old
  failure shape is absent.
- **Task success does not survive.** Each tune passes 1/6 against the base's 5/6
  on the same day. At n=6, 1/6 against 5/6 is Fisher two-sided p ≈ 0.08: a strong
  lead, not a rate. The base matches its earlier rows (4/6, 5/6), and a run of the
  base on a polluted fixture also gave 5/6.
- **Thrash.** Six of twelve tune reps ran to the deadline with 49–109 tool
  errors. No base rep came close (worst: 277 s, 6 errors).

## Reading the traces (conjecture)

**The tunes mangle long paths.** Workers retype absolute workspace paths, and the
tunes copy them wrong: `mellus-worker` for `mellum-worker`, `run/` for `runs/`,
`20261124-…` for `2026-11-24-…`. Each slip writes outside the workspace. That
produced a stray `../mellus-worker` holding a script that re-launches itself
(about 1,500 orphaned processes before it was stopped), a top-level `run/` in the
repo, and an `app.py` written into the suite's own `base/` fixture. Tune reps also
ran `grep -r` over the projects folder, `find /`, and built an unrelated `lat.md`
package. Seven of twelve tune reps left files outside the layout. No base rep did.
The pattern is consistent with a tune that kept the call format but lost precision
on copying and on staying in task.

## Harness findings (measured, separate from the tunes)

A worker can write anywhere its user can, and three things it reached here
contaminated the runs that followed:

1. **The repo `.venv`.** The harness runs under `uv run`, so `.venv/bin` leads
   PATH. Worker installs landed in the repo venv: pip and pytest, then PyPI
   `pi 0.1.2`, which shadowed the Pi agent and made every later session 0
   requests. A later worker removed the 44 off-lockfile packages, and another
   reinstalled them at newer versions.
2. **The suite fixture.** `copytree(base/)` copies untracked files, so the
   worker-written `app.py` seeded every later workspace. Only the writing rep was
   flagged `contaminated`.
3. **Paths outside the repo.** `../mellus-worker` holds the self-launching script.

Contaminated batches were rerun clean. The table above lists them.

## Decision

Neither tune is a candidate for the worker. Tool calling is no longer the
blocker; capability and path precision are. No setting changes.

## What would falsify this / risks

- n=6 per arm. A rerun at n=12 that brings either tune within one pass of the
  base would withdraw "pass rate does not survive".
- One easy suite only. Medium and hard were not run.
- The tunes' training goal is not known here. If they target other work (Satyrn's
  Python 3.15 tasks), easy may be the wrong yardstick.
- sft2 r3–r5 ran on a different repo-venv state than the other arms (see the
  record). The sft2 effect matches sft3, which ran clean.
- The probe is a scratch driver of three single-turn cases: a smoke check, not
  evidence on its own.
