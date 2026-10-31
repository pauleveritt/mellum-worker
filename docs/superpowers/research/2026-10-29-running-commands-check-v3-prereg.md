# Preregistration: E4 Running Commands' lesson check, revision 3

**What is measured.** Nothing yet: fixed on 2026-10-29 before any run of
revision 3, at the commit that adds this note. It is the first deciding run
under the uniform-lessons contract
([spec](../specs/2026-10-29-uniform-lessons-design.md),
[plan](../plans/2026-10-29-uniform-lessons.md) task 7).

**What is conjecture.** That a task which names its own run command,
`python app.py`, leads the 6-bit model to run it as written, in the
foreground, often enough to fail every session without the guard; and that
`guard/block-foreground-server` turns those sessions into passes.

## Dated correction 2026-10-29, before the deciding run

The rule changes to **one session per arm** (spec correction of the same
date, at Andre's direction): the lesson holds if the before session FAILS and
the after session PASSES. Run as `--repeat 1`.

In full view: the change was made after a first attempt at revision 3
(`runs/E4-check-20261029T205258Z-00d8315`, not recorded) that was **void**
from a harness fault: `lesson-check.sh` fed its run lines on stdin, so the
first before session received the after arm's command as part of its prompt,
ran it, and stalled; the after arm never ran (fixed in `4ef2f6d`). The two
clean before sessions of that attempt both stalled on `python app.py` and
failed. The deciding run is a fresh one under the corrected rule.

## Dated correction 2026-10-29, after the first deciding run

The first deciding run under the one-session rule
(`runs/E4-check-20261029T210343Z-19f8d82`) gave before PASS, after PASS: a
miss. It was then found to be **confounded by serving**: the LAN host
returned every turn after the first with its reasoning as `<think>` text,
which Pi fed back to the model as content
([note](2026-10-29-lan-reasoning-leak.md); 35 of 36 and 10 of 11 turns in
its two sessions). At Andre's direction the check is re-run once, cleanly,
with the think-tag adapter (`ae89931`) loaded in every session; everything
else is as fixed above (one session per arm, same lines, same rule). The
confounded run is recorded as such, not counted. A miss on the clean run
uses up E4's one revision.

**Further correction, same day.** The clean re-run started at `1ff6480`
was stopped part-way and is not counted: the adapter removed the `<think>`
text but left its thinking blocks unlabelled, and Pi drops an unlabelled
block from the next request, so the model got no earlier reasoning at all
(the strip-thinking condition, a different confound). The adapter now labels
the block with the reasoning field, as Pi labels reasoning it streamed; the
check runs once more on that.

## Why a revision 3

- Revisions 1 and 2 on BF16 (vast.ai A6000): 3/3 before, 3/3 after. The model
  checked in process, or backgrounded the server itself
  ([note](2026-10-29-e5-check.md)).
- Revision 2 on the 6-bit LAN host, a screen: before 2/3, after 3/3. One
  before session ran `uvicorn app:app --port 8000` in the foreground and
  stalled; the guard fired in two of three after sessions (1 and 7 blocks).
  Record: `evals/2026-10-29-running-commands-check/revision-2-lan-6bit/`.
- Revision 2's step 2 said "Start the app on port 8000", leaving the how to
  the model. Revision 3 gives the project's own command, as a README would:
  "Run the app with `python app.py`, then check it live". Nothing else in the
  challenge changed; it still qualifies (known-good passes, step-2-only
  fails).

## Arms and running

`scripts/lesson-check.sh E4` on the default profile
(`scripts/baseline/lan-profile/`: Mellum at 6 bits on the LAN vLLM host,
model id `mellum`, 65,536 context, Pi 1.3.0 under `.baseline/`). The two arms
are the E4 page's Run it yourself lines:

- **Before:** `--remedy guard/break-repeat-loops,guard/stay-in-workspace,guard/refuse-whole-file-rewrite`
- **After:** the same plus `guard/block-foreground-server`

Both: `--suites-dir learn/challenges --suite running-commands --repeat 3
--deadline 600 --stall 120`, no `--grade`. Arms run one after the other with
port 8000 checked free; the harness sweeps each run's workspace processes
(`57011a9`).

## Rule

- **The lesson holds** if before passes **0 of 3** and after passes **at
  least 2 of 3**.
- **The pathology is confirmed** if at least 2 of 3 before sessions record a
  `stalled` server start.
- Under the plan, a miss here is E4's one revision used up: a second miss
  takes E4 out of the track. A before arm that passes on the 6-bit also
  triggers the plan's stop condition, reopening the reference model before
  any other challenge is built.

## What would falsify this

Before sessions that background `python app.py` themselves (with `&` or
`nohup`) and pass: then naming the command does not lead this model into the
foreground, and the guard is not what a session needs here.

## Risks

- n = 3 per arm: one session moves the verdict.
- The rule's 0 of 3 is strict on purpose: `/lesson`'s `r` runs one session,
  and a learner must see FAIL.
- The LAN host is shared; the record names the commit, profile and serving
  stack so a later run can be compared.

## Result, 2026-10-29

Run at `8a28b60` (`runs/E4-check-20261029T212000Z-8a28b60`, recorded under
`evals/2026-10-29-running-commands-check/revision-3-lan-6bit/`), with
clean serving confirmed in both traces.

- **Before:** PASS (27 requests, no stall). Every server start was
  backgrounded by the model and killed after its `curl`.
- **After:** PASS (46 requests; the guard refused 2 starts).
- **The lesson does not hold:** the before session passed. The pathology is
  not confirmed on this run.

**What it means under the plan.** This is E4's second miss on the 6-bit
(revision 2's screen, then revision 3), so under the plan E4 leaves the
track, and a before arm that passes on the 6-bit is the plan's stop
condition: the reference-model question reopens before another challenge is
built. Across all clean-enough before sessions on this host (the revision 2
screen and this run), the foreground stall showed in 1 of 4; with the
reasoning confound present (the void and confounded attempts) it showed in
3 of 4, which suggests the leak itself pushed the model toward the trap.
That last reading is a lead, not a result.
