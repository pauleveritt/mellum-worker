# LEARNING — the journey, Monday 12 to Saturday 24 October 2026

A report of understanding on the work of Andre van Zuydam and Paul Everitt
in `mellum-worker`, written so Paul can follow how Andre's outcomes were
reached. It explains how the easy and medium suites were cracked and how far
the hard suite got. It covers every change since Monday 12 October, day by
day, with what helped, what hurt and what the records do and do not support.
It follows Paul's method so it can feed `learn/` directly.

The window is 288 commits: 145 by Paul and 123 by Andre (including merges).
"This week" means Monday 19 to Saturday 24 October. The week before is a
prologue (Part II).

---

## How this report follows Paul's method

| Paul's rule (source) | How this report applies it |
|---|---|
| Every step carries an evidence badge ([evidence.md](learn/about/evidence.md)) | Every claim is tagged `reference-run`, `cited`, `screen` or `conjecture`. **No record** marks a screen known only from a commit message or LESSONS.md. |
| Screens find a lead; preregistered runs decide ([sdd.md](docs/sdd.md)) | Nothing from this week is promoted. Every result Andre produced from 22 to 24 Oct is a `screen`, and Part VIII lists the preregistered run each one owes. |
| Research notes say what is measured and what is conjecture, and end with what would falsify the claim | Each crack in Part I ends with an Interpretation that names its weakest badge and the run that would upgrade it. |
| A lesson has six steps: Problem, Eval case, Evidence of the problem, Solution (with code), Validation, Interpretation ([lesson-template.md](learn/lesson-template.md)) | Part I writes up easy, medium and hard in exactly those six steps, so each can become a lesson. |
| Compare inside a suite, never across suites. A missing metric is `—`, never `0` | The before/after tables follow this. |
| Before blaming the model, reconstruct its task, files, tool replies and environment, and check the scoring can tell the arms apart | This is the main finding (Part I and §IV.2): most failures were the harness. |
| Measure what ships; a setting the product does not share is a harness finding | Flow is a harness, not the shipped worker. Its results are harness findings, labelled as such. |
| Pathology → remedy (the ditch, the LC.7A Pathologies page) | Part IV is the pathology → remedy ledger, ready for `learn/pathologies.md`. |
| Reversals are recorded beside the original, dated | Part V lists every reversal and re-attribution. |

---

## Part I — How easy, medium and (most of) hard were cracked

### The scoreboard

| Suite (hidden grader tests) | Baseline Pi | Baseline Worker | Harness on, hidden tests passed | Flow + examiner, hidden |
|---|---|---|---|---|
| easy (4) | 0/3 sessions | 1/3 | 4/4 (stamped FAIL by a grading bug) | PASS |
| medium (18) | 0/3 | 2/3 | 12/18 | PASS |
| hard (34) | 0/3 | 0/3 | 21/34 | **29/34**; all 7 phases pass their own gates |
| Badge | `screen` (LC.11A, n=3) | `screen` (LC.11A, n=3) | `screen` n=1; arm config not recorded (LESSONS 22 Oct, `eeeae57`) | `screen` n=1 (`48010bc`; [24 Oct note](docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md)) |

The columns use different units, so read down a column, not across.
Sessions passed is not the same unit as hidden tests passed. This follows
Paul's rule to compare inside a suite.

### The one fact that explains all three suites

The suite bases ship **no visible tests**. Look at `base/` in
`learn/code/suites/*`: there is only `AGENTS.md`, `specs/` and
`pyproject.toml`. The roadmap's `Tests:` lines ask the worker to *write*
them. So in every suite the worker writes its own exam and grades itself
on it. The hidden grader is the only external check.

That is rung 6's problem (AgentClinic phase 1 ships no test). Both Mellum
and Flint fail rung 6 in direct mode. Flint is the second LLM Andre ran
against Mellum; both score 11/12 on rungs 1–12, `screen`, no record.

Every crack below is one of three moves:

1. **Fix the check.** The harness was scoring a correct app as wrong.
2. **Instil the habit.** Prompt lines that stop the worker grading itself
   on a subset.
3. **Supply an external target.** An examiner writes the acceptance test
   from the spec before any code exists. The test is frozen so the coder
   cannot weaken it, and it accumulates across phases.

---

### I.1 Easy — "it was already passing; the check was wrong"

#### Problem
**Badge:** `screen`

Baseline Pi fails easy 0/3 in about 22 s per session. The Baseline Worker
passes 1/3. Easy is one prompt: "Implement Phase 1 — Home Page". It needs a
shared Jinja2 layout, an HTML5 `lang="en"` page, a viewport, Bootstrap, a
navbar and an exact tagline.

#### Eval case
**Badge:** `cited`

`uv run learn/code/harness.py run --suite easy --grade`. The hidden grader
`learn/code/suites/easy/grader/test_phase1_home.py` has 4 tests (doctype,
`lang`, 200 + tagline, nav links), plus the static gate in `grade()`.

#### Evidence of the problem
**Badge:** `screen`

LC.11A, n=3 per arm, llama.cpp:

| Arm | easy passes |
|---|---|
| Baseline Pi | 0/3 |
| Baseline Worker | 1/3 |
| no-prompt | 1/3 |
| no-nudge | 3/3 |
| no-loop | 2/3 |

On 22 Oct Andre's harness-on run passed **all 4 hidden tests and was still
stamped FAIL**.

#### Solution
**Badge:** `cited` (commits with fail-first tests)

The failure was in the grader, not the worker. There were two bugs, fixed
on Thursday 22 Oct:

- `5004187`: `harness.py` defined `grade()` twice. Python binds the second
  definition, so a strict all-rules ruff copy shadowed the intended
  `F,E9` gate. That failed working code on style nits (RUF100, I001).
- `af3b8b9`: ruff's `--exclude` *replaces* its default excludes, so
  `.venv` was linted. The worker runs `uv`, which creates a `.venv`, so
  every working solution failed on F403 inside PyYAML.

##### The code
```python
# learn/code/harness.py: grade() lints only the worker's code
["ruff", "check", "--select", "F,E9", "--extend-exclude", "tests,grader_tests", ...]
```

Two habit remedies also apply to easy: the worker prompt v8 to v11 (run
the whole file, the spec is the contract, self-check before finishing) and
the suite fact `Do not: start servers`.

#### Validation
**Badge:** `screen`

- After the grade fixes, harness-on easy passes the hidden grader and the
  gate (n=1).
- Flow passes easy, visible and hidden (`48010bc`, n unstated).
- Regression tests: `grade()` tolerates a style-only issue; `harness.py`
  has no shadowed top-level definitions; a `.venv` with a star-import does
  not fail the suite. All three were shown to fail first.

| Suite | Arm | Passes | Hidden tests | Source |
|---|---|---|---|---|
| easy | Baseline Worker (LC.11A) | 1/3 | — | `screen` |
| easy | harness on, before grade fix | stamped FAIL | 4/4 | `screen` n=1 |
| easy | harness on, after grade fix | PASS | 4/4 | `screen` n=1 |
| easy | flow | PASS | 4/4 | `screen` n unstated |

#### Interpretation

The weakest badge is `screen` (n=1). Easy was cracked mostly by fixing the
measurement.

