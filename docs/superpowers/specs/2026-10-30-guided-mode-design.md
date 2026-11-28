# Guided mode design: the harness fixes the code, on the record

**2026-10-30.** The lessons today show a learner a before run that fails and an
after run that passes, and let them switch a remedy on by hand. The next step,
decided with Andre, is to let the learner **drive the real worker at the
problem** from inside the course: say "fix the code", watch Mellum write the
fix into a code panel beside the lesson, re-run until it passes, and keep every
attempt on the record. This spec describes that product behavior. It builds on
the lesson tutor ([2026-10-29-lesson-tutor-design](2026-10-29-lesson-tutor-design.md))
and serves the learner-loop north star
([2026-10-30-learner-loop-and-track](../research/2026-10-30-learner-loop-and-track.md)).

Decided up front (Andre, 2026-10-30): the panel lives **inside Pi's TUI** (not a
web app); guided mode is a **shipped course feature** (SDD applies); the worker's
edits **stream into the panel** as it writes them.

## 1. Goals

- Turn each lesson and challenge into a loop the learner runs themselves:
  **name the failure → say "fix the code" → the worker builds a fix → re-run →
  FAIL becomes PASS**, with the code visible the whole time.
- Keep the loop honest: the learner reads the real run record, not the worker's
  own claim of success, and can run it again to optimise or to prove the fix
  holds.
- Record every attempt and the pathology it hit, so the PI/Mellum combo can
  later open a pull request with findings (the north star; not built here).
- Give the base Pi the learner runs the harness abilities the course teaches,
  so guided mode *is* the worker, not a demo of it.

## 2. The experience

A learner opens a lesson with `/lesson` (or `/start`). Guided mode adds, at the
fix step, a second surface: a **code panel** on the right of Pi's TUI showing
the file under test, beside the lesson stepper on the left. The loop:

1. **Read the failure.** The lesson's before run has failed; the stepper names
   the pathology (reasoning returned as text, reading more than fits, a
   foreground-server stall), and the run record says why.
2. **Fix the code.** The learner types `fix the code` (or presses a key). The
   harness dispatches the worker — the fixed Mellum, the lesson's remedy on —
   at the failing task.
3. **Watch it build.** The worker's edits stream into the code panel as it
   writes them, so the learner sees the fix take shape, not just a final diff.
4. **Re-run.** The harness runs the hidden grader again. The stepper shows
   FAIL becoming PASS, read from the run record.
5. **Again, or change it.** The learner can re-run to prove the fix is not a
   fluke, ask the harness to change something ("make it handle an empty list"),
   or hand-edit the panel themselves and re-run.

S0 is the shape with the machinery stripped away: a stand-in plays the model so
both runs finish in seconds. Guided mode makes S0 the *first interactive* case —
"fix the code" there calls the stand-in — and from E1 on it drives the real
Mellum.

## 3. What the learner can do

- **`fix the code`** — dispatch the worker at the current failing task. The
  remedy the lesson teaches is on, so the after arm is the fix in context.
- **re-run** — run the grader again on the current code, as many times as they
  like. A session is one isolated context and workspace, as today.
- **ask for a change** — a plain instruction to the worker ("return 0 for an
  empty input") that edits the same file; the panel streams it.
- **hand-edit** — type in the panel, save, and re-run; the learner's edit and
  the worker's edit go through the same file and the same grader.

## 4. The code panel

- **Where.** A right-hand panel in Pi's TUI, rendered by the course extension
  with `ctx.ui.custom` (the same overlay/inline mechanism the lesson stepper
  already uses, with key handling and `requestRender`). The lesson stepper
  stays on the left.
- **What.** The file the lesson's task writes (S0: `add.py`; a real lesson: the
  workspace file the worker edits). Read-only while the worker streams; editable
  when the learner takes over (Pi's `editor` dialog primitive backs the edit).
- **Streaming.** As the worker writes, the extension follows the worker's edit
  tool calls (`pi.on("tool_call", ...)`) and re-renders the panel to the file's
  current contents, so the learner sees each change land.
- **The learner is not interested in the recorded sessions.** The panel shows
  the *code* — the mechanism — never the `run.json`/`trace.jsonl` output dirs.

## 5. Architecture

Guided mode is one extension built on the lesson tutor, plus a thin dispatch
into the worker. No new runtime: the pieces exist.

- **Panel.** `ctx.ui.custom` renders the code panel and handles its keys;
  `ctx.ui.requestRender` refreshes it on each streamed edit. Pi's `editor`
  dialog backs hand-editing. (Both are in Pi today; §8 on why we still move to
  1.4.)
- **Dispatch.** "fix the code" starts a worker turn on the failing task with the
  lesson's remedy applied — the same path `/mellum` uses, the same guards and
  facts. The remedy is applied as the lessons already do (a `--remedy` unit, or
  the `before_provider_request` lever the units use).
- **Stream.** `pi.on("tool_call", ...)` sees the worker's `edit`/`write` calls;
  the extension reads the file after each and re-renders the panel. The worker's
  reasoning stays in the stepper's log, not the code panel.
- **Re-run.** The harness runs the challenge's grader (the existing
  `scripts/lesson-check.sh` / `learn/code/harness.py` path), and the stepper
  reads PASS/FAIL and the pathology counts from the run record, exactly as the
  Validation step does today.

