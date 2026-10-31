# Lessons that left the track, and the evidence they carried

**What is measured.** Nothing new. This note keeps the evidence of lesson
pages that left the lesson track on 2026-10-29 under the uniform-lessons
contract ([spec](../specs/2026-10-29-uniform-lessons-design.md)): every lesson
shows one failure, applies one remedy, and goes from FAIL to PASS on a
challenge of its own. A page that could not do that left the track. Each
section links the page as it stood at commit `c5f125a`, the last commit where
it existed, so its full text, tables and run lines stay readable.

**What is conjecture.** Each page's own claims, at the badge it gave them. The
2026-10-29 lesson check ([note](2026-10-29-lesson-check.md)) held for none of
them.

## M5 Thinking Is Working Memory

[Page at `c5f125a`](https://github.com/andrevanzuydam/mellum-worker/blob/c5f125a/learn/lessons/medium/thinking-is-working-memory.md).

- **Why it left.** Keeping earlier reasoning is what Pi does when nothing
  strips it. The failure needs a fault injected (`--arm strip-thinking`,
  `MELLUM_STRIP_THINKING=1`), not a remedy applied, so there is no unit to
  turn a FAIL into a PASS.
- **Evidence.** Thinking spends the output budget: a one-turn smoke at
  `max_tokens 32` returned `content: ''` with 32 completion tokens spent and
  `finish_reason: stop`; at `max_tokens 200` the same prompt returned its
  reasoning and then the answer. The suites' failing runs include finals ended
  by `length` on Bronze and Silver.
- **Lesson check, 2026-10-29** (vLLM host, n = 3 per arm): keeping reasoning
  passed 2 of 3 on Bronze and 1 of 3 on Silver; stripping it passed 3 of 3 on
  both. It did not hold, and points the other way from the oMLX ladder result;
  prefix caching on vLLM may be why, unmeasured.
- **Kept as** the pathologies entry "Thinking spends the answer budget".

## M9 One Spec per Phase

[Page at `c5f125a`](https://github.com/andrevanzuydam/mellum-worker/blob/c5f125a/learn/lessons/medium/one-spec-per-phase.md).

- **Why it left.** The remedy is the brief's layout (`--specs split`), a
  harness flag, not a unit a learner can apply in a session.
- **Evidence.** Silver, n = 3 per arm on llama.cpp: two of six sessions
  finished while the project could not import (an unterminated string in
  `app.py`; a dataclass field without a default in `models.py`), both
  `checks_ran: false`. Phase-4 missing was `joined` {5, 0} against `split`
  {0, 3}: a null under the preregistered rule. What moved usable sessions off
  the floor was each phase's **Acceptance** list in the file the brief names.
- **Lesson check, 2026-10-29:** split 1 of 3, joined 1 of 3, a tie.
- **Kept as** the `BACKLOG.md` entry "A unit that shapes the task in a
  session".

## M10 Steps, Not One Brief

[Page at `c5f125a`](https://github.com/andrevanzuydam/mellum-worker/blob/c5f125a/learn/lessons/medium/steps-not-one-brief.md).

- **Why it left.** The remedy is leaving out `--single-prompt`, a harness
  flag, not a unit.
- **Evidence.** Silver, n = 3 per arm on llama.cpp: the one-brief arm never
  produced a project its checks could open (18 of 18 missing,
  `checks_ran: false`, three of three); the checks ran in three of three
  stepped sessions. One brief was cheaper in requests and wall, but not in
  peak context.
- **Lesson check, 2026-10-29:** 0 of 3 in both arms.
- **Kept as** the same backlog entry as M9.

## H1 Who Drives

[Page at `c5f125a`](https://github.com/andrevanzuydam/mellum-worker/blob/c5f125a/learn/lessons/hard/who-drives.md).

- **Why it left.** Who drives is a role, the operator's or the harness's, not
  a unit; its measured comparison used the `bare` and `worker` arms.
- **Evidence.** Twelve sessions on an Apple M1 Pro (llama.cpp, `--deadline
  2700`, 2026-10-25, preregistered): Bronze 1/3 for each arm, Silver 0/3 for
  each, a null on both. How they failed differed: two of three `bare` Bronze
  sessions ended on the deadline after a foreground `uvicorn … --reload`, and
  `main.py` appeared outside the layout in two `bare` sessions; the worker did
  neither. An earlier Silver sample (worker 2/3 against 0/3 on an M5 Max) did
  not reproduce.
- **Kept as** the opening of the Hard index, "Who drives".

## H2 The Handoff

[Page at `c5f125a`](https://github.com/andrevanzuydam/mellum-worker/blob/c5f125a/learn/lessons/hard/the-handoff.md).

- **Why it left.** The handoff block (`collapseHandoffs`) ships inside
  `extensions/mellum-worker.ts`, not as a unit, and there is no arm for it:
  the delegated child it answered was retired on 2026-10-20 (LC.8).
- **Evidence.** A rationale, not a finding: protocol text in a child's prompt
  is paid on every request of that child, and again on every request of a
  parent that keeps the transcript. The removal is checkable with
  `git log --oneline --grep="one worker"`.
- **Kept as** the `BACKLOG.md` entry "The handoff block as a unit".

## E4 Running Commands

[Page at `484c829`](https://github.com/andrevanzuydam/mellum-worker/blob/484c829/learn/lessons/easy/running-commands.md).

- **Why it left.** Its lesson check did not hold twice on the 6-bit
  reference model (the revision 2 screen, then revision 3 with clean serving):
  without the guard, the model backgrounded its own server starts and passed.
  Under the plan, a second miss takes a lesson out of the track; Andre chose
  that over reopening the reference model.
- **Evidence.** The foreground stall is real: four of nine bare sessions on
  the BF16 host stalled on a server start, and the guard refused foreground
  starts whenever they came. Its challenge, `learn/challenges/running-commands/`,
  stays and still qualifies; its record is
  `evals/2026-10-29-running-commands-check/`.
- **Kept as** the pathologies entry "A server nobody can stop", and the unit
  `guard/block-foreground-server`, which stays in the remedies list for The
  Challenge.

## What would falsify this

This note claims only that the linked pages said what is summarised here; the
linked commit is the check.

## Risks

A summary drops detail. The linked pages carry the full tables, so read them
before reusing a number.
