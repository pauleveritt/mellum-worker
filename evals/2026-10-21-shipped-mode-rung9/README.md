# 2026-10-21: shipped Mode on rung 9 — 0/3

**What is measured.** The shipped worker — `run_ladder --mode mode` (Mellum Mode:
the v7 worker prompt, guards forced on, project-facts injected, the 7-tool set),
with **no mediation** — on rung 9 (phase 4), n=3, oMLX.

**Result (`table.md`): 0/3.** Walls 250 / 373 / 402s; the worker spun 56 / 82 /
68 turns and self-exited incomplete each time. Contrast the direct+**mediated**
run on the same rung ([2026-10-20](../2026-10-20-mediated-6-9-v7/)): **3/3**.

**Run verified correct** (from the trace): system prompt is v7, the
`mellum-facts.ts` block is present in the first user message, guards are on, task
is the native `Implement specs/phase-4-resolve-reopen.md`. So the 0/3 is the
genuine shipped-worker result, not a misconfiguration — confirmed before reading
anything into it.

**Why it fails.** v7 ("make the one failing test pass — read the failing test")
assumes a frozen test that Mode never places, so the worker hunts for a
non-existent test and self-exits. The mediation (the external complete frozen
test + verify/re-dispatch) is what makes the exit honest, and it is **direct-only**
in the ladder — absent from every shipped extension.

**Prerequisite to even launch.** Mode needs the `omlx` provider registered in
`~/.pi/agent/models.json` (from `templates/pi/models.omlx.json`); without it Pi
errors "model not found". Direct mode registers the provider itself.

Note: [`research/2026-10-21-shipped-mode-vs-mediated.md`](../../superpowers/research/2026-10-21-shipped-mode-vs-mediated.md).
Raw `trace.jsonl` / `stdout.txt` / `diff.patch` are stripped per `AGENTS.md`;
each run keeps `run.json` + `final.md`.