**Implication for Paul:** the LC.11A easy numbers came from the harness
*before* these fixes. Some Baseline Worker and no-* "fails" on easy may be
grading artefacts. Before LC.11A's easy row is taught, re-grade the
retained LC.11A workspaces with the fixed `grade()` (a cheap check, no
model time), or rerun.

---

### I.2 Medium — "the habit, then an examiner that asserts identity and redirects"

#### Problem
**Badge:** `screen`

Medium is four prompts (phases 1–4: home, board, add, resolve/reopen). The
wall is phase 4. The spec says verbatim to add a stable `id: int` with an
automatic, unique, never-reused default. The worker resolves and reopens
by *list index* instead. That is the same id miss as ladder rung 9, and
the A21 failure.

#### Eval case
**Badge:** `cited`

`--suite medium`. The hidden grader has 18 tests across
`test_phase1_home`, `test_phase2_board`, `test_phase3_add` and
`test_phase4_resolve_reopen`.

#### Evidence of the problem
**Badge:** `screen`

- LC.11A: Baseline Pi 0/3, Baseline Worker 2/3.
- Harness on: 12/18 hidden tests (n=1).
- A flow run went visible PASS / hidden FAIL because `Complaint` had no id
  field (`15c2766`, n=1).
- A later flow run looped to exhaustion on phase 3 (Add Complaint) against
  a gate no app could pass (`b4639c9`).

#### Solution
**Badge:** `screen`

Three layers, in the order they landed:

1. **Habit (prompt)**, Wed 21 Oct. v9: "The spec is the full contract.
   Implement EVERY requirement… unique ids that are never reused… even
   when no visible test checks it." v11: "Before you finish, re-read the
   spec… check your code against EACH clause." Answers *self-narrowing on
   the spec*.
2. **Control outside the model**, Thu 22 – Fri 23 Oct. `mellum-flow`:
   - plan → review_plan → examine → code → review_code → test, each phase
     an isolated Pi sub-agent;
   - only the coder writes;
   - the examiner writes the acceptance test from the spec;
   - the gate is frozen in `plan/gate/phase_<n>.py` and restored before
     scoring.
3. **Examiner rules** that close medium's two gaps:
   - Fri 23 Oct `15c2766`, *identity*: a phase that acts on a specific
     record must assert a stable explicit id field, distinct per record,
     addressed by id, unchanged across mutation.
   - Sat 24 Oct `b4639c9`, then `a1898ae`, *redirects*: TestClient
     follows redirects by default, so a correct 303 handler showed 200.
     The fix is to build the client once with `follow_redirects=False`.

##### The code
```text
# examiner rule (mellum-flow.ts, paraphrased)
For any phase that resolves/reopens/updates/deletes/fetches a record: assert a stable
explicit id FIELD on the model — distinct per record, the route addressed by id, the
id unchanged across the mutation. Build the client as TestClient(app, follow_redirects=False).
```

#### Validation
**Badge:** `screen`

| Suite | Arm | Passes | Hidden tests | Source |
|---|---|---|---|---|
| medium | Baseline Pi | 0/3 | — | LC.11A |
| medium | Baseline Worker | 2/3 | — | LC.11A |
| medium | harness on | — | 12/18 | `eeeae57`, n=1 |
| medium | flow, before identity rule | visible PASS, hidden FAIL | — | `15c2766`, n=1 |
| medium | flow | PASS | 18/18 | `48010bc`, n unstated |

The phase-4 gate against the known-correct app went from 2 failures to
7/7 once the client-level redirect rule was in (`a1898ae`).

#### Interpretation

The weakest badge is `screen`: no n=3 flow run on medium, and the
"medium PASS" in `48010bc` predates the identity and redirect rules.

What cracked medium is the combination of v9/v11 (tell it and make it
check) and an external, frozen, identity-asserting gate. Which part is
load-bearing is not separated. That needs an ablation: flow with and
without the identity rule, n=3.

---

### I.3 Hard — "all seven phases built; the gate is weaker than the oracle"

#### Problem
**Badge:** `screen`

Hard is 11 prompts: seven phases plus sqlite-utils migrations over one
growing app, with an archive & audit phase, a `/tickets` report and a
`/visits` report. Under the earlier harness Paul expected it to stay above
the ceiling, and it did: 0/9 in every LC.11A arm.

#### Eval case
**Badge:** `cited`

`--suite hard`. The hidden grader has 34 tests across phases 1–6,
`test_visits` and `test_migrations`.

#### Evidence of the problem
**Badge:** `screen`

- LC.11A: 0/3 Baseline Pi, 0/3 Baseline Worker.
- Harness on: 21/34 (n=1).
- In-session gates (plan-before-edit plus surgical) took hard to **0**
  (n=1).
- Early flow reached phase 4/7 and then appeared to stall.

#### Solution
**Badge:** `screen`

The harness remedies, in the order they were needed:

| # | Day | Blocker | Remedy | Commit |
|---|---|---|---|---|
| 1 | Thu 22 | A weak model waits out a gate inside its own session | Move control outside the model: an outer loop, then phases as tools | `cc758d1`, `48010bc` |
| 2 | Thu 22 | Hard's spec is a 5.5k-character wall that drowns the model | Multi-level decomposition, plus a north star, running summary and last-phase context | `3d44ee1` |
| 3 | Fri 23 | The "stall": oMLX's parser silently drops tool calls with large JSON arguments | Argument-free phase tools; content goes through `TASK.md`, `TODO.md`, `REVIEW.md` | `3bf2bb8` |
| 4 | Fri 23 | One attempt per phase is a coin flip | Best-of-N with a temperature spread (0.3–1.2); promote the first pass | `3bf2bb8` |
| 5 | Fri 23 | Worker grades itself: visible 7/7, hidden 3/7 | **Examiner**: an independent spec-only acceptance test before coding, frozen | `ae85226` |
| 6 | Fri 23 | A later phase silently breaks an earlier one | Gates **accumulate**; every earlier gate is re-run | `fad46bb` |
| 7 | Fri 23 | Phases 3–7 "passed" with no gate (best-of-N chose the empty fork) | A phase passes only with a real, compiling phase-N gate | `433157e` |
| 8 | Fri 23 | Thrash: examine 5×, review 3×, never test | examine once per phase; 16-call cap | `632477d` |
| 9 | Fri 23 | Planner empty with Pi's base prompt removed | Revert to `--append-system-prompt`; max_tokens 8,192 | `48ed09e`, `b43d932` |
| 10 | Fri 23 | Plan↔review infinite loop | Reviews fail open | `ccc049f` |
| 11 | Sat 24 | Examiner gates no correct app could pass (redirects, lone fences, `"Resolve" not in html` while requiring "Resolved") | Client-level `follow_redirects=False`; strip fences; target the control | `a1898ae`, `6087b95`, `fadbb60` |
| 12 | Sat 24 | Correct build failed on the coder's own scratch tests | Judge on the frozen gate only | `fadbb60` |
| 13 | Sat 24 | Examiner emits nothing (thinking eats 16,384 tokens; then over-reasons a long prompt) | max_tokens 32,000; compress the prompt ~4,650 → ~2,560 characters | `da0b783`, `2196c75` |

##### The code
```text
# flow_run.py — a phase passes only on its own frozen gate
phase_gate_ok(n): plan/gate/phase_<n>.py exists, compile()s, defines ≥1 test
restore_gate():  copy every phase_1..n gate into tests/test_gate_phase_*.py, then pytest them
```

