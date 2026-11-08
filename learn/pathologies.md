# Pathologies

The ways a small model goes wrong on an agentic task, each with the record that
shows it and the shape that answers it. Read it as a map of failure, not as a
scoreboard.

![A doctor robot with a stethoscope examining the small robot beside a chart and magnifying glass](assets/illustrations/pathologies.webp){ .illustration }

## How to read this

- **An entry needs an observation behind it.** A run that happened, in this
  repository or, where it says `Seen elsewhere`, in a record we can point at.
  A failure mode somebody reasoned their way to is a hypothesis, not an entry.
- **It is a reference, not a rate, and not a denominator.** Do not count the entries and call it
  a rate. They were collected opportunistically, on different tasks, and the
  count measures what got written down.
- **Some entries are not the model's fault.** A harness or spec fault that reads
  as a model fault belongs here too, marked as such, because from the outside
  the two are indistinguishable until someone checks, and misfiling one is the
  mistake worth remembering.
- **`Answer:` means the shape that answers it, not a proven cure.** Where
  nothing answers it yet, the line says so.

## Pathology and remedy

Each pathology is tied here to the remedy unit that answers it — the `/remedy`
unit you switch on, listed in [Remedies you can try](challenge/remedies.md) — or
marked where there is **no loadable remedy**, because the answer lives in the
harness, the spec or the sampling settings instead. The numbers match the
entries below.

| # | Pathology | Remedy |
| --- | --- | --- |
| 1 | False success | none — the harness runs the command and scores it |
| 2 | Fabricated evidence | none — the harness runs the command after the child exits |
| 3 | A dropped requirement | none as a unit — cumulative grading is a harness guarantee; `workflow/spec-driven-flow`'s per-phase gates come closest |
| 4 | A narrowed test | none — hidden graders run externally after the run |
| 5 | An empty final | `nudge/empty-turn` |
| 6 | A loop | `guard/repeat-loops` (and `guard/turn-cap` for an unbounded budget) |
| 7 | A runaway search | `guard/outside-workspace` |
| 8 | A server nobody can stop | `guard/foreground-server`, or `tool/background-long-commands` to rewrite it to the background |
| 9 | Thinking spends the answer budget | none — an output cap with room for the answer, a sampling-settings fix |
| 10 | An inert gate | none — a harness fix (read the gate's config at settle time) |
| 11 | A stop-cap and a gate deadlock | none — a harness fix (reconcile the cap and the gate) |
| 12 | Writes outside the layout | none yet — a write-confining guard is planned; `guard/outside-workspace` covers searches only |
| 13 | A lost id | none as a unit — the acceptance list carries the contract; `workflow/spec-driven-flow`'s frozen gates come closest |
| 14 | The project stops importing | none as a unit — a seeded test and the test command in the brief give the signal; the harness records `checks_ran` |
| 15 | Builds it somewhere else | none as a unit — the project layout belongs in the spec |
| 16 | A skipped rule | none — a fact is a reminder; the guard enforces (e.g. `guard/foreground-server` for "do not start servers") |
| 17 | Ships without running its own code | under test — `guard/foreground-server` blocks the server-start that passes for a check; a verification lever is being measured ([easy-ladder](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)) |
| 18 | A defective oracle | none — repair assertions with wrong and valid alternative builds |
| 19 | The workspace controls its examiner | none — trusted dependencies/configuration and structured results |
| 20 | The default, not the hook | `check/mediated-test` carries a check for it; it lost on budget in R.1 |
| 21 | Works past the finish | none yet — a check that ends the run at green is open |
| 22 | A check the model's own server breaks | none — a harness fix (the check reports what the app printed) |

## It says it is done and it is not

1. **False success.** The final reply reports a working app and passing tests
   the run never executed, so the operator pays for a result they then have to
   verify themselves. **Seen:** the ditch session, where the model claimed a
   passing run over a project with four errors
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-the-ditch-session.md)). **Answer:** run the command
   yourself; the scoring is the check, not the reply.
