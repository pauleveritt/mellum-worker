# 2026-10-20: mediated rungs 6–9, v7 worker prompt — 12/12

**What is measured.** Mellum (`Mellum2.1-12B-A2.5B-Thinking-6bit`) on the four
AgentClinic rungs 6–9, three repeats each, direct mode on oMLX, **mediated**:
each rung gets its external, frozen phase test placed in the baseline
(`--acceptance-test tests/test_phase{1..4}.py`), which the worker cannot weaken,
and is verified by re-running that test (`--redispatch 5 --effort-ramp`).

**Config under test (the change from the 9/12 arms):**
- **v7 worker prompt** (`prompts/mellum-worker.md`): make the one named test
  pass — read the test *and* its spec, create the module the test imports, run
  *only* the named test, never edit the test, no other test files.
- **Focused test command**: the task and re-dispatch verify with
  `pytest tests/<the-test>`, not the whole `tests/` directory.
- **Trimmed tools**: `read, ls, bash, edit, write` (no `grep`/`find`, which
  shell out to `fd`/`rg` and are unavailable offline).
- **Fail-fast effort ramp**: start thinking off / 2k tokens, escalate to
  medium/8k then high/16k only as the frozen test keeps failing.

**Result (see `table.md`): 6–9 = 12/12.** Rung 9 (phase 4, resolve/reopen — the
auto-`id` miss) is **3/3**; across every prior arm it never exceeded 2/3, and
6–9 topped out at 9/12 (a19-facts-on, a21-control, a21-light).

**Honest framing.** n=3, one clean run (an earlier run polluted by a concurrent
duplicate was discarded). This is a *method* step — the mediated + v7 + fail-fast
stack vs the earlier Mellum Mode + project-facts stack — not a single-variable
ablation. v7 is specialized to the "make a failing test pass" shape, which is
Mellum's recommended best-measured usage. Compare mechanically with
`ladder/scripts/compare_runs.py`. Raw traces are not committed (per `AGENTS.md`);
this record keeps `run.json` + `final.md` per run and `table.md`.