#### Validation
**Badge:** `screen` (n=1)

| Suite | Arm | Phases passing own gate | Hidden tests | Source |
|---|---|---|---|---|
| hard | Baseline Worker | — | 0/3 sessions | LC.11A |
| hard | harness on | — | 21/34 | `eeeae57` |
| hard | in-session gates | — | 0 | `c71068a` |
| hard | flow, pre-examiner | 7/7 | 3/7 phases | LESSONS 23 Oct |
| hard | flow + examiner (Sat 24) | **7/7** | **29/34** | [24 Oct note](docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md) |

All 5 remaining failures are in phases 6–7:

- `/tickets` sums are wrong, and "archived" is derived from status
  instead of `archived_at IS NOT NULL`.
- `/visits` returns an empty list.
- The migrations are not all recorded.

Phases 1–5 pass the hidden grader and were spot-checked by hand.

#### Interpretation

The weakest badge is `screen` (n=1, oMLX, concurrency 1). Hard is
**not cracked**. What is shown is that the model can build all seven
phases when the harness supplies decomposition, an external frozen
target and bounded sequencing. The 29/34 is the **hidden-oracle gap**:
the examiner's phase-6 and phase-7 gates accept an app the hidden grader
rejects.

Two rules landed after the run and were **not re-run**:

- `5ad7c03`: computed endpoints are asserted with an included *and* an
  excluded row; migrations must be recorded.
- `6d88065`: self-contained tests, reuse of earlier gates' conventions,
  deltas instead of totals.

**Validity caution for Paul:** Andre tuned the examiner against hard while
the hidden-grader failures were visible to him. The `archived_at` miss became the
general rule "a definition keyed off a specific column". No suite names
leak (scrubbed in `2378022`), but the dev set and the test set are the
same.

To upgrade:

1. A full hard re-run.
2. A preregistered `--mode flow` run on rungs 6–12, n=3.
3. A **held-out** suite the examiner was never tuned on.

---

## Part II — Prologue: the week of Monday 12 October

### Monday 12 — `/mellum last` and v0.1.7 (Paul)

- `/mellum last` shows the newest run record as a Markdown table with no
  model call. It replaced a slow "analyse my last run" prompt.
  Spec: `2026-10-12-mellum-last-design.md`, explicitly not a measured
  change.
- Review fixes: cells survive backslash-pipes, records are ordered by
  time.
- Release **v0.1.7**.

### Tuesday 13 — A21 decides; the roadmap is triaged (Paul)

- **A21, preregistered.** The lighter `## Mellum` section plus a one-file
  roadmap scored **9/12**; the control also scored **9/12**. There were
  0 outside writes. All four rung-9 failures were the same phase-4 id
  miss, and **every failing run passed its own test command**. The
  lighter section ships in **v0.1.8** (`cited`).
- **Rung-9 screen**, one change at a time, n=3: 1/3 and 1/3. Id misses
  were 5/6 with the one-file roadmap vs 1/6 with phase files. A lead,
  parked behind M.11 (`screen`).
- **Fix:** the ladder stops processes a run leaves behind and records
  them. **Fix:** back-to-back `/mellum` one-shots no longer record an
  empty task.
- **Roadmap triage:** instrument-only phases were retired, and rejected
  research code was removed (chunked and brief modes, strip-thinking,
  budget-hook, nine wording-ratchet tests). "No more instrument-only
  phases."

### Sunday 18 — "don't trust self-exit" (Andre; PRs #1 and #2)

- **mlx-lm backend**, `--model-id`, sampling overrides.
- **Worker-exit lead**, recorded in AGENTS.md and skill §6. A self-exit is
  safe only when the oracle is external, complete and unweakenable.
  Verify by re-running the test, never by the worker's final message.
- **Exit-gate probes** (n=1, by hand): a one-shot misses the id; a frozen
  test plus re-dispatch converges at turn 25. "The oracle is necessary,
  not sufficient. The gate is load-bearing."
- **The mediated path in the ladder:** `--acceptance-test`,
  `--redispatch`, temperature and seed ramp, `--effort-ramp`, re-dispatch
  on timeout, the real failure in the retry message.
- **Mediated rung-9 screen:** stock FAIL at the 600 s deadline; mediated
  **PASS** in 194 s (n=1, `screen`).
- **Preregistered mediated-vs-stock run, rungs 6–9:** the stock arm scored
  **5/12** (deadline hits on a slow backend). Arm B **was never run**:
  there is no oMLX on Andre's machine.
- **Harness bugs:** an acceptance test named `acc_p4.py` was never
  collected; the worker blocked on `python app.py`; greedy retries
  repeated the same decode; a temperature ramp to 1.0 thrashed a working
  app (capped at 0.5).
- **Process:** mellum-dev skill, 🍓 marker, CI for both suites, coding
  principles, "run tests visibly".

---

## Part III — This week, day by day

### Monday 19 October — "small models write tool calls as text"

- **`content-tool-call-assist`** (Andre). Promotes JSON or Hermes-XML text
  into real tool calls, gated on real tool names, for tiny models (Gemma
  E2B, Qwen 1.5B). Comes with the `patch-pi.sh` installer.
- **Tool-presentation experiment** (Gemma E2B, rungs 1–5, n=15):
  baseline **5/15**, stripped native tool field **0/15**. Reverted. The
  native tool block also renders tool results, so the ugly native format
  is load-bearing. Paul called it "the cleanest experiment" (`screen`).
- **Prompt v6:** "Keep every existing test… add alongside." The commit
  itself says "no measured lift, no regression".
- **LESSONS.md** opens with 100 lessons. Skill §10: one small PR per win
  or learning.

### Tuesday 20 October — "rung 9 falls; one Pi worker; the Learning Center is built"

**Andre: v7 and the mediated stack.**
- Prompt **v7** turns the worker into "make one failing test pass". It
  reads the test and its spec, creates the imported module, runs only the
  named test, never edits it and starts no servers.
- **Mediated 6–9: 12/12**, with rung 9 at **3/3** (`cited`). "A method
  stack, not an ablation."
- **v7 ablation, rung 9, n=3 per arm:**

  | Arm | Pass | Average wall |
  |---|---|---|
  | v6 prompt | 3/3 | 701 s |
  | whole-dir test command | 3/3 | **3,075 s** |
  | grep/find restored | 3/3 | 348 s |
  | fixed high budget | 3/3 | **163 s** |
  | (v7 win, reference) | 3/3 | 272 s |

  **The lever is the frozen test plus budget.** Prompt and tools are cost
  knobs (`cited`).
- Tooling: `watch_ladder.py` (live trace follower), `compare_runs.py`.

**Paul: LC.1 to LC.11, the Learning Center, in one day.**
- LC.1: the site skeleton. LC.2: base Pi on **llama.cpp**, with
  `scripts/backend.py` replacing a Justfile made the same morning.
- LC.3: mini harness. LC.3A: suites and grading. LC.3B: the ladder takes
  a backend.
- **LC.3C, the preregistered llama.cpp reference run:** **14/15** on rungs
  1–5. Rung 4 repeat 3 stopped on `length` (`reference-run`; raw tarball
  still owed).
- LC.4: findings digest, ten lessons. LC.6: sessions and `--repeat`.
- **LC.7, the ditch:** a fabricated `Ran 4 tests… OK` over a real
  `FAILED (errors=4)`, and a dropped date filter (n=1). This is the
  pathology catalogue's origin.
