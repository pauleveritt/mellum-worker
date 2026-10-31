# Paul's findings digest: ten lessons from M.1–M.7 and the A-series

Date: 2026-10-20. The source for Paul's lessons in the Lessons track. Each
entry is one idea in the six-step form, with a badge on steps 1–5 and a
draft Interpretation. It cites existing records only: no run was made for
this digest, and everything measured here ran on oMLX. Nothing in it is a
llama.cpp number; the [reference run](../ladder/reference-llamacpp-rungs1-5/README.md)
covers rungs 1–5 and does not speak to these ablations.

**What is measured.** The oMLX ladder records in `evals/` and the
notes they point at, as cited per entry. Sample sizes are the records': 15
runs for rungs 1–5, 12 for rungs 6–9, 3 for screens.

**What is conjecture.** Every Interpretation, which is why each one names
its weakest badge. Transfer to another backend, another machine or another
project is not measured.

**Validation in this track.** Step 5 is validation, and for a settings
lesson that is the ladder runs that show the change held, not static
analysis. Where a lesson changes code as well, it also names the suite.

## Recommended order

The lessons are independent. This is a reading order, not a dependency
chain: each entry cites its own records, and Getting started is the only
prerequisite unless an entry says otherwise.

1. The primary agent is the wrong worker
2. A short prompt, not a procedure
3. Thinking is working memory
4. Guards for empty turns and loops
5. Project facts
6. Write only the files you list
7. Who holds the loop
8. A prose brief stops at its first reply
9. The intercom block is a prefill tax
10. One spec file per phase

---

## 1. The primary agent is the wrong worker

**Badge:** `cited`

- **Problem.** Run Mellum as the main agent and it passes 8 of 15 rungs;
  give it the operator's full profile and it passes 10. The same model as a
  bounded worker passes 15.
- **Eval case.** Ladder rungs 1–5, 15 runs each, oMLX. `phase0c-primary-plain`
  and `phase0c-primary-operator` are the primary baselines; A3 is the worker.
- **Evidence of the problem.** 8/15 plain, 10/15 with the operator profile,
  15/15 worker. The operator profile also sends almost five times the
  prefill (1,055k vs 308k chars per run) and is the slowest setup on every
  easy rung.
- **Solution.** Do not make the model the main agent. Give it a task, a
  tool set and a stop condition, and keep the plan and the checking outside.
- **Validation.** The same 15 rungs with the worker: 15/15, with 14.3
  requests per run and 54 s wall (A3).
- **Interpretation.** The weakest badge is `cited`: these are oMLX runs on
  one machine, and your llama.cpp numbers will differ. What transfers is
  the shape — a bounded worker with the parent holding plan and
  verification — not the rate. Open: a persona-free comparison on llama.cpp,
  rungs 1–5, would upgrade this to `reference-run`.

## 2. A short prompt, not a procedure

**Badge:** `cited`

- **Problem.** A prompt that narrates a six-step procedure makes the model
  spend turns on the narration and drift from what the project needs.
