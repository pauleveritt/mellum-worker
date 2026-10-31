# A19: Mellum Mode with project facts on, rungs 1–9 (M.7)

**What is measured.** Mellum Mode at commit `aff031a` (the M.7 facts code;
`run.json` records `worker_git` `v0.1.2-40-gaff031a`, prompt v5) with guards
on and project facts on (`--mode-facts on`), on all nine rungs, three repeats
each. What each rung received, checked in every trace (one `Project facts:`
block per request, in every request of the run):

- rungs 6–9 (AgentClinic): the fixture's `## Mellum` section, three bullets
  (`Test command: uv run python -m pytest tests`, the write-only list, the
  do-not line);
- rungs 2–5 (Python, `pyproject.toml` mentions pytest, no `AGENTS.md`): the
  detected fallback, `Test command: uv run --offline python -m pytest -q`;
- rung 1 (Node): nothing.

It answers two comparisons: rungs 1–5 against [A17](../ablation-a17-mode-v012/README.md)
(Mode as shipped, 14/15), and rungs 6–9 against
[A18](../ablation-a18-agentclinic-facts-off/README.md) (facts off, 1/12
rescored, median 50 requests). Rungs 6–9 are scored under spec §2 rule 3 as
changed by Paul ("no existing test is removed or edited; additions are
allowed"), already in the scorer at `aff031a`, so the A18 comparison uses
A18's rescored numbers: same rule on both sides.

Launch, 2026-10-10 08:10 EDT, from `ladder/` at commit `aff031a` (finished
08:56 EDT, 27 rows):

    uv run python -m ladder.run_ladder --mode mode --profile baseline --rung 1 --rung 2 --rung 3 --rung 4 --rung 5 --rung 6 --rung 7 --rung 8 --rung 9 --repeat 3 --deadline 600 --mode-facts on --out ../evals/2026-10-10-ablation-a19-facts-on

oMLX was up; `~/.pi/agent/mellum-mode-runs.jsonl` had 7 lines before and 7
after. An earlier launch (2026-10-09 21:39) was stopped after 4 complete rows
by a pause and moved aside, out of the repo; this record is the full re-run
from scratch.

## Result, rungs 1–5 (against A17)

| rung | A17 passes | A19 passes | A19 requests, median (runs) | A19 wall s, median |
| --- | --- | --- | --- | --- |
| 1 (no facts) | 3/3 | 3/3 | 7 (7, 10, 7) | 9 |
| 2 (fallback) | 3/3 | 3/3 | 10 (16, 10, 10) | 26 |
| 3 (fallback) | 3/3 | 3/3 | 19 (12, 19, 20) | 34 |
| 4 (fallback) | 3/3 | 3/3 | 14 (13, 14, 17) | 54 |
| 5 (fallback) | 2/3 | 3/3 | 16 (16, 16, 20) | 118 |
| all | 14/15 | **15/15** | mean 13.8 (A17 12.9) | mean 51 (A17 44) |

Nudges 4 (A17 3), tool errors 17 (A17 12), from each phase's `run.json`. No
regression in passes. Mean requests, 13.8, are above both A14 (13.1) and A17
(12.9); mean wall, 51 s, falls between A17 (44 s) and A14 (70 s).

## Result, rungs 6–9 (against A18)

| rung | A18 passes, rescored | A19 passes | A19 requests, median (runs) | A18 requests, median | A19 wall s, median (runs) |
| --- | --- | --- | --- | --- | --- |
| 6 (phase 1, home) | 0/3 | 3/3 | 25 (36, 25, 21) | 42 | 70 (108, 70, 61) |
| 7 (phase 2, board) | 1/3 | 3/3 | 25 (25, 27, 20) | 42 | 90 (90, 91, 73) |
| 8 (phase 3, add) | 0/3 | 2/3 | 43 (88, 43, 33) | 57 | 399 (399, 600, 103) |
| 9 (phase 4, resolve and reopen) | 0/3 | 1/3 | 24 (28, 24, 16) | 51 | 116 (123, 116, 116) |
| all | 1/12 | **9/12** | **26** (mean 32) | **50** (mean 54) | |

Wall is the runner's untrusted clock. One run hit the 600 s deadline (rung 8
r2; A18 had three).

## Per run, rungs 6–9

`wp` is `outside_write_list`; `facts` is `facts_cmd_pass`; `hid` is
`hidden_pass`; `kept` is `tests_unchanged` under rule 3.

| run | pass | requests | wp | facts | hid | kept |
| --- | --- | --- | --- | --- | --- | --- |
| 6 r1 | yes | 36 | none | yes | yes | yes |
| 6 r2 | yes | 25 | none | yes | yes | yes |
| 6 r3 | yes | 21 | none | yes | yes | yes |
| 7 r1 | yes | 25 | none | yes | yes | yes |
| 7 r2 | yes | 27 | none | yes | yes | yes |
| 7 r3 | yes | 20 | none | yes | yes | yes |
| 8 r1 | yes | 88 | none | yes | yes | yes |
| 8 r2 | no | 43 | none | no | yes | yes |
| 8 r3 | yes | 33 | none | yes | yes | yes |
| 9 r1 | no | 28 | none | yes | no | yes |
| 9 r2 | no | 24 | none | yes | no | yes |
| 9 r3 | yes | 16 | none | yes | yes | yes |