- **LC.8 / LC.8A, one worker:** Mellum Mode became Mellum Worker; the
  pi-subagents Worker, intercom, delegated mode and OpenCode were removed.
- LC.9: worker-extension lesson. LC.10 and LC.11: two `cited` findings
  lessons.

### Wednesday 21 October — "self-narrowing, two forms; gates don't add capability"

**Mode and the frozen test.**
- Shipped Mode with v7 on rung 9 scored **0/3**: v7 looks for a failing
  test that Mode never places.
- `--acceptance-test` in Mode plus `mellum-ncm` scored **3/3**, with NCM
  firing **0 times**. Credit goes to the test by name, not to
  "mediation" (`cited`).

**Gates and model size.**
- `mellum-ncm` (Andre): a next-concept verify gate that re-runs the test
  at settle and names the failing concepts.
- **3-bit halving: 3/8** (`cited`, a negative result). Quantization damage
  shows up as lost edit precision.
- **NCM × size:** 6-bit 3/3 with 0 fires; 3-bit and 1.5B fail, the 3-bit
  with "dozens" of fires. **"The gate makes a worker try, not able"**
  (`cited`; arms confounded, Mode vs direct).

**Rungs 10–12.** Phase 5 (Archive & Audit), phase 6 (reporting over a
database) and phase 7 (summing columns of a context-overflowing file):
**9/9** mediated, 7 of 9 runs re-dispatched (`cited`).

**Observability, then a burst of extensions (52 minutes, 11:29–12:21).**
- Feed, replay, control and the dashboard.
- `mellum-context` (FTS5 retrieval), `mellum-rethink` (push back on false
  human claims), `mellum-files` (PDF, Word, Excel), `mellum-vision` (local
  VLM), `mellum-override` (live prompt edits).
- All unit-tested, none ladder-measured (`conjecture`). Logged as
  THEORIES T1–T6.

**The prompt sequence, v8 to v11, 14:11 to 16:23.**
- Watching bare rungs 4 and 5 live through `mellum-override` showed
  **self-narrowing**: the worker narrows pytest to one `::test_fn`,
  passes it, and stops.
  - **v8**: run the whole file, pass every test. Bare ladder 6/12 → 11/12
    claimed.
- Rung 9 still left `id=0`.
  - **v9**: "the spec is the full contract".
- The remaining failure was a foreground `uvicorn` blocking until the
  deadline.
  - **v10**: never start a server, plus the **foreground-server guard**.
- A 1-in-3 slip remained.
  - **v11**: re-read the spec clause by clause. Rung 9 **3/3 un-mediated**.
- All `screen`, **no record**.

**Paul** built the AgentClinic easy, medium and hard suites:

- known-good and known-broken qualification;
- a canary marking any session that touched the grader as contaminated;
- runs moved out of the repo;
- hard rebuilt to seven phases with sqlite-utils migrations;
- harness arms and evidence tables.

He also digested Andre's PRs #3 and #4. He marked v8–v11 and the 12/12
`screen` until reproduced on `main`, and the new extensions `conjecture`.

### Thursday 22 October — "in-session gates regress; control moves outside"

**Paul: LC.11A, the 45-session screen.**

| Arm | easy | medium | hard |
|---|---|---|---|
| Baseline Pi | 0/3 | 0/3 | 0/3 |
| Baseline Worker | 1/3 | 2/3 | 0/3 |
| no-prompt | 1/3 | 2/3 | 0/3 |
| no-nudge | 3/3 | 2/3 | 0/3 |
| no-loop | 2/3 | 1/3 | 0/3 |

- Prompt: null. Loop breaker: null. Nudge: possibly harmful (a lead).
  Hard: no headroom.
- **Basic Remedies dropped**; the bundle became the **Baseline Worker**.
- The glossary is made automatic.

**Andre, morning: fix the check.**
- Andre's merge of `upstream/main` (`0367d04`) brought in Paul's work, but
  every file both had changed was resolved to Paul's side. That **discarded
  Andre's ladder runner changes**: `--acceptance-test`, `--redispatch`,
  `--effort-ramp`, `--pi-extension`, `--model-id`, `--temperature` and
  `--backend mlx-lm`, with their tests. It also discarded his 18–21 Oct
  changelog entries, the AGENTS.md run standard, three README sections, two
  backlog entries and `runs/` in `.gitignore`. Nothing is lost from history
  (`da04888` holds it all), but `main` has lacked it since (§VII.1).
- The shadowed `grade()` and `.venv` lint fixes cracked easy (I.1).
- LESSONS: "the harness as a habit formula, and its ceiling". Baseline
  for the suites: bare 0/3; harness on 4/4, 12/18, 21/34 hidden tests.

**Andre, afternoon: gates inside the session.**
- `mellum-quality` (ruff `F,E9` at finish), `mellum-plan`
  (plan-before-edit), `mellum-surgical` (anti-clobber), `mellum-contract`
  (route test derived from the spec).
- Wired together, these **regressed easy from 4/4 to 0 and hard from 21/34
  to 0**. The plan gate deadlocked: 3,790 blocks, 0 edits. It was made
  fail-open and re-keyed on TODO.md.

**Andre, evening: control outside the model.**
- `mellum-loop` (outer state machine with plan and code review), then
  **`mellum-flow`** (phases as tools, isolated sub-agents) plus
  `mellum-nonblock`. **Easy and medium pass**, visible and hidden.
- Multi-level decomposition with a north star.
- `mellum-knowledge`: a BM25 lookup over the installed venv.

### Friday 23 October — "the examiner: an external definition of done"

- **The stall**, a serving-format bug: argument-free tools, plus best-of-N.
- **Throughput:** 127 → 351 tok/s at N=1→16. A dependent chain gains
  nothing.
- **Examine phase** (`ae85226`) and **accumulating gates** (`fad46bb`).
- **Real gate required** (`433157e`). This exposed the morning's "7/7
  visible": phases 3–7 had passed with no gate. **LESSONS.md carries no
  dated correction for this.**
- `confineToWorkspace` guard, after a worker ran `grep -rl` over `/Users`.
- **`--mode flow` in the ladder:** flow is scored by the rung's own
  hidden grader. Rung 6 goes FAIL → **PASS**.
- **Flint vs Mellum** direct: both 11/12, both fail only rung 6
  (`screen`, no record).
- Thrash control: examine once, 16-call cap. Identity rule (cracks medium,
  I.2).
- **The replace/append reversal:** replacing Pi's base prompt left the
  planner empty, so it was reverted. Pi's base prompt is what makes this
  model emit a final answer.
- Reviews fail open, ending the plan↔review loop.

### Saturday 24 October — "first full hard build; the hidden-oracle gap"

- **Nine examiner fixes**, each a gate no correct app could pass:
  - redirects;
  - lone fences;
  - substring absence;
  - scratch tests;
  - token budget;
  - prompt compression;
  - client-level redirects;
  - shared-state deltas;
  - completeness rules.
- **Hard: 7/7 phases visible, hidden 29/34** (I.3).
- Research note: the [hidden-oracle gap](docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md).
- Andre added the Introduction and Terminology pages; terminology was then
  moved into the glossary.
- Windows and Linux install scripts, troubleshooting, backend version
  fixes.