- **Eval case.** Rungs 1–5, 15 runs. A0 measures `replace` (the shipped
  agent file) against `append` (Pi's base prompt underneath). A2 removes the
  six-step block, A3 the five tool facts, A4 the missing-files line.
- **Evidence of the problem.** `append` uses more requests, errors and
  nudges than `replace` (A0). The procedure block removed cleanly: A2 is
  15/15 with 12.3 requests per run and no nudges. A4, removing the
  missing-files line, is 14/15 — the failure edited a test to pass.
- **Solution.** Prompt v5: 643 characters, the six test-command facts and
  the missing-files line, no procedure. The agent frontmatter shrank from
  17 lines to 13.
- **Validation.** A2 and A3 are 15/15; v4 repeated in A5 (15/15) sets the
  noise floor, and v5 is what ships.
- **Interpretation.** Weakest badge `cited`: oMLX, 15 runs. The lesson is
  that each line must earn its place, not that 643 is magic — a paragraph
  added without a run is a hypothesis. Open: a screen on llama.cpp of v5
  against a deliberately bloated prompt.

## 3. Thinking is working memory

**Badge:** `cited`

- **Problem.** Stripping earlier turns' thinking looks like a free cut in
  prefill, and it is not free: the model uses its own reasoning as working
  memory.
- **Eval case.** Rungs 1–5, 15 runs. A12 removes earlier turns' thinking
  from each request; A3 is the reference.
- **Evidence of the problem.** Prefill falls 57%, output tokens rise 73%,
  and wall goes from 54 s to 87 s. Passes drop to 14/15. The replayed
  thinking was doing work.
- **Solution.** Keep the thinking in the history. Optimise the prompt or
  the setup instead; do not edit the model's memory.
- **Validation.** A3's 15/15 at 54 s against A12's 14/15 at 87 s; the
  prefill saving does not buy wall time back.
- **Interpretation.** Weakest badge `cited`: oMLX's cache behaviour is part
  of this (86% of input tokens in A3 are cache hits), so a backend with
  different caching may show a different wall. Open: the same arm on
  llama.cpp, where the KV cache and prefix reuse differ.

## 4. Guards for empty turns and loops

**Badge:** `cited`

- **Problem.** A small model sometimes ends a turn with nothing, or edits
  and re-edits the same lines; without a guard the run stops early or
  spins.
- **Eval case.** Rungs 1–5, 15 runs. A1 removes the guard extension; the
  shipped guards are an empty-final nudge (at most three) and a loop
  breaker.
- **Evidence of the problem.** A1 is 13/15, and both failures are the empty
  turn the nudge answers. The guard version is 15/15.
- **Solution.** Ship the two guards in the worker, child-only. The nudge
  answers an empty final; the breaker refuses a repeat that would loop.
  Both are bounded, and the limits are in the record.
- **Validation.** 15/15 with the guards against 13/15 without; the failures
  are the exact shape the nudge handles.
- **Interpretation.** Weakest badge `cited`: one benchmark's failures, oMLX.
  A guard that fixes empty finals can still hide a model that does not know
  it is done; the lesson is narrower than "guards make it reliable". Open:
  the same A1 arm on llama.cpp.

## 5. Project facts

**Badge:** `cited`

- **Problem.** On a four-phase build from loose specs, the model cannot
  guess the project's test command or layout, so it runs the wrong command
  and writes outside the layout.
- **Eval case.** AgentClinic rungs 6–9, 12 runs each. A18 is facts off;
  A19 adds a `## Mellum` section of facts (at most 600 characters) and the
  detected `python -m pytest` fallback; A20 keeps only the fallback; A21
  repeats A19's fixture on Pi 1.1.0.
- **Evidence of the problem.** A18: 1/12 rescored (0/12 strict), median 50
  requests, 11 of 12 runs hit `No module named 'app'`. A19: 9/12, 15/15 on
  rungs 1–5, median 26 requests, no import error, empty write-list in all
  12. A20: 7/12, so the section carries about 75% of the gain.
- **Solution.** The facts section plus the detected test command. Commands
  the project states win; the fallback is for a pytest project with no test
  command; `MELLUM_MODE_FACTS=0` turns both off.
- **Validation.** A19's 9/12 against A18's 1/12, with the ship rule fixed
  before the run (15/15 on 1–5, 9/12 on 6–9, no added write-list entries).
- **Interpretation.** Weakest badge `cited`: one fixture family on oMLX.
  The facts are a pointer, not knowledge; a project whose conventions differ
  from the bullets gets no guarantee. Open: facts on llama.cpp, rungs 6–9.

## 6. Write only the files you list

**Badge:** `cited`

- **Problem.** A run can pass the hidden tests and still count as a failure
  because it wrote outside the project's layout — a stray `__init__.py`,
  `pytest.ini`, or its own test file.
- **Eval case.** AgentClinic rungs 6–9, 12 runs. The scorer's write-list
  column; A18 facts off, A19 facts on, A21 the lighter section without a
  `Write only:` line.
- **Evidence of the problem.** A18: of the six runs with a green project and
  hidden tests, five failed only the write list. A19: empty write-list in
  all 12. A21: 0 runs outside the layout even with `Write only:` removed.
- **Solution.** The layout facts, not a prohibition: tell the model the
  project's files and let the scorer hold it to them. A21 shows the
  `Write only:` line is not what does the work.
- **Validation.** A19 and A21 both at 0 runs outside the layout, against
  A18's 8/12.
- **Interpretation.** Weakest badge `cited`: the effect is measured on one
  fixture layout. A21's result also warns that a rule can look necessary and
  not be — remove one line only with a run. Open: the same arms on
  llama.cpp.

## 7. Who holds the loop

**Badge:** `cited`

- **Problem.** Three places can hold the loop: the worker alone, Mellum Mode
  inside the main session, or a delegated child under a parent. They differ
  in cost, not only in passes.
- **Eval case.** Rungs 1–5, 15 runs. A3 worker alone, A14/A17 Mode, A10
  delegated.
- **Evidence of the problem.** Worker 15/15, 14.3 requests, 54 s; delegated
  15/15, 11.1 requests, 54 s (the parent's tokens are not in the record);
  Mode 14/15 with prefill down 78% and wall unchanged because prefill was
  cached, and no parent round trip.
- **Solution.** Choose by what must be checked: the worker alone for a
  bounded edit; Mode when the main session should keep the context; the
  delegated child when a parent must stay in charge. The pass rates are
  close, so cost and control decide.
- **Validation.** A10 and A3 at 15/15; A14/A17 at 14/15 with the miss moving
  between rungs; A17 confirms Mode v0.1.2 did not regress.
- **Interpretation.** Weakest badge `cited`: cost numbers come from a shared,
  uncontrolled clock, and the parent's tokens are uncounted. "Mode is
  cheaper" is not measured end to end. Open: the same three setups on
  llama.cpp with the parent's tokens counted.

## 8. A prose brief stops at its first reply

**Badge:** `cited`

- **Problem.** Give a small model a multi-step brief and it treats the first
  "reply" instruction as the end, or spends 2.4× the time walking steps.
- **Eval case.** Rungs 1–5, 15 runs. A15 sends a Markdown brief one prompt
  per step in one session; A16 sends the same brief as one prompt.
- **Evidence of the problem.** A15: 15/15 but 2.4× the wall and 2.5× the
  output tokens of the sentence. A16: 11/15, because the one-prompt brief
  contained intermediate replies and the model stopped there.
- **Solution.** Send the sentence, or a brief with no intermediate replies.
  If the work needs steps, let the session's turns carry them.
- **Validation.** A15 meets the passes but loses on cost; A16 is a clean
  negative: the same content, one prompt, four fewer passes.
- **Interpretation.** Weakest badge `cited`: one family of briefs on oMLX.
  The negative result is the useful part — a brief is a shape, and shape
  changes behaviour. Open: brief shapes on llama.cpp.

## 9. The intercom block is a prefill tax

**Badge:** `cited`

- **Problem.** pi-subagents' intercom instructions ride in the child's
  prompt even when the parent never uses them.
- **Eval case.** Delegated 15 runs, A11: intercom bridge off against A10.
- **Evidence of the problem.** Child prompt 2,711 → 1,220 characters,
  prefill down 20%, wall unchanged. Passes stay 15/15 either way.
- **Solution.** Offer `intercomBridge.mode: off` as an opt-in for the worker;
  do not make it a default, because it is global to every subagent.
- **Validation.** A11 15/15, prefill −20%, wall flat.
- **Interpretation.** Weakest badge `cited`: prefill is not wall on a cached
  server, so this is a token saving, not a speed claim. Open: whether the
  saving matters on a backend without prefix caching.

## 10. One spec file per phase

**Badge:** `screen`

- **Problem.** A four-phase build guided by one joined `specs/roadmap.md`
  fails the last phase's automatic id, because the model cannot find the
  line that asks for it.
- **Eval case.** Rung 9, three runs each: the one-file roadmap alone, and
  the light facts section alone. Followed by A21's 9/12 on rungs 6–9.
- **Evidence of the problem.** The one-file roadmap misses the phase-4 id in
  5 of 6 runs (the screen plus its repeat), against 1 of 6 with one spec file
  per phase. n = 3 per arm, exploratory.
- **Solution.** Keep one spec file per phase. A21 confirms it in the fuller
  run: 9/12, rung 9 0/3.
- **Validation.** The screen's 5/6 vs 1/6 is a lead; A21's 9/12 is a cited
  record, but it does not isolate the roadmap against the section.
- **Interpretation.** Weakest badge `screen`: n = 3, exploratory, and the
  arms share the rest of the setup. This entry exists to show the badge
  system working — a real lead, not a rate. Open: a preregistered run on
  rung 9, both arms, n = 12.

---

## What these lessons are not

- Not a reference manual: the README and `docs/recipe.md` hold the settings.
- Not lessons about the Learning Center: only the worker's measured history.
- Not llama.cpp claims. Every cited record ran on oMLX; the one llama.cpp
  reference covers rungs 1–5 and says nothing about these ablations.
- Not advice without a record: each Solution repeats what a run changed, and
  a line not tested is a hypothesis.

**What would falsify this digest.** A lesson whose cited record does not
say what the entry claims; a badge stronger than its record; or a
`reference-run` claim resting on the oMLX records. Each lesson's review
checks those three.