2. **Fabricated evidence.** A test run is reported that never happened: the
   output is invented, in the shape a real run would have taken. **Seen:** the
   same ditch session, whose test output was written rather than printed
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-the-ditch-session.md)). **Answer:** the harness runs the
   command after the child exits, so nothing the child says about a test counts.
3. **A dropped requirement.** A later phase is built and an earlier one is
   silently lost, so the project passes the newest checks and fails the oldest.
   **Seen:** `split` session `995575`, which passed every phase-3 and phase-4
   check while missing 3 of 4 phase-1 checks
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson10-run.md)).
   **Answer:** cumulative checks: grade every phase on every run, not just the
   phase that was asked for.
4. **A narrowed test.** The worker changes the test rather than the code: a
   function narrowed to one assertion, a passing `assert True`, a selector
   pointed at the easy case. **Seen:** LC.9's `/mellum` session left three
   passing tests including one `assert True`
   ([row](https://github.com/andrevanzuydam/mellum-worker/blob/main/ROADMAP.md)); Andre's digest records the narrow-to-one-function
   form ([harvest](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-pr-harvest-index.md)).
   **Answer:** hidden graders run externally after the run, and required starter
   tests retain their trusted execution; the mediated-test cycle (LC.21) is the
   fuller remedy.

## It stops before the work is done

5. **An empty final.** A turn ends with no text and no tool call, and the run
   stops there having done nothing, followed by the quiet version, an empty
   final at the very end. **Seen:** ten Easy sessions in which the nudge never
   fired because no empty turn had the shape it answers, the finals ending on a
   context overflow or the output cap instead
   ([lesson](lessons/index.md)). **Answer:** the bounded
   nudge answers a self-ended empty turn; a capped or aborted one is a budget
   question and needs its own fix.
6. **A loop.** The same text or the same call repeats until the budget is gone,
   with no progress between repeats. **Seen:** a smoke run looped about four
   minutes retrying refused command shapes, each a slightly different call
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-26-server-guard-run.md));
   the loop breaker exists and is unmeasured
   ([lesson](lessons/index.md)). **Answer:** a refusal that
   names an alternative, and a loop breaker, which no arm has yet shown earns
   its place.
7. **A runaway search.** Instead of working the task, the model searches (the
   filesystem, the web, its own context) and the turns go into looking rather
   than doing. **Seen elsewhere:** Andre's index, "the runaway search", with no
   reproduction here yet
   ([harvest](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-pr-harvest-index.md)).
   **Answer:** a spec that names the workspace and the files, and a tool set
   that does not invite wandering.
8. **A server nobody can stop.** The model starts `uvicorn` in the foreground to
   check its work, the call never returns, and the session burns its whole
   deadline waiting. **Seen:** three `no-facts` sessions that went silent for
   143–460 s, two of three `bare` Easy sessions, LC.19's first two attempts,
   and, on the local 6-bit MLX host, two of three bare `build-a-harness` sessions
   (2026-10-29 smoke), and two of three easy `acceptance + ncm` reps on local Q4
   that were killed at the 120 s stall on a foreground `python main.py`, before
   the settle gate could ever fire (2026-10-31)
   ([screen](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-24-project-facts-screen.md),
   [run](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson1-run.md),
   [attempts](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson10-run.md),
   [6-bit](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-local-lessons-smoke.md),
   [gate screen](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-31-cap-ncm-deadlock.md)).
   **Answer:** a brief that names the check (`pytest`, `TestClient`) stops it
   at the source; the dormant guard refuses the call when it appears, at the
   cost of retries.

9. **Thinking spends the answer budget.** The model reasons until the output
   cap is gone, and the turn ends with no answer. **Seen:** a one-turn smoke at
   `max_tokens 32` that spent all 32 tokens thinking and returned empty content,
   and suite finals on Easy and Medium ended by `length`
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lessons-left-the-track.md)). **Answer:** an output cap with room for the answer;
   stripping earlier reasoning does not give the turn its budget back.
