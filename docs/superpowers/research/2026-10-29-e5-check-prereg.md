# Preregistration: E5's lesson check (Running Commands)

**What is measured.** Nothing yet: arms, n, scoring and rule fixed on
2026-10-29 before any run, at the commit that adds this note.

**What is conjecture.** That the challenge provokes a foreground server on
this host, and that `guard/block-foreground-server` is what lets a session
finish.

## The challenge

`learn/challenges/e5-running-commands/`: build `app.py` with `GET /health`,
make sure it starts and answers, then add `GET /items` and `GET /items/{id}`
(404 for a missing id) with tests. The hidden grader checks all four routes
and behaviours. A session that hangs on a server it started never reaches
step 2 and fails; `harness.py qualify` passes the known-good build and fails
the step-1-only build. The workspace has no `AGENTS.md`, so the project-facts
remedy (M1) cannot tell the model not to start servers.

## Arms

Run with `harness.py run --suites-dir learn/challenges --suite
e5-running-commands --arm bare --repeat 3 --deadline 600 --stall 120` on the
pinned vLLM host (RTX A6000, Mellum 2.1 BF16, vLLM 0.32.0, Pi 1.3.0), no
`--grade` (the lesson is about hanging, not lint):

- **Before:** `--remedy guard/break-repeat-loops,guard/stay-in-workspace,guard/refuse-whole-file-rewrite`
  (everything Easy adds before E5).
- **After:** the same plus `guard/block-foreground-server`.

n = 3 per arm.

## Rule

- **The lesson works** if before passes 0 of 3 and after passes at least 2
  of 3.
- **The pathology is confirmed** on this host if at least 2 of the 3 before
  sessions record a `stalled` server start (`python app.py`, `uvicorn`, …).
- Otherwise the page says what happened, and the challenge or the lesson is
  revised and preregistered again; nothing is tuned between these runs.

## What would falsify this

Before sessions that never start a server (the challenge does not provoke
the failure), or after sessions that fail for a reason the guard does not
touch.

## Risks

n = 3 per arm; one session moves the verdict. The prompt asks the model to
make sure the app starts, which invites a server run, but does not say how;
a model that checks in process passes both arms.