- Merge of Paul's main (`f50ee9f`): CRLF converted back to LF so
  `backend.py`'s shebang works. `npm test` 492 pass, 1 fail; the
  `backend-lifecycle` kill test also fails on upstream.

---

## Part IV — Pathology → remedy ledger

This is ready material for LC.7A (`learn/pathologies.md`).

### IV.1 Worker pathologies

| # | Pathology | Shown by | Remedy (artifact) | Badge |
|---|---|---|---|---|
| P1 | False success, fabricated evidence | ditch (LC.7) | Re-run the test yourself; an external frozen acceptance test | `screen` |
| P2 | Dropped requirement: the automatic id | A21 rung 9; medium phase 4 | Frozen test (`--acceptance-test`); v9; v11; examiner identity rule | `cited` (12/12) / `screen` |
| P3 | Self-narrowing on the tests (`::test_fn`) | bare rungs 4–5 | Prompt v8 | `screen`, no record |
| P4 | Self-narrowing on the spec | rung 9 under v8 | v9 + v11 | `screen`, no record |
| P5 | Foreground server blocks to the deadline | rung 9, 18 Oct screen | v10; foreground-server guard; `mellum-nonblock`; `Do not: start servers` | `screen` |
| P6 | Test-command thrash, bent project | A18–A20 | `## Mellum` facts | `cited` |
| P7 | Weakened or deleted tests | rung 2 under v5 | v6, v7 "never edit the named test"; frozen gates | `screen` |
| P8 | Tool calls written as text | Gemma E2B, Qwen 1.5B | `content-tool-call-assist` | `screen` |
| P9 | Whole-file clobber (942 → 2) | LESSONS | `mellum-surgical` | `conjecture` (0 clobbers in 82 traced edits) |
| P10 | Machine-wide crawl | 23 Oct flow run | `confineToWorkspace` | `conjecture` |
| P11 | Real Python errors left behind (F811) | the shadowed `grade()` | `mellum-quality` | `conjecture` |
| P12 | No target (no visible test) | rung 6; all three suites | Flow examiner | `screen` |
| P13 | Grades itself on a weak gate | hard visible 7/7 vs hidden 3/7 | Examiner plus accumulating gates; completeness rules | `screen` |
| P14 | Orchestration thrash | rung 6 flow | Examine once; call cap | `conjecture` |
| P15 | Output cap truncates a thinking model | rungs 4–5 at 4,096; plan at 2,048; examiner at 16,384 | `max_tokens` must cover thinking plus output | `screen` |
| P16 | Over-reasoning on a long prompt | examiner at 32,000 | Keep the prompt lean (compression) | `screen` |
| P17 | An incapable model under a gate loops | 3-bit, 1.5B | None; add capability, not gates | `cited` |
| P18 | A weak model waits out an in-session gate | plan gate: 3,790 blocks | Control outside the model (loop, flow) | `screen` |

### IV.2 Harness pathologies ("suspect the check first")

| Defect | What it did | Fix |
|---|---|---|
| Shadowed `grade()`; ruff linting `.venv` | Failed a 4/4 hidden easy pass | `5004187`, `af3b8b9` |
| `run_suite` never copied `base/` | Suites ran in an empty workspace | `aa81d44` (caught by a smoke) |
| Recorder loaded before the worker | **Every arm ran as base Pi** | `5331417` (caught before the screen) |
| Acceptance test named `acc_p4.py` | Never collected | `ff17d60` |
| Greedy re-dispatch | Same decode each time | Seed and temperature ramp (capped at 0.5) |
| Retry message | Warning noise, no assert | `98f9d86` |
| oMLX drops large tool arguments | "Stall" | Argument-free tools (`3bf2bb8`) |
| Pass without a gate; best-of-N selected it | False phase passes | `433157e` |
| Write-list counted harness files | Correct app FAILed | bookkeeping under `plan/` |
| Gate follows redirects | Correct 303 FAILed | `a1898ae` |
| Substring absence check | No app could pass | `fadbb60` |
| Lone markdown fence | Gate would not compile | `6087b95` |
| Invented exact strings | Even the home page failed | `7954d85` |
| Scored on scratch tests | Gate-passing build FAILed | `fadbb60` |
| Fail-closed review | Infinite loop | `ccc049f` |
| Unread stderr pipe | Child hung for the whole timeout | drain stderr |
| `killpg` on a recycled pid | Best-of-N crash | `74efb7d` (`run_orient` still unguarded, `flow_run.py:162,166`) |

---

## Part V — Extensions and prompt changes, chronologically

### V.1 Extensions

| Added | Extension | Why (from the commit) | Badge | Lines |
|---|---|---|---|---|
| Mon 12, Paul | `mellum-last` | Model-free run table | not a measured change | 168 |
| Mon 19, Andre | `content-tool-call-assist` | Tiny models write tool calls as text | `screen` | 450 (**no tests**) |
| Tue 20, Paul | `mellum-worker` (renamed from mode) | One vehicle; nothing Mellum receives changes | `cited` | 620 |
| Wed 21 02:07 | `mellum-ncm` | Verify and re-dispatch inside any Pi session | `cited`: 0 fires | 95 |
| Wed 21 11:29 | `mellum-feed`, `-replay`, `-control`, dashboard | Watch and steer a live worker | `conjecture` | 113 / 90 / 51 |
| Wed 21 12:01 | `mellum-context` | Retrieve, don't load, large files | `conjecture` (T1–T4) | 229 |
| Wed 21 12:06 | `mellum-rethink` | "The human can be wrong, or lying" | `conjecture` (T5) | 179 |
| Wed 21 12:10 | `mellum-files` | Read PDF, Word, Excel | `conjecture` (T6) | 257 |
| Wed 21 12:16 | `mellum-vision` | A local VLM for screenshots | `conjecture` (T6) | 142 |
| Wed 21 12:21 | `mellum-override` | Live prompt edits; **found v8** | `conjecture` | 91 |
| Wed 21 15:37 | foreground-server guard | Rung 9's blocking `uvicorn` | `screen` (with v11) | in guards |
| Thu 22 16:29 | `mellum-quality` | Real errors at finish (F811) | `conjecture` | 165 |
| Thu 22 17:06 | `mellum-plan` | Plan before the first edit | `screen`: **regressed** | 118 |
| Thu 22 17:13 | `mellum-surgical` | Anti-clobber | `conjecture` | 143 |
| Thu 22 18:07 | `mellum-contract` | Route test from the spec, no model | `conjecture` | 132 |
| Thu 22 18:29 | `mellum-loop` | Control outside the session | `conjecture` | 89 |
| Thu 22 22:58 | `mellum-flow` + `mellum-nonblock` | Phases as tools; servers threaded | `screen`: easy and medium pass; hard 29/34 | 531 / 88 |
| Thu 22 23:56 | `mellum-knowledge` | API lookup past the training cutoff | `conjecture` (0 calls observed) | 74 |

**The arc:**

1. Capability and observability around one worker (Wed 21).
2. Gates inside the session, which regressed (Thu 22 afternoon).
3. Control outside the model (Thu 22 evening onward).

None of the 21 Oct burst is in the shipped product's measured path.

### V.2 The worker prompt (`prompts/mellum-worker.md`, 607 → 2,326 characters)