## 6. The worker builds the fix

The after arm is already the real model building code; guided mode makes the
learner the one who dispatches it. "fix the code" is not a canned diff:

- It runs the fixed Mellum with the lesson's remedy on, against the failing
  task, in the lesson's session.
- The remedy shapes *how* the model writes the fix (repairs think tags, trims a
  long tool result, keeps it in the workspace) — the model still writes the
  code. S0 is the exception: its "model" is the stand-in, kept for speed.
- Done is read from re-running the grader, never the worker's final message —
  the exit-gate discipline the harness already teaches (don't trust the
  self-exit).

## 7. Recording

Every attempt is a run on the record, as runs are today: `run.json` with
`passed`, `checks_ran`, `stalled`, `tool_errors`, `compactions`, and the
pathology count the challenge caps. Guided mode adds nothing new to the record
format; it makes the learner the one generating the attempts. The north star —
the worker opening a pull request with what it learned across attempts — reads
this record. It is **out of scope here** and stays a research note until a
measured loop backs it.

## 8. Move the course to Pi 1.4

The panel primitives (`ctx.ui.custom`, the `editor` dialog) are in Pi 1.3, so
guided mode *can* build on the pinned version. But 1.4 fixes exactly the things
a step-by-step, panel-plus-dispatch flow leans on, so the course should move:

- Concurrent `custom()` panels and dialogs no longer clobber each other (a code
  panel open while a prompt or the worker runs).
- Extension tools stay active on resume and `/tree` (a lesson a learner comes
  back to).
- A session survives a tool call truncated at the output limit, and auto-retry
  covers more stream failures (a long model edit on a small local server).

Moving the pin is a measured-settings-adjacent change: bump `PI_VERSION` in
`install.sh`, the pin in the profile/docs, and reconcile the README install
lines and the changelog in one release. The ladder runs `--no-extensions`, so
the measured numbers are unaffected by the UI version; this is a runtime/UX
move, not a model-settings change.

## 9. Scope

- **S0 first.** Make S0 interactive end to end with the stand-in: "fix the
  code" flips the stand-in from the wrong answer to the right one, streams it
  into the panel, re-runs, PASS. Proves the loop with no GPU.
- **Then one real lesson (E1).** The real Mellum, the real `repair-think-tags`
  remedy, the real grader — the loop running for real, recorded and measured.
- **Shipped.** The base Pi the learner installs carries guided mode, so the
  course *is* the worker.

## 10. Risks and open questions

- **Streaming edits into a TUI panel is the unproven part.** `tool_call`
  gives the edit events and `requestRender` repaints, but a smooth
  stream-as-it-writes panel needs a spike before the full build. Fallback:
  render the file after each completed edit, not mid-token.
- **A long real-model turn on the local server** may be slow or hit the output
  limit; 1.4's truncation recovery helps, but the panel must show progress, not
  freeze.
- **Hand-edit versus worker-edit on the same file** needs a clear owner at any
  moment (read-only while the worker streams; editable when it is the learner's
  turn), or the two races corrupt the file.
- **"complete" for the grader** is the load-bearing word the harness already
  warns about: the re-run must be the hidden grader, not a worker-authored
  check.

## 11. Phases

| phase | ships |
| --- | --- |
| GM.1 | A spike: stream one `edit` tool call into a `ctx.ui.custom` code panel beside the stepper, on Pi 1.4. Decides the streaming approach (§10). |
| GM.2 | Move the course pin to Pi 1.4 (install.sh, profile, README lines, changelog). |
| GM.3 | S0 interactive: "fix the code" drives the stand-in, streams into the panel, re-runs to PASS. |
| GM.4 | E1 interactive: the real Mellum and remedy, recorded and read from the grader. |
| GM.5 | re-run and "ask for a change"; hand-edit with a clear edit owner. |
| GM.6+ | One phase per further lesson/challenge brought into guided mode. |

## Excluded

- The north-star autonomous loop (the worker opening a pull request with
  findings). It reads guided mode's records but is its own, later, measured
  piece.
- A web/browser editor. Decided: the panel is Pi's TUI.
- Any change to the recorded run format, the grader, the prompt, or the model
  settings — guided mode changes who drives, not what is measured.
