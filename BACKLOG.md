# Backlog: mellum-worker

Deferred work. Read [`ROADMAP.md`](ROADMAP.md) for what is in flight.

Every entry states a reopen condition; an entry over 1,200 characters owes a
research doc and shrinks to a summary, a link, and its reopen condition.
Resolved entries are removed once their outcome is recorded in a feature-cycle
row or a research doc that the row links. Cite entries by heading anchor,
never by line number.

Reopen conditions, not promises.

**Kill-by-name test skipped on the GitHub Actions runner.**
`tests/backend-lifecycle.test.mjs`'s "kill ends every process with the server's
name" spawns two fake processes under a unique name and asserts `backend.py
kill` ends them via `pgrep -x`. It fails only on the hosted GitHub runner:
`backend.py`'s `pgrep` finds nothing even though the test's own `pgrep` saw both
fakes a moment earlier. Not reproducible on macOS or a clean Ubuntu 24.04
container — there a copied binary keeps its name as `comm` and `pgrep -x`
matches, and the production path (`pgrep -x <name>`) is proven correct — so the
test is skipped when `GITHUB_ACTIONS=true` rather than left red. *Reopens when*
the failure reproduces off the hosted runner (e.g. under parallel `node --test`
load) and the cause is pinned.

**Grounded knowledge / docs lookup for the coder.** The model fails exact-API
contracts it cannot know — FastAPI's `RedirectResponse` default (307, so a POST
redirect loops; the spec needs 303), the sqlite-utils migration API, hard's
phase 6/7 SQL semantics — and, decisively, anything past its training cutoff:
the ladder runs on Python 3.15, which the model was never trained on. Reasoning
cannot recover post-cutoff facts. Plan: give the coder a `lookup` tool grounded
in the LIVE environment — installed-package signatures, docstrings, source,
`--help`, changelogs — not a stale snapshot, so it reflects the exact versions
running; prompt it to look an API up before guessing, especially when a failure
is API-shaped (`TooManyRedirects` → redirect status). Fairness boundary: ground
on library docs a developer would have, never the task solution or hidden
grader. Local retrieval (offline, reproducible) over open-internet lookup, which
breaks the ladder's reproducibility. *Reopens when* a grounded-knowledge trial
is scheduled against the exact-contract phases (hard 3/6/7).

**Generalized task decomposition for `flow_run`.** `split_phases` only splits
on `## Phase`, so it chunks the suite prompts but not an arbitrary large
command (a spec wall, an issue dump, a file to refactor) — which this model
drowns on, as it cannot bound its reasoning (`supportsReasoningEffort: false`).
Planned layers, cheapest first: structural split (any header level, top-level
numbered/bulleted items, `#{1,2} Phase/Step N`); a size gate (small stays one
unit); a splitter sub-agent that emits a numbered step list from an
unstructured wall (small output over large input); a paragraph size-chunk
fallback. A terse step stays grounded by threading a small, constant forward
context — north star, a running summary of what is built, the last phase's
context — plus its own slice, not the whole wall. *Reopens when* a
non-phase-structured task is measured on `flow_run`, or the harness is pointed
at real-world, non-suite commands.