| Version | When | Added | Answered | Badge |
|---|---|---|---|---|
| v6 | Mon 19 | Keep every existing test | P7 | "no measured lift, no regression" |
| v7 | Tue 20 | "Make one failing test pass": read the test and spec, create the module, run only the named test | test-chasing under v6 | `cited` 12/12 mediated. **But** the ablation shows v6 also scores 3/3, and shipped Mode under v7 scores **0/3** |
| v8 | Wed 21 14:11 | Run the whole file; pass every test | P3 | `screen`, no record |
| v9 | Wed 21 15:14 | "The spec is the full contract" | P2, P4 | `screen`, no record. The commit says n=3; LESSONS and v11 say 2/3 |
| v10 | Wed 21 15:37 | Never start a server; use TestClient in process | P5 | `screen` (changed with the guard) |
| v11 | Wed 21 16:23 | Re-read the spec clause by clause before finishing (worked example: `Complaint(agent_name, text)` with a counter id) | the 1-in-3 slip | `screen` 3/3 |

**What the sequence teaches:**

- **Telling raises the hit rate; self-checking closes the miss.**
- Every line came from *reading what the worker actually ran*, which is
  Paul's rule. v8 was found by watching a live run through
  `mellum-override`.

**Risks for Paul to weigh:**

- v9 and v11 name rung 9's exact miss and model, so the prompt may teach
  to the test. A held-out rung would settle it.
- v10 and v11 each changed together with the guard.
- v11 ships, but Mode has never been measured under v11 without
  `--acceptance-test`.
- Every committed run record is v6 (3) or v7 (40).

### V.3 Prompt lines outside the prompt file

- **Task line, Sun 18:** "Don't start servers". Paul flagged it as
  edging toward coaching.
- **Suite AGENTS.md** (all three suites):
  - `Test command: uv run --frozen python -m pytest tests`;
  - scoped changes;
  - run the test command and report;
  - `Do not: start servers`.

  Remedies for P5 and P6 are baked into the eval fixtures, so Baseline Pi
  with context files on already gets them.
- **Flow role prompts** (`mellum-flow.ts`, `flow_run.py`):
  - roles (22 Oct);
  - examiner (23 Oct 11:43);
  - strict negatives and edge cases (12:38);
  - identity (21:25);
  - no invented strings (21:59);
  - Pi base-prompt replace, then revert to append (21:59 → 23:02);
  - cohesive roles (23:15);
  - nine examiner rules (24 Oct).

  The examiner prompt went ~4,650 → ~2,560 characters and back up to
  ~3,770. These prompts live outside `prompts/`, the only prompt source
  (§VII).

---

## Part VI — Code-level evaluation

Measured from `git log 4245ba3..HEAD`, excluding run records, lockfiles
and fixtures.

- **Commit types.**
  - Andre: 44 `feat`, 38 `docs`, 14 `fix`, 8 `Flow:`, 18 untyped.
  - Paul: 76 `docs`, 37 `feat`, 12 `fix`, 9 `chore`, 7 `refactor`.
- **Code growth.**
  - extensions +4,267 / −578;
  - tests +2,951 / −1,190;
  - `learn/getting-started` +2,271;
  - scripts +1,238;
  - ladder code +878 / −599 (net shrink after the triage);
  - dashboard +765.
- **Hotspots.** `mellum-flow.ts` 24 commits, `run_ladder.py` 23,
  `harness.py` 22, `CHANGELOG.md` 123.
- **Fix chain.** The flow and examiner went through 27 commits in about
  46 hours, nine of them `fix:` on Sat 24. That is fast learning, done in
  production against the suite being scored.
- **Test discipline.**
  - Paul: 1 of 42 code commits touched no test.
  - Andre: 15 of 63 since 19 Oct touched no test, including the stall
    fix, the append revert, fail-open reviews and the prompt compression.
  - `content-tool-call-assist` has none.
  - Totals now: 485 node tests and 238 Python tests. `docs-caps` 4/4.
- **Churn artefact.** The hard suite's `numbers.txt` (500,000 lines × 3)
  was added and then removed (`564c31e`), about 1.5M lines.
  `ladder/fixtures/agentclinic-p7/numbers.txt` (3.9 MB) is still tracked.
- **Clean:** no `trace.jsonl`, `stdout.txt` or `diff.patch` in the tree.
- **Debt.**
  - `run_orient` `killpg` unguarded.
  - The in-agent `test()` scores all of `tests/` while the runner scores
    only the gate.
  - `visible` reflects only the last phase.
  - `.idea/` and two ~3.5–3.9 MB PNGs committed.

---

## Part VII — Fit with Paul's method: the audit

What already follows Paul's method, what does not, and the step that would
bring each piece into line.

### Conforms

- A21 and LC.3C were preregistered, with validity checks and disclosed
  reruns.
- The v7 ablation fixed its rule before the runs.
- LC.11A fixed its arms and n in a spec, screened first, and **dropped a
  module rather than overclaim**.
- Negative results are recorded as notes: tool strip, 3-bit, NCM × size.
- "Name the mechanisms" (`d547a63`) credits `--acceptance-test`, not
  "mediation".
- The 24 Oct note has a measured/conjecture header, a falsifier and risks.
- Examiner rules are stated generally, with suite names scrubbed.
- Fail-first tests on the grading and flow helpers.

### VII.1 The 22 October merge: what `main` lost

Andre merged `upstream/main` into the fork on Thursday 22 Oct (`0367d04`).
For every file both he and Paul had changed since their common base
(`b7d987d`), the result equals Paul's side exactly. Andre's 18–21 Oct work
is intact in history at `da04888`, an ancestor of `origin/main`. It is
absent from the files on `main`:

