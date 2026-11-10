# R.1b: think-briefly on Base, Easy Phase 2 — a cost screen

## For Andre

**Date:** 2026-11-09. **Cycle:** R.1b, cut from `integration` at `28647b1e` (F.7, F.8, R.1a).
**What is measured:** three local Easy Phase-2 sessions with `prompt/think-briefly` on Base, from R.1a's
checkpoint, read against R.1a (n = 1); two further Base sessions are recorded but are not part of the
reading. All in [the evals record](../../../evals/2026-11-09-r1b-think-briefly/table.md). A lead, not a rate.
**What is conjecture:** any rate; why a session needs one send-back or five; whether anything here
carries to Phase 1 on the pod, where the Easy count was taken.

**Result.** The preregistered rule, read as written, says *lead*: two of three accepted, median charged
output 17,735 against the 32,066 bar. The mechanism check beside it fails: the line did not make the
model think less, and cost per accepted phase did not fall. **Think-briefly does not go on to a frozen
count on this result, and it enters no preset.**

| Run | Accepted / strict | Requests | Charged output | Pi seconds | Thinking share | Replies |
| --- | --- | --- | --- | --- | --- | --- |
| R.1a (Base, reference) | yes / yes | 97 | 47,860 | 606.9 | 88% | 94 |
| brief-r01 | yes / yes | 45 | 13,170 | 328.7 | 86% | 43 |
| brief-r02 | yes / yes | 35 | 17,735 | 241.0 | 92% | 35 |
| brief-r03 | no / no (budget ending) | 86 | 65,212 | 914.7 | 90% | 85 |

### Why think-briefly and not no-live-server

The roadmap row screens your `guard/no-live-server` first *if the live-server spiral recurs*. It did not
in R.1a: of 90 tool calls, none started a server or probed `localhost`; the model checked the app in
process with `TestClient` throughout. A guard that never fires cannot change cost, and a screen in which
it never fires cannot reject it either. The row's other candidate targets where R.1a's output went:
thinking was about 136,300 of the 155,000 characters the model generated (88%); tool arguments 17,400;
plain text 1,400. So R.1b screens your `prompt/think-briefly`, taken unchanged from your `main`.

*Corrected 2026-11-09, after the runs:* the spiral does recur on this phase. Three of the six sessions
started `app.py` and probed `localhost` (base-r02: 5 starts and 6 probes; base-r03: 1 start; brief-r01:
6 and 7), each start cut at 30 s by `tool/bounded-commands`. R.1a was one of the three that did not. All
three spiralling sessions were accepted at or below the median cost of their arms; both costly sessions
(47,860 and 65,212) had no server start. The guard's condition is now met; a cost effect is not implied.

## Reading, fixed before the runs

- **Arm:** Base as counted plus one unit: `--arm vanilla --remedy
  tool/bounded-commands,check/mediated-test-settle,prompt/think-briefly --grade --stall 180`, Easy,
  `--grader f7-roadmap --phase 2 --from-checkpoint` the `base-r02` Phase-1 checkpoint (`ffced376`),
  counted against a fresh host card, `--pi-binary ~/.local/bin/pi`. Same Mac, server and checkpoint as
  R.1a.
- **n = 3**, the least a screen comparison takes. The reference is R.1a's one Base attempt (47,860 charged
  output, 97 requests). No new Base attempts: this asks whether the candidate is worth a large count, not
  what Base's Phase-2 rate is.
- **The bar.** Base sits at 4.47× Vanilla's median output tokens; the rule is 3×. Cutting Base by a third
  (to 0.67 of its cost) is what 3× needs if Vanilla does not move. Against R.1a: 32,066 charged output.
- **Rule.** *Lead, take to the frozen count:* at least two of three accepted and the median charged output
  of all three attempts at or under 32,066. *No lead:* one or none accepted, or a median at or above
  R.1a's 47,860. *Between:* a saving too small to clear 3× alone; not worth a large count by itself.
- **Also read:** cost per accepted phase (all three attempts' charged output over accepted phases),
  requests, Pi seconds, send-backs, and the thinking share of generated text (did the mechanism act?).

## Result

**Primary rule, as preregistered.** 2 of 3 accepted (brief-r03 ended on the output budget and was
rejected); charged output 13,170 / 17,735 / 65,212; median 17,735 against the 32,066 bar. The rule's
reading is *lead*.

**Mechanism check, beside it: failed.** Thinking was 86%, 92% and 90% of the characters generated,
against R.1a's 88%. The two cheap runs were short, not terse: 43 and 35 replies against R.1a's 94, with
median output per reply 112 and 380 against R.1a's 263. All-attempt charged output per accepted phase
is 96,117 / 2 = 48,059, against R.1a's 47,860 (an n = 1 reference). A line that left thinking per reply
where it was cannot be credited with the cheap runs, and on the measure that counts failures it saved
nothing.

**Conclusion.** Think-briefly does not go on to a frozen count on this result, and it enters no preset.
It stays an explicit unit, off by default.

**Before any deciding run, the cost rule must name its token count.** In the Easy count, Base's median
was 4.47× Vanilla's on charged output (33,993.5 / 7,598.5) but 3.43× on the output in the trace
(26,028 / 7,598.5); the difference is compaction, which the budget proxy charges and the trace omits.

### Not part of the reading

Two plain Base sessions (base-r02, base-r03) were run after the three above, on this session's own
judgment to test whether R.1a was typical, **without Paul's approval**. Both were accepted: 63 requests /
24,491 charged output / 355.3 s, and 23 / 17,957 / 273.3 s. They are recorded, not used above. The
sessions also showed the live-server spiral (see the correction above), and where cost went: the two
costly sessions, R.1a and brief-r03, were sent back four and five times over the model's contract.
brief-r02 overwrote the project's `AGENTS.md` with one line and was still accepted.

## Ladder run

Easy rung through `learn/code/harness.py run --grader f7-roadmap --phase 2 --from-checkpoint` the
`base-r02` Phase-1 checkpoint, `--host-card` (fresh, passed), `--pi-binary ~/.local/bin/pi`,
`--repeat 3` with think-briefly (and `--repeat 2` for the unapproved Base pair), followed live with
`ladder/scripts/watch_ladder.py`. The same llama-server process as R.1a. Raw traces under
`~/mellum-runs/r1b/` and `~/mellum-runs/r1b-base/`; a research release is owed when pushed.

## Persuasion → enforcement

Think-briefly is persuasion: one line appended to every user message by `before_provider_request`. It
arrived in every request and did not change how much the model thought per reply. The enforcement is
unchanged: `tool_call` bounds each command (it ended every server start at 30 s), and
`agent_before_settle` re-runs the frozen mediated tests. brief-r03 shows the send-back cap's limit: after
the fifth send-back the model kept editing, and only the budget ended it, on a build that no longer
imports, worse than its last red one.

## What would falsify this / Risks

- n = 3 against one reference is a screen. A large count could still find a median saving; this screen
  gives no mechanism to expect one.
- brief-r03's failure could be chance rather than the line; that changes cost per accepted phase, not
  the absent mechanism.
- The runs were sequential on one server across an evening; server drift is not ruled out.
