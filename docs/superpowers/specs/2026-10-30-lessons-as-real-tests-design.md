# Lessons as real tests: the model alone must fail

**2026-10-30 (Andre and Paul).** A lesson is only a lesson when the vanilla
model, unaided, genuinely fails a test — and the learner can run that test and
watch it fail, then watch a change make it pass. Today S0 fakes this with a
rigged stand-in (`fake-pi-wrong.sh` writes `a - b` on cue), which is why it
reads as hollow and has no runnable before. This spec sets the rule, reframes
S0 and S1, and ties the lessons to the baseline pages Paul wants. It builds on
the challenge/grader pattern four lessons already use, and feeds the Vanilla Pi
and Baseline Worker pages.

## 1. The rule

- **Each lesson is a task plus a test script.** The task lives in `task.md`
  (the model, or the learner, runs it). A grader — `grader/test_challenge.py`,
  the shape four lessons already have — checks the model's real output.
- **The vanilla model, alone, must fail the test.** If an un-helped model
  passes, there is nothing to train and the lesson is cut. The failure is real
  and recorded (a preregistered run), never a rigged stand-in.
- **The remedy (or the knob) makes it pass.** The after arm is the real model
  with one change — a remedy unit, a thinking level, a guard — nothing else.
- **No fakes in the learner's hands.** `fake-pi-wrong.sh` / `fake-pi.sh` leave
  the learner experience. A stand-in may remain only for an explicitly labelled,
  no-model mechanics demo, never dressed as a training lesson.

## 2. The recorder is the foundation (S0)

Before any number — quality or budget — there has to be a record. S0 is that
step: **add the recorder.**

- **S0 is not a model-fail lesson.** It is the setup every later lesson needs.
  Its one extension is `learn/code/record-pi.mjs` — the recorder, not a remedy.
- **S0 before:** vanilla Pi runs a task and leaves **no record** of what
  happened.
- **S0 after:** with the recorder added, the same run leaves a **record** —
  turns, tokens, wall clock, requests, tool calls, context. The learner sees the
  `run.json` appear and reads it.
- **From S1 onward the recorder is always in.** It is the measuring instrument
  the rest of the course assumes; no later lesson teaches it again.

S0's "test" is therefore: a run with the recorder produces a record carrying the
effort fields; without it, nothing. That is the before/after, and it is real —
no rigged model needed, because S0 is about the instrument, not the model.

## 3. The first real fail (S1): thinking low vs high

S1 is the first lesson that obeys the rule — a real model fail on a real knob.

- **One task, two thinking levels.** The vanilla model runs the task at
  `--thinking low` and at `--thinking high`. Low genuinely fails the grader (or
  burns a far worse budget for the same result); high passes.
- **Measured by the recorder** (always in from S1): the lesson shows both
  **quality** (the grader's pass/fail) and **budget** (turns, tokens, wall
  clock) at each level, so the learner sees the trade the knob makes.
- **The change is the knob, nothing else** — same prompt, same tools, same
  model, only `--thinking`.

## 4. Quality and budget are the two axes

Every lesson from S1 reports two things, both from the recorder:

- **Quality** — does the grader pass? (the hidden test on the model's output).
- **Budget** — turns, tokens, context, and wall clock (with an asterisk: wall
  clock is host-dependent, so it is a lead, not a rate).

A remedy that lifts quality at a budget cost, or holds quality for less budget,
is the kind of result a lesson exists to show.

## 5. Feeding the baseline pages (Paul's notes)

This rule is what the two baseline pages rest on. They come after "Intro to Pi
extensions", the eval harness and the eval suites in Getting Started.

- **Vanilla Pi 1.4** — the starting point: vanilla Pi with only the recorder (no
  remedy). Numbers on the Easy suite, three ways on the big Vast instance —
  **BF16, Q8, Q4** — reporting quality (passing Easy) and budget. Then: "this
  tutorial chooses Q4 to target 16 GB laptops," and a fresh baseline on the
  local A6000, with its numbers. End of page.
- **Baseline Worker** — starts from Vanilla Pi and adds only the bare minimum
  of prompt and guards the Easy lessons need to have any hope, then shows the
  numbers against Vanilla Pi, for both quality and budget.

Both pages are **measured**: the numbers come from preregistered runs on the
A6000 baseline rig and the Vast instance, recorded in `evals/`, never
typed by hand.

## 6. What this changes

- **Retire the fakes** from the learner path: `fake-pi-wrong.sh`, `fake-pi.sh`.
- **Reframe S0** as "Add the recorder" (before: no record; after: the record).
- **Build S1** as thinking-low-vs-high, the first real fail.
- **Give every remaining lesson** a `task.md` and a `grader/test_challenge.py`,
  with a recorded vanilla-model failure gating it — the four existing challenges
  (`reasoning-as-text`, `context-overflow`, `looking-around`,
  `running-commands`) are the pattern.
- **The lesson UI shows the before/after up front** — the failing test run and
  the passing one — not hidden behind a keypress on a single step.

## 7. Phases

| phase | ships |
| --- | --- |
| LT.1 | Reframe S0 as "Add the recorder": the page, the before (no record) and after (the record), fakes retired from S0. |
| LT.2 | S1, thinking low vs high: `task.md`, grader, a recorded vanilla fail at low and pass at high, quality + budget shown. |
| LT.3 | The Vanilla Pi 1.4 page: Easy on BF16/Q8/Q4 (Vast) + local A6000, quality + budget, Q4-for-16 GB rationale. |
| LT.4 | The Baseline Worker page: minimal prompt+guards vs Vanilla Pi, quality + budget. |
| LT.5+ | One phase per remaining lesson: give it a task + grader + a recorded vanilla fail; drop any that the model passes unaided. |

## Excluded

- Keeping any rigged stand-in in a training lesson.
- Hand-typed numbers on the baseline pages — all measured and recorded.
- Changing the existing graders, prompts or model settings of the four lessons
  that already obey the rule, except to surface their before/after.