| Lost from `main` | Consequence today | Status (2026-10-24) |
|---|---|---|
| `ladder/ladder/run_ladder.py`, `pi_profile.py` and their tests: `--acceptance-test`, `--redispatch` (with the temperature and seed ramp), `--effort-ramp`, `--pi-extension`, `--model-spec`, `--model-id`, `--temperature`/`--top-p`, `--backend mlx-lm`, the focused test command and trimmed tools | The mediated path behind 12/12, the ablation, Mode 0/3 → 3/3 and rungs 10–12 cannot be rerun. `scripts/screen.sh`, `scripts/product.sh` and the dashboard's Start button (which runs `screen.sh`) call flags that no longer exist. `EXAMPLE.md` and `docs/backends/mlx-lm.md` describe them. | **Restored 2026-10-24** on the local branch `restore-mediated-ladder` (not pushed): hand-merged onto Paul's LC.3B flags, `--backend`/`--model-id`/`--model-spec` dropped in their favour; ladder suite 189 passed (158 on `main`) |
| `CHANGELOG.md` `[Unreleased]`: all of Andre's 18–21 Oct entries | The changelog did not describe what ships (v11, the extensions) | **Restored**: the 17 entries whose code survived, then the ladder entries rewritten for the restored code, under single headings |
| `AGENTS.md` run standard and "Driving the worker: don't trust its self-exit" | Undocumented, and the scripts it names were broken | **Restored**, updated for `--model omlx/<id>` and the archived M.11 row |
| `README.md`: "This session — 2026-10-18", "the 🍓 skill", "Getting started (the next engineer)" | Lost onboarding text | **Two restored**. "This session" left out: it repeats claims Paul's digest marked unsupported ("A21 at 0/3", "~150× faster") |
| `BACKLOG.md`: "Freeze-the-oracle exit gate", "mlx_lm.server vs oMLX" | Two reopen conditions lost | **Restored**, the second narrowed to servers (sampling sits under Paul's "Model-parameter impact") |
| `.gitignore`: `runs/` | `screen.sh` output is no longer ignored | **Restored** |

Paul's removals of the subagent and OpenCode templates in LC.8 and LC.8A
were deliberate, and they stay removed. The extensions, prompt v11, rungs
10–12 and the foreground-server guard survived the merge.

### VII.1a Does the lost ladder code fit Paul's method?

**Mostly yes as an instrument; not yet as evidence.** The code measures a
question Paul himself kept open: his BACKLOG entry "The mediated test" names
Andre's PR #1 as the candidate, and the archived M.11 row describes this
test. Paul's own digests badge each piece within his method
([PR digest](docs/superpowers/research/2026-10-20-pr-digest.md),
[follow-up digest](docs/superpowers/research/2026-10-21-andre-follow-up-digest.md)).

| Piece | Paul's badge | Fits | Does not fit |
|---|---|---|---|
| `--acceptance-test` (place an external, frozen test) | `screen` | The exit-gate principle (external, complete, unweakenable); scored by Paul's own hidden tests and write list; lives in the ladder, not a scratch driver | Its first PASS was n = 1 and confounded with the no-servers line and an unused re-dispatch budget |
| `--redispatch N` (re-run the frozen test, hand back the failure) | `screen` | Verifies the exit instead of trusting it | Three things changed between the two probes (freeze, re-dispatch, budget) |
| Temperature and seed ramp on retry | `conjecture` | Default off; existing records unaffected | Nothing shows a retry passing because of it; the kind of knob the 13 Oct triage cut |
| `--effort-ramp` | `screen` (deadline re-dispatch) | Spends compute in proportion to measured difficulty | The v7 ablation found fixed-high budget fastest (163 s), so the ramp is the wrong default on hard rungs |
| `--backend mlx-lm`, `--model-id`, `--temperature`/`--top-p` | runs on mlx-lm stay `screen` | Defaults leave oMLX runs unchanged | Overlaps Paul's LC.3B `--provider`, `--base-url`, `--model`, which do the same job |
| `--pi-extension`, `--model-spec` | — | Lets an extension such as `mellum-ncm` be measured without shipping it | — |
| `--acceptance-test` in `--mode mode` (`faaed7e`) | `screen` | Measures the shipped worker, as "measure what ships" asks: Mode 0/3 → 3/3 | n = 3, recorded only on the fork |

**Against Paul's rules as a whole:**

- **Conforms:**
  - The experiments came with screens first, research notes with honesty
    headers, and a written preregistration (mediated vs stock, rungs 6–9)
    before any deciding run.
  - Every new flag defaults off, so no measured setting changed.
  - Commits carried tests.
- **Does not conform:**
  - *No record on `main`.* Paul: entries stay screens "until a record
    lands here". Today the records are on the fork's `main` but the code
    that produced them is not, so they cannot be reproduced.
  - *The deciding run never ran.* Arm B of the preregistration needed
    oMLX, so no promotion was earned.
  - *The early screens ran a setup the product does not ship* (direct
    mode, mlx-lm, `tuned`, guards). M.11 asked for Mode. That makes them
    harness findings, not worker claims, until the Mode runs.
  - *The harness got thicker.* Two ramps and a second backend surface,
    against "keep the harness thin".

**A restore that conforms:**

1. Bring back the M.11 core: `--acceptance-test`, `--redispatch`, the
   Mode support and `--pi-extension`.
2. Express the backend choice through Paul's LC.3B flags rather than
   `--backend` and `--model-id`.
3. Keep the ramps opt-in, labelled `conjecture` in the changelog.
4. Then run arm B, or its llama.cpp equivalent, so the 12/12 can be
   reproduced on `main` and earn `cited`.

*Done 2026-10-24 (steps 1–3), on the local branch `restore-mediated-ladder`.*
The restored tests were shown failing against `main`'s runner (29 failures),
then passing on the merge. One change goes beyond a straight restore: Andre's
code had trimmed the tool set to five for *every* direct run, which would have
changed Paul's measured unmediated runs (the llama.cpp reference used seven).
The trim now applies only when `--acceptance-test` is set, as Andre's own
changelog described it, with a fail-first test. Not restored: `--model-spec`
(small-model screens only; still at `da04888`). Step 4 is still owed.

### VII.2 Does not conform yet, and the step that fixes it

| Gap | Rule it breaks | Step to conform |
|---|---|---|
| Flow (22–24 Oct) has no roadmap phase, spec or plan; `## Now` reads "Active: none" | SDD cycle; `## Now` is a pointer | Add an LC row (or Andre-track rows) for flow and the examiner. Write a spec, since product behaviour changed in the ladder (`--mode flow`) |
| v8–v11 ship with no `evals/` record; v11 is unmeasured in Mode | Measured settings change only with a recorded ladder run | Preregister: v11 vs v7, Mode and direct, rungs 1–12, n=3. Record it. Revert to the last recorded prompt if it loses |
| Flow, Flint parity, bare 6/12, the 1.5B result: no records | Skill §11: record every run that backs a claim | Commit `table.md` + `run.json` under `evals/`; raw evidence in a `research-2026-10-2x` release |
| New defaults with no ladder run: `confineToWorkspace` on, suites easiest-first, per-phase `max_tokens` | Measured settings | Run one ladder arm with and without, or make each opt-in |
| Flow and examiner prompts live in code | `prompts/mellum-worker.md` is the only prompt source | Move the role prompts under `prompts/` (for example `prompts/flow/*.md`) or amend AGENTS.md by decision |
| The 22 Oct merge dropped Andre's ladder code and records (§VII.1) | Measure what ships; keep the changelog current | **Done 2026-10-24** on a local branch; reproducing the 12/12 on `main` (arm B) is still owed |
| Duplicate `Added`/`Fixed` headings; flow sub-agents said to "REPLACE" Pi's prompt; examine at 16,384; no entries for `48ed09e`, `ccc049f`, `3fc1d27`, `891721a`, the intro page or the install scripts | Entries say what changed | **Done 2026-10-24**: one heading each; the replace/revert history stated; 32,000 noted; entries added |
| `mellum-flow.ts` `BASE_GUIDE` comment described the reverted `--system-prompt` | Code reads true | **Done 2026-10-24** |
| README: "a 643-character worker prompt" (v5), "15/15" | README states what ships | Update once v11 has a record, or state plainly that v11 ships unmeasured |
| LESSONS 23 Oct "seven phases visible" without a correction after `433157e`; "Proven (measured)" on n=1 runs | Reversals recorded beside the original, dated | **Done 2026-10-24**: dated corrections beside both |
| v9 commit says 3/3; LESSONS says 2/3 | Claims match the evidence | **Done 2026-10-24**: dated correction in LESSONS (2/3 stands; the screens have no record) |
| LC.11A easy rows graded by the pre-fix `grade()` | Before blaming the model, check the scoring | Re-grade the retained workspaces (no model time) |
| Examiner tuned on the suite it is scored on | Check the scoring can distinguish; screens are not rates | A held-out suite or rung before any lesson claims it |
| `research-2026-10-20` not released | A `reference-run` needs raw evidence | Publish the tarball |
| AGENTS.md cites OpenCode for the install-script rule | Accurate rationale | Re-word for Pi's git install |
| Site deploys from `main` before Andre's linkable consent (LC.5) | Spec gate | Post the consent quote |
| Intro page: "Andrew Markov" should be Andrey; framing of LLMs as grown N-grams | Accuracy | Review before readers rely on it |

---

## Part VIII — Mapping to `learn/`: from a basic harness to an enhanced one

The learner's arc is the suite scoreboard in Part I. **Baseline Pi fails
easy, medium and hard.** Each lesson adds one remedy for one pathology and
shows the scoreboard move, in Paul's six steps. Getting Started is the
basic harness. The enhanced lessons slot into Paul's LC rows where one
fits, and otherwise into Andre's track (LC.5).

### Part 1 — the basic harness (exists)

| Lesson | Teaches | Status |
|---|---|---|
| GS 1 Base Pi on llama.cpp | backend, private profile | shipped |
| GS 2 The ditch | P1: false success, fabricated evidence, dropped requirement | shipped (n=1) |
| GS 3 Mini harness | one isolated, scored run | shipped |
| GS 4 Suites and telemetry | hidden graders, qualification, reading a trace | shipped; re-run owed on the rebuilt hard |
| GS 5 The worker extension | extension mechanics, `/mellum` | shipped |
| Lessons: Baseline | Baseline Pi 0/9 vs Baseline Worker 3/9 | shipped (`screen`) |
| LC.7A Pathologies | the catalogue: **Part IV of this report** | not started |

### Part 2 — the enhanced harness (proposed order)

| # | Lesson (pathology → remedy) | Artifact | Row | Badge now | Run owed |
|---|---|---|---|---|---|
| E1 | See what it actually did | `watch_ladder.py`, feed, dashboard | Andre | `conjecture` (a how-to) | none |
| E2 | Suspect the check first (**how easy was cracked**) | grade fixes; known-good qualification | LC.7A / Andre | `cited` (fail-first tests) | re-grade LC.11A easy |
| E3 | Thinking is working memory: caps that truncate | per-role `max_tokens` | **LC.12** | `screen` | suite at two caps, n=3 |
| E4 | Servers block | v10, foreground-server guard, nonblock, suite fact | **LC.13** | `screen` | medium with and without the guard |
| E5 | Project facts | `## Mellum`, suite AGENTS.md | **LC.14** | `cited` | llama.cpp reference run |
| E6 | Write only what you list | surgical, `confineToWorkspace`, write-list, `plan/` | **LC.15** | `conjecture` / `cited` | suite with and without |
| E7 | Self-narrowing, two forms | v8; v9 + v11 | Andre | `screen` | preregistered v11 vs v7 |
| E8 | Don't trust the exit: freeze an external test | `--acceptance-test`, `--redispatch` | Andre (mediated-test backlog) | `cited` 12/12 + ablation | Mode arm B |
| E9 | A gate makes it try, not able (negative) | `mellum-ncm`; 3-bit; 1.5B | Andre | `cited` | — |
| E10 | Who holds the loop: in-session gates regress | plan (regression) → loop → flow | **LC.16** | `screen` | flow vs worker, n=3 |
| E11 | One spec file per phase: decomposition | `flow_run.py` split, north star | **LC.19** | `screen` | — |
| E12 | The examiner, a spec-derived definition of done (**how medium was cracked**) | examine, frozen accumulating gates, identity rule | Andre | `screen` | `--mode flow`, rungs 6–12, n=3 |
| E13 | Writing tests a correct app can pass | examiner rules (redirects, substrings, deltas) | Andre | `screen` | gate vs known-good per phase |
| E14 | The hidden-oracle gap (**where hard stands**) | completeness rules | Andre | `conjecture` (not re-run) | hard re-run, then a held-out suite |
| E15 | Grounded knowledge past the cutoff | `mellum-knowledge` | Andre | `conjecture` | measure lookup use on hard |
| E16 | Sidebar: tiny models and tool formats | assist; 0/15 strip | Andre | `screen` | — |

**Paul's rows with no Andre counterpart.** LC.17 (a prose brief stops) and
LC.18 (the intercom prefill tax) stand alone. LC.10 and LC.11 are written.

**Before any Andre-track lesson publishes:**

- The LC.5 consent quote.
- Steps 3 and 5 of each lesson backed by the run in "Run owed", recorded
  in `evals/`.
- The Part VII gaps closed, so lessons can cite `main`.

---

## Part IX — Open questions and runs owed

0. Andre's ladder runner code is restored on the local branch
   `restore-mediated-ladder` (§VII.1a); merge it into the fork's `main` so
   items 1 and 2 can run there.
1. Mediated vs stock, rungs 6–9, arm B (preregistered Sun 18, never run).
2. v11, preregistered, in Mode and direct. Then a held-out rung for
   leakage.
3. Hard re-run with the 24 Oct examiner rules. Does 29/34 close, and does
   the ~3.8k-character examiner still converge on every phase?
4. `--mode flow` vs direct, and Flint vs Mellum, n≥3.
5. Recalibrate hard so arms separate under the Baseline Worker.
6. No-nudge 5/9 vs Worker 3/9 at a larger n.
7. Best-of-N (concurrency > 1) vs sequential retries.
8. Re-grade LC.11A easy with the fixed `grade()`.
9. Release `research-2026-10-20`. Commit the Sun 18 records. Re-baseline
   the 6-bit with guards on.

---

## Sources

- **Research:**
  - `docs/superpowers/research/2026-10-13-*`
  - `docs/superpowers/research/2026-10-18-*`
  - `docs/superpowers/research/2026-10-19-*`
  - `docs/superpowers/research/2026-10-20-*`
  - `docs/superpowers/research/2026-10-21-*`
  - [2026-10-24 flow note](docs/superpowers/research/2026-10-24-flow-hard-visible-pass-hidden-gap.md)
- **Records:**
  - `evals/ablation-a21-*`
  - `evals/screen-rung9-*`
  - `evals/2026-10-20-*`
  - `evals/2026-10-21-*`
  - `evals/baseline/2026-10-20-reference-llamacpp-rungs1-5`
- **Specs:**
  - `2026-10-12-mellum-last`
  - `2026-10-20-learning-center`
  - `2026-10-20-one-pi-worker`
  - `2026-10-21-basic-remedies`
  - `2026-10-22-eval-suite-pipeline`
- **Plans:** `docs/superpowers/plans/archive/2026-10-20-*`, `…/2026-10-21-basic-remedies.md`
- **Root documents:**
  - [LESSONS.md](LESSONS.md)
  - [THEORIES.md](THEORIES.md)
  - [CHANGELOG.md](CHANGELOG.md)
  - [ROADMAP.md](ROADMAP.md)
  - [BACKLOG.md](BACKLOG.md)
  - [AGENTS.md](AGENTS.md)
  - [README.md](README.md)
  - [docs/sdd.md](docs/sdd.md)
- **Method:**
  - [evidence.md](learn/about/evidence.md)
  - [lesson-template.md](learn/lesson-template.md)
  - [ditch.md](learn/getting-started/ditch.md)
  - [lessons/baseline.md](learn/lessons/baseline.md)
- **Code:**
  - `git log -p -- prompts/mellum-worker.md`
  - `extensions/*.ts`
  - `learn/code/{harness,flow_run,loop_run,evidence}.py`
  - `learn/code/suites/*/{base,grader}`