**Lesson 10's layout question needs a sample it does not have.** The
preregistered `joined`-against-`split` arm came back null at n = 3: phase-4
missing {5, 0} against {0, 3}, two usable sessions per arm, and medium 0/3 on
passes for both arms
([record](docs/superpowers/research/2026-10-25-lesson10-run.md#attempt-4-2026-10-2527-the-arm-ran-and-the-layout-did-not-separate-it)).
The reading had to be the per-module one because medium floors on passes, so a
claim about spec layout needs a task above that floor **and** n above 3.
*Reopens when* a suite with pass headroom exists, or a lesson or default needs
the layout claim.

**Checks that never ran read as every check missing.** `score_workspace_details`
counts as many missing checks as `expected.json` lists whenever pytest aborts
before running them: LC.19's attempt 3 scored 18/18 with `passed: false` because
two grader modules hit `ModuleNotFoundError: No module named 'models'` and pytest
stopped with `Interrupted: 2 errors during collection`
([record](docs/superpowers/research/2026-10-25-lesson10-run.md#attempt-3-2026-10-26-the-hang-is-fixed-the-scoring-is-not-yet-measuring)).
Phase 1 alone passed 3 of 4. A record could not tell "the worker failed everything"
from "the checks never ran" without the tail. LC.19A-adjacent work added
`checks_ran: false` for that case; what is still owed is a lesson table column
that shows it wherever a record reports missing checks.
*Reopens when* a lesson table quotes a full set of missing checks without
saying whether they ran.

**The leak sweep misses a foreground server that made its own process group.**
`pi`'s bash tool runs each command in a new session, so a model-started server
lands in its own group; `run_suite` kills and sweeps `child.pid`'s group, which
is `pi`'s, so `leaked.json` reports nothing. LC.19's attempt 2 hung on
`uv run python -m uvicorn app:app --reload` in its own group, and a
`uv run uvicorn app:app --port 9000` from run `20261025T112212Z-medium-31816b`
was still alive 1 day 7 h later, holding its port
([preregistration](docs/superpowers/research/2026-10-25-lesson10-preregistration.md#amendment-2026-10-26-attempt-1-aborted-before-any-session-completed)).
A censored session therefore leaves a server behind and the next session
inherits the port. The fix is to sweep children by ppid as well as by group.
*Reopens when* a censored session's `leaked.json` is empty while a server
survived, or the sweep is next changed.

**The deadline is counted on a clock that stops when the Mac sleeps.**
`run_suite` bounds each child with `child.wait(timeout=remaining)` from
`time.monotonic()`, and on Darwin that clock does not advance while the system
sleeps: LC.19's attempt 1 hung on a foreground server and had counted roughly 8
minutes of its 2,700 s after 62 minutes of wall, so no `deadline` marker existed
and the session outlived its budget by the sleep
([preregistration](docs/superpowers/research/2026-10-25-lesson10-preregistration.md#amendment-2026-10-26-attempt-1-aborted-before-any-session-completed)).
A `deadline` marker is therefore only honest on a machine that stayed awake; a
run that quotes one should say it was caffeinated. The fix is a wall-clock
deadline, or a `deadline` row in the trace carrying both clocks.
*Reopens when* a run's deadline marker is missing past its budget, or the harness
deadline is next changed.

**`run.json`'s `wall` under-reports a censored or stalled session.** `report()`
in `learn/code/harness.py` derives wall from trace timestamps, so a session
the deadline ends reports its last traced event: LC.24's two censored `bare`
sessions report 70 s and 180 s against a 2,700 s deadline, one session killed at
600 s recorded 164 s, and LC.19's censored session recorded 448 s against 2,700 s
([LC.24 run](docs/superpowers/research/2026-10-25-lesson1-run.md),
[context screen](docs/superpowers/research/2026-10-24-context-budget-screen.md),
[LC.19 run](docs/superpowers/research/2026-10-25-lesson10-run.md)).
Only the `deadline` marker tells the truth, so any table quoting wall beside a
censored session is understating it. The fix is a wall from process lifetime,
or a `deadline` row in the trace; it changes a column the Getting Started
suite lesson teaches, so it needs its own test and a re-read of the records
that quote a wall, not a mid-arm patch.
*Reopens when* a page or an arm quotes a wall for a session that hit its
deadline, or when the harness report is next changed.

**The foreground-server pathology is measured but not placed.** Three
`no-facts` sessions hung on `uvicorn app:app --reload` / `python app.py` after
143–460 s of silence and died at the 600 s deadline
([record](docs/superpowers/research/2026-10-24-project-facts-screen.md)); LC.24's
`bare` easy arm and LC.19's first two attempts hung the same way. It is Andre's
(index P2) and belongs to **LC.7A**. 2026-10-27: the guard fired **0** times on
medium — neither arm issued a foreground command, because the briefs now name the
verification loop
([run](docs/superpowers/research/2026-10-26-server-guard-run.md)) — so it stays
dormant and the pathology is instructional, not unfixed.
*Reopens when* LC.5 closes and LC.7A starts, or the arm's three-way question
(facts bullet, dormant guard, both) can land on a page.

**The recorder cannot have the payload and the refusal at once.** Pi runs
`before_provider_request` handlers in extension load order and each may
replace the payload, so a recorder loaded first sees messages before the
worker appends its facts block (79 requests counted zero injected blocks,
[record](docs/superpowers/research/2026-10-24-context-budget-screen.md)), and
a recorder loaded last never sees a compaction the worker cancels. The split
is a second, tiny watcher extension for `session_before_compact` alone, with
its own trace file so the two writers do not share a `seq` counter.
*Reopens when* an arm needs both a payload reading and a refused-compaction
count in one session, or when the recorder is next changed.

**Discovery/output policy beyond M.7E.** Seven tools do not prevent shell
dependency scans. Throwaway discovery interception blocked scans, but its
compact-output branch had no model-run evidence and its heuristics can block
legitimate recursion. M.7C/M.7D own telemetry and regression cases; M.7E owns
any narrowly justified Pi trial. Broader output preservation/compaction is
still deferred ([synthesis](docs/superpowers/research/2026-10-11-session-to-roadmap.md)).
*Reopens when* corrected host records show retrieval remains material after
M.7E, with scoped legitimate recursion and recoverable full-output checks.

**Natural project instructions and a short test-first policy.** Pi 1.0.2
transfer spike: measured phase facts complete/correct 2/2; general replacement
0/2 (one template leak missed by hidden tests, one blocking-server timeout).
Mode parser general 1/2, TDD 0/2; the bullet reached Mellum but execution failed.
Worker general and TDD both 2/2; TDD achieved behavioral red/green twice, once
with parent resume/repair. Parents supplied enriched briefs, so this is not an
isolated bullet effect. Keep ordinary command/environment and bounded facts;
no video-continuity constraint, no further hello-world tuning, no universal
TDD rule from n=2
([results](docs/superpowers/research/2026-10-11-pi102-mode-worker-experiments.md)).
*Reopens when* broader transfer/TDD ladder trials are scheduled; shared prompt
or setup/learn promotion needs applicable ladder and host checks.

**Prompt default `python -m pytest` (Worker).** Prompt v5 guesses `uv run
--offline pytest -q`, which runs the `pytest` entry point without the
project root on `sys.path`. Since M.7, Mellum Mode forwards the `## Mellum`
test command, or `uv run --offline python -m pytest -q` for a pytest
pyproject (AgentClinic rungs 6–9: section 9/12,
fallback only 7/12, facts off 1/12 rescored;
[research note](docs/superpowers/research/2026-10-09-m7-project-facts.md)).
The Worker's child still sees only the brief and the prompt, so a parent
that omits the test command gets the guess. A `v6` default is a prompt
change for both paths, sized in the
[steering note](docs/superpowers/research/2026-10-09-steering-and-next-phase.md)
§2; rungs 6–9 are the ac-demo-shaped fixture it asked for. *Reopens when* a Mode run record shows the prompt's default run and fail in a project without a `## Mellum` section; the Worker path goes with M.12.

**Ladder drives the one-shot command.** After M.5, `pi -p "/mellum
<sentence>"` works, so the ladder could launch the shipped command (and get
run records per run) instead of `MELLUM_MODE=1`. That changes the measured
launch (an on-marker in the messages), so it is a phase compared against
A17, not a runner tweak. *Reopens when* M.11's screen is set up: its runner drives `/mellum` with a test file, and launching the shipped command is the same change.

**Final reply omits moves and pre-existing work.** Recorded forms: a reply
silent about `rm tests/test_hello.py`; a reply claiming to have created files
a previous run left behind (`files: []`, one passing command); dead code and
an environment mutated to make a named command pass. The completion fact
makes "exits 0" the goal. The handoff and the Worker's parent test run are
the measured answers; schema-2 records (M.5) make the gap countable.
*Reopens when* records show two or more runs whose final reply claims success
with `filesMissingAtEnd` non-empty or `lastCommand` not `ok`.

**OpenCode 2.x plugin shape.** The V2 host reads `default.setup`, not
`server`, and uses a flat `skills` array. *Reopens when* a 2.x host is
available to test against.

**Empty-final nudge misses announce-and-stop turns.** The guard nudges only
when a turn ends with no text. The A17 rung 5 miss ended with "Now let's run
the tests again." and no tool call: the turn had text, so no nudge fired and
the run stopped unfinished. A check for a final turn that announces an action
without making a tool call would catch it, but it is a guard change on a
single observed miss in 30 Mode runs (A14, A17). *Reopens when* a second
announce-and-stop miss is recorded in a ladder phase or a run record.

**The worker refuses compaction, so a long suite run overflows.** While the
worker is on, `session_before_compact` refuses Pi's auto-compaction, so a run
whose history outgrows the window has no way down. On the easy suite against
llama.cpp at `n_ctx` 50,176, three of ten sessions in the LC.13A guard arm
ended with an `error` final: `request (51697 tokens) exceeds the available
context size (50176 tokens), try increasing it`. The empty-final nudge cannot
answer these — it continues only a `stop` turn — and the same refusal will
truncate every later arm. *Reopens when* an easy-suite run is expected to
finish on the taught backend: choose a window the task fits inside, or a
compaction policy that does not refuse while the mode is on, then re-baseline
the suite, because the change moves a setting the baseline was measured with.
[arm record](docs/superpowers/research/2026-10-24-nudge-llamacpp-screen.md).

**Write-only guard: refuse writes outside the facts block's list.** Mode
forwards the `## Mellum` section's `Write only:` line as text; nothing
enforces it. On AgentClinic rungs 6–9 the text was enough: with the section
forwarded, 0/12 runs had a non-empty `outside_write_list`
([A19](evals/2026-10-10-ablation-a19-facts-on/README.md)), against 8/12 with facts
off (A18) and 5/12 with the fallback only (A20, no list sent). A guard that refuses `write`/`edit` outside the list is a guard
decision, so it is measured before it ships.
*Reopens when* a facts-on ladder phase or a run record shows a non-empty
`outside_write_list` with the list forwarded.

**Facts and learn v2: uv and `.venv`.** A session in ac-demo lost an
exit-127 detour to bare `python` (not on PATH; only `uv run` works) and a
large result from `find .` walking `.venv`
([note](docs/superpowers/research/2026-10-11-facts-wording.md)). Candidates:
a suggested bullet `Run Python with uv: uv run python …`; `learn` patterns
for "command not found" or exit 127 on `python`/`pytest` (remedy: the uv
bullet) and for `find`/`grep -r` over `.` without excluding `.venv`
(remedy: a positive bullet, `List project files with: git ls-files`;
in a bare-Pi run on 2026-10-11 "Do not: search .venv/" did not stop
`find .` walking 52 KB of `.venv`, while the command-shaped uv bullet
worked first time, so suggest commands, not prohibitions); ac-demo's roadmap saying `uv run
python app.py`; `/mellum check` linting the `## Mellum` section (nested
bullets or continuation lines, a test label not exactly `Test command:`, a
fallback adding a second test command; seen in ac-demo 2026-10-11). The
bullets change what Mellum reads, so they need their own ladder arm; A21
(2026-10-13) measured the section without them. *Reopens when* a ladder
arm for these bullets is scheduled.

**Worker recorder never resets after a settle.** `createRecorder` in
`extensions/mellum-guards.ts` keeps its baseline and turns for the whole
process, so a session that sends several prompts (the guards loaded with
`-e` in an interactive session, or a Worker child a host re-uses) writes a
cumulative line per settle with the same task, and `/mellum learn` counts
each as a run. pi-subagents children run one prompt per process, so it does
not arise there. The fix is a new baseline at each new user prompt, with
the dedupe key per prompt. *Reopens when* a host re-uses a Worker child
across prompts, or `learn` reports from `-e` sessions start to matter.

** The OpenCode
port ships a step-capped Worker subagent, installed through the plugin array,
with no Mode, guards or run records; the README says it is unmeasured.
Measuring it needs a `--harness opencode` runner in `ladder/` and a record
writer built against observed runs. The Pi Worker's retirement in M.12 does
not touch it. *Reopens when* an OpenCode user reports a run worth measuring,
or someone offers the runner.

**Ollama backend (was M.4).** GGUF weights, a Modelfile, a tool-call check,
provider templates for both hosts and a ladder rerun;
[`docs/backends/ollama.md`](docs/backends/ollama.md) lists what a port needs.
Only oMLX has been run. *Reopens when* a machine without Apple Silicon is on
hand to run the ladder against it. Restored 2026-10-20: LC.2 chose llama.cpp,
so this entry is not taken and its condition still stands.

**Execution bounds (was M.7E).** A measured opt-in policy for bash commands
with no timeout under the shipped guards, preserving explicit overrides and
verifying process cleanup, with completion scored separately. The
[phase](docs/superpowers/research/2026-10-11-pi110-opt-in-guards.md) and
[hello](docs/superpowers/research/2026-10-11-pi110-hello-guards.md) probes show
the mechanism in bare Pi, not a benefit; `Do not: start servers` and the
ladder's leftover-process cleanup (0.1.8) cover the cases seen in Mode.
*Reopens when* a ladder record or run record shows a Mode run cut by a
blocking command that those two did not handle.

**Versioned assessments (was M.7D).** Four independent dimensions (behavior,
verification, completion, report support) as a sidecar beside each run's
`run.json`, originals preserved;
[approved spec](docs/superpowers/specs/2026-10-11-m7d-versioned-assessment-design.md),
[superseded plan](docs/superpowers/plans/archive/2026-10-11-m7d-versioned-assessment.md).
Retired on 2026-10-13 as instrument work the current checks already cover
([triage](docs/superpowers/research/2026-10-13-roadmap-triage.md)). *Reopens when* a decision is blocked because two arms tie
on pass/fail but differ in verification or report, and the existing `check`
fields cannot show it.

**The mediated test.** Your main model turns a request or a spec phase into
a failing test, shows it, and hands it to the worker as "make this pass";
completion is scored by the hidden tests and write list, with the test
written once and not by the worker. Measured in the triage note's order: a
rung 9 screen (three runs) first, then a preregistered run on rungs 6–9
against A21's 9/12, then a command that records the test beside the request.
Andre's [PR #1](https://github.com/pauleveritt/mellum-worker/pull/1) is a
candidate implementation (`--acceptance-test`; an n = 1 rung 9 screen on
mlx-lm, [digest](docs/superpowers/research/2026-10-20-pr-digest.md)).
*Reopens when* someone can run the rung 9 screen and wants the result; the
closed cycle and its design inputs are in [`ROADMAP-M.md`](ROADMAP-M.md).
2026-10-24, on Andre's fork: `--acceptance-test` and `--redispatch` are on
`main` again after a merge dropped them ([LEARNING](LEARNING.md) §VII.1).

**Freeze-the-oracle exit gate.** Make "done" an external test the worker cannot
weaken, instead of its own final message. Promote the ladder's scorer checks
(`existing_tests_kept`, `outside_write_list`) into a runtime guard on the
worker, and gate the exit on an actual run of the frozen acceptance test with
the failure re-dispatched as the next "make this pass". The mediated test
supplies the external, complete test; the unweakenable half is here
([note](docs/superpowers/research/2026-10-18-harness-exit-gate.md)).
*Reopens when* a mediated run moves rung 9 and a trace shows a worker editing or
deleting a test to exit, or writing outside the allowed paths, on a run that
then scored as done. 2026-10-24: restored after a merge dropped it; rung 9 has
moved (screens), but no such trace is recorded yet.

**Benchmark a plain mlx_lm.server against oMLX.** The ladder reaches any
OpenAI-compatible server (`--provider`, `--base-url`, `--model provider/id`;
[recipe](docs/backends/mlx-lm.md)), but no oMLX-vs-mlx-lm runs have been made.
The servers cannot be made byte-identical: `thinking_budget`,
`max_tool_result_tokens` and penalty handling are oMLX server-only with no
mlx_lm.server equivalent, so a result is a harness finding about servers, not a
claim about the shipped worker. Sampling sweeps belong to "Model-parameter
impact on eval results". *Reopens when* someone runs a screen (a few rungs, a
research note naming the server's launch flags and n); a measured claim needs a
preregistered run with the server differences pinned.

**One worker.** Retire the pi-subagents Worker (agent template, child-only
guard loading, Worker run records, the setup skill's agent-file and intercom
phases, the ladder's `delegated` mode) and rename: `extensions/mellum-mode.ts`
becomes `mellum-worker.ts` and "Mellum Mode" becomes mellum-worker in the
docs, skill and templates. `/mellum` and the run-record path stay; `learn`
and `last` keep reading old `kind: "worker"` records; a rung 1 and a rung 6
smoke show the rename launches the same requests. *Reopens when* the mediated
test lands, or the rename is worth doing on its own; the closed cycle and its
exclusions are in [`ROADMAP-M.md`](ROADMAP-M.md). 2026-10-20: taken as LC.8
because the Learning Center needs one worker; the entry stays until it lands.

**pi-subagents Worker: one-liners and an in-process child (were M.8, M.9).**
`async: false`, a re-dispatch line in the description and the intercom
opt-out ([A11](evals/2026-10-09-ablation-a11-delegated-nointercom/README.md)); a
`mellum_worker(task)` tool through Pi's SDK
([cost note](docs/superpowers/research/2026-10-09-worker-cost-options.md) §2,
§3b). *Reopens when* M.12 does not retire the Pi Worker.

**PyCharm learning content.** Learning Center material made for PyCharm
users, building on the Getting started track. Paul's pitch to Andre
(2026-10-20) names it as a later step that needs JetBrains approval; the
[Learning Center spec](docs/superpowers/specs/2026-10-20-learning-center-design.md)
excludes it. *Reopens when* JetBrains approves the content and LC.3 has
closed, so both Getting started lessons exist to build on.

**Satyrn Education refactor.** Move the Learning Center from `learn/` in
this repo to Satyrn Education, keeping lessons as plain Markdown with front
matter so the move is a copy
([spec](docs/superpowers/specs/2026-10-20-learning-center-design.md) §11).
From Paul's pitch to Andre (2026-10-20). *Reopens when* LC.5 has closed and
Satyrn Education is ready to host the lessons.

**Model-parameter impact on eval results.** What temperature, `top_p`, `top_k`
and context do to rung scores is unmeasured; the lesson that teaches a setting
needs that evidence, and the settings come from a checked-in project file so an
arm can differ by one value ([spec](docs/superpowers/specs/2026-10-20-learning-center-design.md)
§12). *Reopens when* LC.3's harness can run a rung fixture twice with one
parameter changed.

**PR #1 prompt and guard extraction.** The prompt v6–v11 triage is recorded: v6 is a null arm, v7–v9/v11 are ladder evidence, and v10’s foreground-server guard is dormant on branch `lc11b-server-guard` at `420ba1d`; workspace confinement is on branch `lc11b-confinement` at `176922f`. No guard is enabled and Baseline Worker is unchanged. Prospective Lessons #20–#22 are index entries only, not feature cycles. The source map is the decision ledger. PR #1 stays open; the digest ends with a comment, not a close. *Reopens when* Getting Started is closed and a screen repeats a foreground-server or outside-workspace hang, or a prompt version has a suite-shaped arm worth measuring; enabling a guard needs a baseline v2 and re-baseline. [prompt triage](docs/superpowers/research/2026-10-24-prompt-v8-v11-triage.md), [PR #1 digest](docs/superpowers/research/2026-10-24-pr1-digest.md), [source map](docs/superpowers/research/2026-10-24-andre-lessons-map.md).

**PR measurement support.** The PRs carry measurement machinery that is not a lesson: the mlx-lm backend, the effort-ramp flags, the mediation scripts, rungs 10–12, `scripts/screen.sh` and `product.sh`, `halve-model.sh`, and the workflow/tests. None is in the installed package or the Lessons track. *Reopens when* a preregistered ladder run or a Flow phase needs one of them; port only the part that run uses and keep the record with the run. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md), [PR #1 source map](docs/superpowers/research/2026-10-24-pr1-digest.md).

**Dashboard and replay.** PR #1/#4's dependency-free server, feed and replay page watch, launch and steer runs. It is not a lesson and is not installed. *Reopens when* a live run needs operator control that the trace and `/mellum last` cannot show, or a lesson asks the learner to replay a turn. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md), [Flow triage](docs/superpowers/research/2026-10-24-flow-triage.md).

**Content-tool-call assist.** PR #2's extension promotes a tool call the model emitted inside text content to a real call, gated on known tool names. It is unit-tested but not ladder-measured, and PR #1 carries the same extension. *Reopens when* a suite or ladder run records a stall where the model emits a valid call in text and never reaches the tool field. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md), [PR digest](docs/superpowers/research/2026-10-20-pr-digest.md).

**Experimental agent extensions.** Plan, surgical, quality, NCM, loop and knowledge are PR #4 extensions with unit tests, not ladder results. Context, rethink, files and vision already route to INT.3 candidates; this entry is the remainder. *Reopens when* a screen or a Flow phase needs one extension and has a record that distinguishes it from the Baseline Worker; do not install the group speculatively. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md), [follow-up digest](docs/superpowers/research/2026-10-21-andre-follow-up-digest.md).

**Tier-1 contract test.** The PR #1 structural gate checks that routes exist; it is not the behavioral examiner Flow needs. *Reopens when* the INT.2 spec needs a cheap structural pre-check before the frozen behavioral gate, and a Flow run shows the examiner alone is too slow or too broad. [source map](docs/superpowers/research/2026-10-24-pr1-digest.md), [Flow triage](docs/superpowers/research/2026-10-24-flow-triage.md).

**Andre's context and input lessons.** Lessons #15–#20 in the track index — rungs 10–12, context search, skeptical rethink, documents/images, live control and next-concept verify — are candidates, not feature cycles. #16–#20 are INT.3 workflow candidates; #15 remains a lesson candidate. They need LC.5's written consent and a recorded screen for the extension each describes; several may be dropped. *Reopens when* LC.5 closes and one candidate has a record that supports a six-step page. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md#lesson-map), [re-plan](docs/superpowers/research/2026-10-24-curriculum-replan.md).

**Pathologies page.** A reference in `learn/` of the ways small models fail:
announce-and-stop, false success, test-command thrash, a bent project, long
runs, servers, settings drift, empty finals, loops, writing outside the
layout, a test edited to pass, a lost phase id. Each gets the record that
shows it and the guard, fact or spec shape that answers it. `learn` already
counts seven of these from run records; the page adds the ladder's and links
`evals/`, so a lesson links one pathology instead of restating it.
*Reopens when* the ditch lesson names more than the page covers, or a second
lesson needs the same explanation. Taken as LC.7A on 2026-10-21; the entry stays until it lands.

**Glossary of the eval terms.** One page that fixes the measurement vocabulary —
session, prompt, turn, suite, rung, arm, screen, reference run — so lessons,
records and the harness use the same words. `learn/glossary.md` already defines
the Learning Center's terms; this one covers the eval terms and links back.
Session is the unit: one isolated Pi context and workspace, fed one or more
prompts, with one trace. *Reopens when* a record or lesson uses an eval term the
glossary lacks, or two documents use one word for different things.

**Reject a gate test that cannot pass.** A frozen gate test can fail every
correct app because the test itself is broken: Bronze's gate called
`inspect.getfile` on a FastAPI instance (`TypeError` inside the test), and the
model got through only by monkeypatching `inspect` in `app.py`
([flow record](docs/superpowers/research/2026-10-29-vllm-flow.md)). The
redirect-following client, the one instance seen twice, is fixed by
`noFollowRedirects`. The general guarantee needs a design: before the build, a
broken test and a missing app both error, so a dry run must tell an error
raised in the test's own frames from one raised in app code or an import of a
module not yet built. The 2026-10-29 rerun added a second shape: an
assertion that contradicts the test's own setup (four audit-worthy calls, three
entries expected), which raises nothing. *Reopens when* a design can flag
either shape without the reference app, or a third flow run hits one.

**A unit that shapes the task in a session.** Two lessons left the track on
2026-10-29 because their remedy was a harness flag, not a unit: one spec file
per phase (`--specs split`) and one brief per phase instead of one joined
brief (leaving out `--single-prompt`). Their evidence is in
[the note](docs/superpowers/research/2026-10-29-lessons-left-the-track.md):
stepped sessions produced projects the checks could open where one-brief
sessions did not, and per-phase Acceptance lists mattered more than the file
layout. *Reopens when* a remedy unit can shape the task inside a Pi session
(feeding phases one at a time, or pointing each at its own spec), so a lesson
could show the FAIL turning into a PASS.

**The handoff block as a unit.** `collapseHandoffs` in
`extensions/mellum-worker.ts` replaces a closed span's messages with one
handoff block, so a parent does not re-pay a child's transcript on every
request. The lesson that taught it left the track on 2026-10-29: it is not a
unit and has no arm, since the delegated child was retired
([note](docs/superpowers/research/2026-10-29-lessons-left-the-track.md)).
*Reopens when* the handoff block is a remedy unit and a challenge shows a
session that fails on context without it and passes with it.