10. **An inert gate (not the model's fault).** The verify-and-redispatch gate
   that should refuse a premature "done" was switched off the whole session, so
   the worker self-exited with the work incomplete and nothing sent it back — a
   harness fault that reads from the outside as the model stopping early.
   **Seen:** the 2026-10-30 easy remedy screen, where `mellum-verify` read `NCM_TEST`
   at extension-load — before `mellum-acceptance` set it at `session_start` — so
   `[mellum-verify]` fired zero times and a 17-turn session settled with the app
   built as `main.py` and the Phase-1 home checks unmet
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-30-acceptance-gate-inert.md)).
   **Answer:** read the gate's config at settle time, not at load, and run the
   contract with the workspace on `PYTHONPATH`; a smoke run that asserts the gate
   actually redispatches would have caught it.
11. **A stop-cap and a gate deadlock (not the model's fault).** Two remedies own
   opposite halves of the stop/go decision and neither yields: a tool-call cap
   refuses the next call ("budget reached — stop") while a verify gate refuses
   the settle ("tests still fail — keep going"), so the worker can neither act
   nor finish and churns text turns to the deadline. **Seen:** the 2026-10-31
   easy screen, a `turn-cap(120)` + `mellum-verify` rep that ran 296 turns to the
   1800 s wall with `tool_calls` pinned at 120, `agent_settled` zero times, 349
   budget blocks against 193 gate refusals; the one rep where the cap barely bit
   (5 blocks) passed at 125 turns
   ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-31-cap-ncm-deadlock.md)).
   **Answer:** do not run a hard stop-cap and a refuse-to-settle gate together
   without reconciling them — the gate stands down once the budget is exhausted,
   letting the run settle on its real (incomplete) state rather than timing out.

## It damages the project while finishing

12. **Writes outside the layout.** The run passes every hidden test and still
   leaves scratch files, a second copy of the app, or an edited test, so the
   workspace is no longer the project. **Seen:** the file-set check found
   `main.py` outside the layout twice, and `pyproject.toml` once
   ([run](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson1-run.md),
   no lesson yet). **Answer:** name the layout in the task and compare the file
   set after the run; a guard that confines writes is planned.
13. **A lost id.** The last phase's identity contract never lands: the field is
    missing, or it is rebuilt from a position that changes when the list does.
    **Seen:** phase 4's group of checks missing in three of the four sessions
    whose checks ran, in the spec-layout arm
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson10-run.md)).
    **Answer:** write the contract into the acceptance list (unique, stable,
    never reused) and grade the phase rather than the session.
14. **The project stops importing.** A syntax error, or a dataclass that cannot
    construct without an argument the seed code does not pass, leaves a
    workspace nothing can load. **Seen:** three of three sessions of a joined
    brief, and two of six in the spec-layout arm: `ModuleNotFoundError`,
    `SyntaxError: unterminated string`, `Complaint.__init__() missing …
    'timestamp'`
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-27-prose-brief-run.md),
    [record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson10-run.md)).
    **Answer:** the test command in the brief and a seeded test give the signal
    on the first turn; the harness now records `checks_ran: false` so a full
    set of missing checks is not read as a full set of failures.
15. **Builds it somewhere else.** The requirements are met, but in a file the
    project's own notes did not name (the dataclass in `app.py` rather than
    `models.py`) so everything that imports the project fails. **Seen:** three
    joined-brief sessions and one spec-layout session ended without `models.py`,
    and each scored 18 of 18 missing
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-27-prose-brief-run.md),
    [record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson10-run.md)).
    **Answer:** the project layout belongs in the spec, and the checks should
    say they could not run rather than that everything failed.

## It ignores what it was told

16. **A skipped rule.** An instruction is in every request, in the project's own
    words, and the run does the opposite. **Seen:** `Do not: start servers` sat
    in every request and both attempts started one
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-25-lesson10-run.md)), and
    the facts block that carried it moved no pass at n = 3
    ([run](lessons/index.md)). **Answer:** a fact is a reminder, not
    an enforcement; the guard is the enforcement, and it stays dormant until an
    arm needs it.