## What changed against A18

- **The import error is gone.** No tool result in rungs 6–9 contains `No
  module named 'app'` (A18: 11 of 12 runs). The first pytest command of every
  run was the facts command, `uv run python -m pytest tests`, with `-q` or
  `-v` added in some.
- **The write-list holds.** `outside_write_list` is empty in all 12 runs
  (A18: 8 of 12, the `__init__.py`, `pytest.ini`, `pyproject.toml`/`uv.lock`
  fixes for the import error).
- **Test additions.** Four runs added tests to a starting test file without
  removing a line (7 r2, 7 r3, 8 r1, 8 r2, from `diff.patch`); rule 3 accepts
  them. Under A18's strict byte-identical rule, 7 r2, 7 r3 and 8 r1 would
  fail, giving 6/12; that number is read from the diffs, not scored.

## Failure shapes

- **8 r2: its own test was wrong, then a server in the foreground.** It
  appended `test_post_complaint`, which asserts 303 from `client.post` without
  `follow_redirects=False`; the test client follows the redirect and gets 200
  (`assert 200 == 303` in the trace), so the facts command fails. Hidden tests
  passed. It then started a server on port 8000 in the background, and its
  `curl` to `localhost:8000` timed out after 7.8 s; a foreground start on
  8000 failed with `[Errno 48] ... address already in use`. Port 8000 was
  held by A18 6 r2's leftover phase-1 app (see Risks; the process was
  identified by the controller after the phase, not from this trace). It
  moved to a foreground `uv run uvicorn app:app --host 0.0.0.0 --port 8001`,
  which bound, and the trace ends there with no result before the 600 s
  deadline; that this call held the run is inferred from the trace, and
  the server it started was left running.
- **9 r1 and 9 r2: complaint ids.** Both broke the spec's "assigned
  automatically; `Complaint(agent_name, text)` still works". 9 r1 added
  `id: int = None` and set ids only in the POST route, so two new complaints
  share `None` (`assert None != None`) and resolving a seeded complaint gives
  422. 9 r2 made `id` the first positional field, so `Complaint("a", "b")`
  raises `missing 1 required positional argument: 'text'`. Checked by
  rerunning the hidden tests in the retained workspaces after the phase (not
  part of scoring). Each ran the facts command once, saw it pass, and
  stopped; the visible tests do not cover ids.
- **Rung 8's import of `RedirectResponse`.** Every rung-8 run, here as in A18,
  tried `from fastapi import RedirectResponse` at least once (the looser spec
  dropped the import). 8 r1 spent 88 requests and 25 tool errors before
  passing with an `HTTPException(status_code=303)` redirect.

## What is conjecture

That the gain comes from the stated test command rather than the write-only
and do-not bullets. The import error and the write-list entries vanished
together, so this phase cannot separate them;
[A20](../ablation-a20-facts-fallback-only/README.md) (fallback command only)
is the partial answer. That rung 9's id failures are a spec-reading limit and
not a facts effect: they occur in A18, A19 and A20 alike.

## What would falsify this

A repeat of this launch landing at 4/12 or fewer on rungs 6–9 (A18 + 3 is
the ship rule's floor), or with a median at or above 50 requests, would show
9/12 was a lucky draw. A non-empty `outside_write_list` in a repeat would show
the bullets do not reliably hold the write-list.

## Risks

- Three repeats per rung; 9/12 against 1/12 is a large gap, but per-rung
  results (rung 9 at 1/3) are not stable estimates.
- Rungs 2–5 received the fallback command, so rungs 1–5 measure "facts on"
  including the fallback, not Mode with nothing added.
- Runs share the machine's ports, and the runner does not stop leftover
  servers. Every run that hit the 600 s deadline in A18, A19 and A20 (A18 6 r2, 8 r1, 9 r1; A19 8 r2; A20 6 r2) ended on a server
  started in the foreground, and the runner left it running when it cut
  the run, on ports 8000 to 8003 (A19 8 r2's on `*:8001`, the port
  oMLX serves on at 127.0.0.1). A later run that starts a server meets
  them. Scores are not affected (both affected runs fail for their own
  reasons), and the controller stopped those servers on 2026-10-10 about
  09:50 EDT, after the phases.
- Rule 3 changed after A18 ran; A18 is compared through its rescored
  workspaces, not a fresh run under the new rule.

Raw traces, stdout and diffs: [`ablation-a19-facts-on.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/ablation-a19-facts-on.tar.gz)
(sha256 `aca9d936997ef15ffb33e4eea5b71af60d64a5956326b7cedff6121ac5aab895`).
