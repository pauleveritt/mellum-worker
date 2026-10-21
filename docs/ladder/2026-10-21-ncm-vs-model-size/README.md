# 2026-10-21: the NCM gate × model size — it makes a worker try, not able

**What is measured.** `extensions/mellum-ncm.ts` (the NCM verify gate — re-runs
the frozen test at settle and, while red, sends the worker back on the unmet
concepts) against three model sizes on rung 9, n=1 each, frozen `test_phase4.py`
placed, guards on. The 1.5B also loads `content-tool-call-assist` (it cannot
emit structured tool calls otherwise).

Result (`table.md`):

- **6-bit Mellum: 3/3**, gate fired **0 times** — it passes first-try, so the
  gate never acts (dormant, non-regressing). Record:
  [`2026-10-21-mode-ncm-rung9`](../2026-10-21-mode-ncm-rung9/).
- **3-bit Mellum: FAIL** (291s) — gate fired dozens of times; the model makes
  imprecise edits and never lands the fix.
- **1.5B Qwen + assist: FAIL** (62s) — tool-calls via the assist plugin but
  loops running `pytest` without editing; the gate forces it back, still no fix.

**The finding.** `mellum-ncm.ts` is a verify/exit gate: it forces a worker to
keep going until the frozen test is green. It **cannot supply capability** — on
both small models it fires and they still fail, each at its own wall (3-bit:
edit precision; 1.5B: can run the test, can't fix the code). The only pass is
the capable 6-bit, which did not need the gate.

**Consequence.** The route to a smaller worker is to **add** capability (a LoRA
— format then a policy distill from Mellum's traces), not to **gate** an
incapable one. See [`halving-3bit`](../2026-10-21-halving-3bit.md) and the LoRA
direction in the notes.

Note: [`research/2026-10-21-ncm-vs-model-size.md`](../../superpowers/research/2026-10-21-ncm-vs-model-size.md).
Raw stripped per `AGENTS.md`.
