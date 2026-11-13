# Reconstructing the Nov 5-9 runs onto the scoreboard — what the real-harness draw showed

**What is measured:** the Nov 5-9 experiment configs, re-run through run.json-persisting
paths and recorded on `learn/scoreboard.md` (they had run through scratch rigs that wrote
to `/tmp`, so no board record survived). Backend: the local llama.cpp server on
`127.0.0.1:8001` serving `Mellum2.1-12B-A2.5B-Thinking` at Q4_K_M — the measured backend
per `AGENTS.md`, replacing the retired oMLX 6-bit the original notes used. Settings were
frozen; only run.json emission was added to the flow and ladder rigs (a recording change).
**What is conjecture:** why the one-pass exit-gate arm, 3/3 on the scratch screen, did not
reproduce at n=3 here (context blow-up vs a gate-induced live-server spiral vs draw
variance); and whether the medium remedy pass rates would hold at larger n.

## Provenance

Real shipped paths: `learn/code/flow_run.py` (flow), `learn/code/harness.py run` (remedy
screens), `ladder.run_ladder` (one-pass/plan). Each wrote a scoreboard-shaped `run.json`
recorded with `learn/code/scoreboard.py record`. The hidden grader is the oracle; a flow
run's board `passed` is its hidden full-pass verdict, never its visible gate. Raw traces
were not committed. 23 runs landed on the board; the plan arm produced no gradable run
(below).

## Results

**Flow (fills the previously empty tiers):**

| run | hidden | board `passed` | turns | wall | note |
|-----|--------|----------------|-------|------|------|
| flow medium | 17/18 | fail | 65 | 2467s | misses only the phase-4 resolve/reopen id invariant — the leak every arm shares |
| flow hard | 15/34 | fail | 128 | 12811s | phases 4 and 5 exhausted their attempts this draw, so fewer phases passed than the note's seed-verified 29-31/34 |

Flow hard is the first Hard-tier entry the board has ever carried. Its 15/34 is below the
2026-10-24 note's 29-31/34 because that run resumed from a seed with phases 1-5
hidden-verified; this is a full cold run where phases 4-5 did not pass, which also regressed
two earlier checks. Lower score, but an honest end-to-end cold draw.

**Medium remedy screens (`--arm worker`, n=3, deadline 1800):**

| remedy | pass | fastest pass (turns / wall) |
|--------|------|------------------------------|
| `context/trim-tool-output` | 3/3 | 47 / 329s |
| `prompt/think-briefly,guard/turn-cap` | 2/3 | 37 / 259s |
| `guard/no-live-server` | 2/3 | 67 / 358s |
| `context/repair-think-tags` | 2/3 | 48 / 298s |
| `guard/outside-workspace` | 1/3 | 21 / 103s |
| `guard/repeat-loops` | 1/3 | 15 / 32s |

These are single-remedy screens on the worker arm, each a lead, not a rate. `think-briefly
+ turn-cap` at 2/3 is consistent with the 2026-11-06 medium lead (median 16 under the cap +
reduced thinking).

**One-pass exit-gate (Arm A: `--mode direct --rung 13 --acceptance-test test_medium.py
--redispatch 5 --guards --thinking low` + the five measured remedies), n=3:**

| rep | passed | turns | wall | stop |
|-----|--------|-------|------|------|
| 1 | no | 202 | 2651s | error |
| 2 | no | 309 | 2761s | length |
| 3 | no | 260 | 2675s | length |

**0/3.** Every rep ran the worker's context to 200-300 turns and truncated
(`stop=length`/`error`, largest prompt ~290K chars, past the 50K window) instead of the
note's clean ~70-request pass. This is the honest divergence a real ladder run exists to
surface: the 2026-11-08 scratch screen's 3/3 does **not** reproduce at n=3 on the Q4
llama.cpp backend.

**Architect plan loop (Arm B: `--mode plan`), 1 rep, deadline 600:** `passed=False,
turns=0, deadline_hit=True` — plan mode hung to the full deadline with **zero requests**,
exactly reproducing the 2026-11-09 gap: the delegate/plan path's llama.cpp support is on the
`remove-omlx` branch, not `main`. No gradable run, so it is **not** recorded on the board (a
0-request hang is not a measured run); the gap is reported here instead of forging a row.

## Decision

- **The board now extends past Nov 3 and the Hard tier is no longer empty.** 23 runs
  recorded; `npm test` 717 pass, `zensical build` clean, no em-dash in the page.
- **One pass + exit-gate is downgraded from "full-pass route" to an unreproduced lead.** The
  scratch 3/3 did not hold at n=3 on the shipped ladder path; on this draw the arm
  non-converges into context truncation. Nothing about the measured settings was changed to
  chase a pass — the frozen config is what produced 0/3. Whether the cause is the gate's
  redispatch inflating context, the reduced-thinking preamble under-steering a long build,
  or draw variance is the next question, and it needs the backend's context handling looked
  at before a larger-n rerun.
- **The plan arm stays blocked** on llama.cpp until the `remove-omlx` delegate support
  lands; its cost remains the screened 300+ request baseline, unmeasured here.

## What would falsify this / Risks

- **Arm A's 0/3 may be a backend artefact, not a property of the arm.** The 290K-char
  prompts suggest context was not being trimmed/compacted against the 50K window; a run with
  working context management (or a larger window) could still reach the gate and pass, which
  would restore the lead. Until that is ruled out, read 0/3 as "did not reproduce on this
  setup," not "the arm is wrong."
- **n=3 per config is a screen, not a rate** — the medium remedy pass rates (3/3 … 1/3) and
  the flow scores are small-n draws; the board rows are labelled as the leads they are.
- **Flow hard's 15/34 is one cold run;** a seed-resumed run (phases 1-5 verified) would score
  higher, as the 2026-10-24 note did. The single cold number is not the hard ceiling.
- **The quant and backend differ from the original notes** (Q4 llama.cpp vs oMLX 6-bit); some
  of the divergence, especially Arm A, could be the serving stack rather than the config.