20. **The default, not the hook.** The spec asks for a default that a later part
    can override, and the run writes the default as a literal, so the default
    passes and the override has nothing to override. **Seen:** all three counted
    Vanilla Easy sessions of the F.5 smoke wrote `<title>AgentClinic</title>` into
    `base.html` with no block, and all three miss
    `test_extending_page_can_override_layout_title`
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-11-07-f5-smoke/table.md)). **Answer:** none yet as a
    unit; a check that renders an extending page and reads its title is a
    candidate for R.1. 2026-11-08: R.1's mediated test carries that check. It
    was the test's most frequent re-dispatch, and 11 of 48 mediated sessions
    still ended without the block
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-11-07-r1-step-three/table.md)).

## It does not stop when it is done

21. **Works past the finish.** The work already passes, and the run keeps going
    until the budget is gone. **Seen:** R.1 step three, where 32 of 48 sessions
    shown an acceptance test ended on the request or token budget though 33 had
    reached 13 of 13 on the hidden grade, and some of those that hit the budget
    were never sent back by the test
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-11-07-r1-step-three/table.md)).
    **Answer:** none yet; a check that ends the run once the test is green is
    the open question.

## It ships a defect it never ran

17. **Ships without running its own code.** The run declares done after an
    ineffective self-check — it starts a foreground server, or only re-reads the
    files, instead of exercising the real route or test — so a genuine defect
    ships even though nothing was fabricated. Unlike false success (1), the model
    is not inventing a result; it is verifying by the wrong means. **Seen:** the
    Easy ladder at n = 6 (4/6) on `vanilla + name-the-layout + python-developer`,
    where rep 2 wrote `def home(request):` (no `Request` annotation, so `GET /`
    returned 422) and "verified" by launching `uvicorn`, which never hits the
    route, and rep 5 had the route right but a different defect and only re-read
    the files before stopping
    ([easy-ladder](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-02-easy-ladder.md)).
    **Answer:** verification — run the real route or test before finishing;
    `guard/foreground-server` removes the server-start that stands in for a check,
    forcing a different verification, and a verify lever is being measured.

## The measuring instrument goes wrong

18. **A defective oracle.** A wrong build passes a weak assertion, or a valid
    alternative fails an unstated restriction. This is an instrument fault.
    **Seen:** F.4's deterministic audit accepted an empty migration view and
    fixture-only report totals, but rejected a valid newest-first board
    ([audit](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-07-suite-oracle-audit.md)).
    **Answer:** pair a failing wrong-build witness with valid alternative builds;
    version the repaired assertions so old and current grades stay distinguishable.
19. **The workspace controls its examiner.** Configuration changes replace or
    deselect hidden tests, while score parsing trusts printed success strings.
    **Seen:** F.4's known-broken Easy build scored 4/4 after a submitted conftest
    replaced test execution with no-ops
    ([audit](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-07-suite-oracle-audit.md)).
    No model run is implied.
    **Answer:** use trusted dependencies and configuration, external hidden tests,
    disposable per-check copies, and structured per-test outcomes.
22. **A check the model's own server breaks (not the model's fault).** A check
    that launches the app collides with a server the model left running, and
    reports the failure without its reason, so the model goes hunting.
    **Seen:** R.1 step three, where Easy's mediated launch check reported an
    empty log when the port was already held; 10 of 48 sessions hit it, and one
    spent its turns finding and killing its own servers
    ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-11-07-r1-step-three/table.md)).
    **Answer:** the check reports what the app printed (fixed); a check of
    behaviour should not depend on the state the model leaves behind.

---

*Provenance: entry 7 comes from Andre's harvest and has no observation here yet;
entries 1, 2 and 4–22 are drawn from this repository's own records, linked on
each line; the strongest are three of three. Collected as runs happened, which is why the list is uneven and why
it is not a rate.*
