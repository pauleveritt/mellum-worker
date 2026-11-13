# Preregistration: the context budget on llama.cpp, easy

Date: 2026-10-24, written before the run. Phase LC.13A, task 3. The guard arm
([record](2026-10-24-nudge-llamacpp-screen.md)) is void because no nudge
fired: every empty final was `error` (a 51,697-token request against
`n_ctx` 50,176) or `length`. The window is therefore the first thing that has
to be settled, because lessons 1, 2, 4 and 8 all run on the suite that
overflowed.

**What is measured.** Whether the easy suite fits, and what pays for it: a
bigger window, or a compaction policy that does not refuse while the worker
is on. One suite, one task, one machine.

- Backend: `llama-server` 0.7.0 (build 11669), Mellum 2.1 `Q4_K_M`,
  `127.0.0.1:8002`, started by `uv run scripts/backend.py start`.
- Sampling: the learner's profile from `learn/code/profile`, `temperature 1`,
  `top_p 0.95`, `top_k 20`, `max_tokens 16384`.
- Runner: `uv run python learn/code/harness.py run --suite easy --arm worker
  --repeat 3 --grade`.

**The ceiling is the model, not the machine.** Mellum's own
`max_context_window` is 56,000 ([llamacpp.md](../../../backends/llamacpp.md)),
so 56,000 is the largest window this question can ask for. Memory is not the
constraint: KV at 50,000 tokens is 0.20 GB at `q8_0` on the 7 full-attention
layers, and the 50k server peaks at 8.38 GB of a 32 GiB machine. The observed
failure was 51,697 — only 4,300 tokens of headroom exist above it.

**One logical change, two files.** A window arm moves `[tool.mellum] context`
*and* the profile's `contextWindow`, because Pi sizes its compaction against
the profile while `llama-server` sizes `n_ctx` against `-c`. The arm is only
valid if the served window (`/props`, `n_ctx`) and the profile agree; the run
order is `context` edit → `scripts/backend.py stop` → `start` → `profile` →
`harness.py run`.

**Arms, easy only, n = 3** (the lesson template's n; see the conflict note in
[the arm inventory](2026-10-24-lc13a-arm-inventory.md#what-n)).

| Arm | Window | Compaction | One change against |
| --- | --- | --- | --- |
| `A-50k` | 50,000 (`n_ctx` 50,176) | refused | — the control |
| `B-56k` | 56,000 | refused | A: the window |
| `C-compact` | 50,000 | allowed | A: the refusal |

`C-compact` is **provisional**. It runs only if the instrument check below
shows Pi attempts auto-compaction in this headless path and the attempt is
visible; otherwise it is recorded as inexpressible and dropped, never as a
failure. A session whose trace cannot show whether compaction happened is
void for C.

**Instrument check, before any arm (n = 1, no claim).** One easy session at
`A-50k` with the recorder watching for a compaction event, read from the
trace and `stdout.txt`. Its numbers are not evidence for anything else: it is
a screen, n = 1, and carries a `screen` badge if it is cited at all.

**Amended 2026-10-24, before the arms ran.** The check is **inconclusive** and
C's fate moves to the arms. It ran one session: PASS, 33 requests, peak input
**1,639 tokens**, and zero `before_compact` rows. That is not evidence that Pi
never attempts compaction, because Pi's threshold is
`contextWindow - reserveTokens` — 50,000 - 16,384 = **33,616** by default
(Pi's own `docs/compaction.md`) — and this session
never came near it. So a null at n=1 cannot separate "never attempted" from
"never needed".

Two consequences, fixed before the arms. First, **C runs if any `A-50k` or
`B-56k` session records a `before_compact` row**; if none does, C is recorded
as unreachable in practice at this n and dropped. Second, the check's own
number is a warning about the control: 1,639 tokens here against the screen's
51,697 on the same suite and window means easy's demand varies by more than
an order of magnitude between sessions, so a window that "fits" at n=3 may be
fitting a short run rather than a bounded one.

**Reading.** Per arm: passes out of n; the peak input tokens over the
session's requests; how many requests exceeded 50,000 and 56,000; empty
finals by `stopReason`; wall; tool errors; and compaction events. Peak
demand is the number this arm exists to produce — it is the figure Task 4
inherits whatever the passes say.

**Decision rules, fixed now.**

1. `B-56k` passes every session and no request exceeds the served window: the
   window is the budget. `[tool.mellum] context` moves to 56,000 with its
   re-baseline, and the compaction refusal stays, because its reason (a
   lossy parent session and a lost on-marker) is untouched.
2. `B-56k` records a request above 56,000 and ends `error`: no window the
   model can serve pays for the easy suite as written. Recorded as the
   demand figure, and escalated to a suite or session change — **not** to a
   worker change, and not to a bigger window that llama.cpp cannot serve.
3. `C-compact` shows a compaction event and passes at least as many sessions
   as A: allowing compaction while the mode is on is the budget, as a
   product change with its own re-baseline and a check that the on-marker
   survives.
4. A and B both fail and C never ran: the budget is unsettled, Task 4 does
   not start, and the finding is the peak demand with the reason it cannot
   be paid.
5. No session in either arm records a `before_compact` row: the compaction
   refusal is unreachable in this path at this n, recorded as such, and the
   window is the only budget in question here — the refusal stays and is not
   described as the overflow's cause.
6. A session whose served `n_ctx` disagrees with its arm, whose profile
   `contextWindow` disagrees with the arm, or whose workspace was
   contaminated is invalid: excluded and named.

**Re-baseline, owed by this task.** At the settled window, `bare` and
`worker` on easy at n = 3, recorded as the new easy baseline rows. The old
rows stay as the 50k record and are labelled so; nothing in
`evals/` is touched.

**What is conjecture.** That three sessions of one task settle anything. Easy
is a single prompt, so `2/3` against `3/3` is one session, and the arm's
purpose is to fix the setting Task 4 runs under, not to publish a rate. That
the easy suite's demand is stable across sessions: it may be; the peak
demand column is what would show it.

**What would falsify this.** A request above 56,000 that passes — the
overflow explanation would be wrong and the failure was something else. A
session that ends `stop` with an empty final at either window — the
`stopReason` reading in the guard record would be incomplete. A compaction
event in `A-50k` or `B-56k` — the refusal would not be doing what the code
comment says. Any served window other than the arm's, or a run under a
different Pi version than the one named here.

**Risks.** 56,000 is 4,300 tokens above the observed failure; if demand sits
just over it the answer will look like an edge case and will not be one. The
`length` failures in the guard record are untouched by any of these arms: an
output cap is a different budget and stays Task 4's problem. One machine, one
quant, one task.

**Raw evidence.** `trace.jsonl`, `stdout.txt` and `diff.patch` per run go to
a `research-2026-10-24` release after review, never into git.
