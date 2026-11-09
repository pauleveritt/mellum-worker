# Backlog: mellum-worker

Deferred work. Read [`ROADMAP.md`](ROADMAP.md) for what is in flight.

Every entry states a reopen condition; an entry over 1,200 characters owes a
research doc and shrinks to a summary, a link, and its reopen condition.
Resolved entries are removed once their outcome is recorded in a feature-cycle
row or a research doc that the row links. Cite entries by heading anchor,
never by line number.

Reopen conditions, not promises.

**Reconcile the budget proxy against the server log.** F.5's proxy counts what
passes through it; a session that calls llama-server directly (a `curl` to
:8001 from its own bash) is not counted. lc40's floor caught that by matching
the server log's generations against the proxy's requests (LC.39's "direct
server call" case). F.5 left it out to keep the port to one host's needs; the
F.5 smoke's proxy and trace counts agreed on every counted session.
*Reopens when* a counted session's server log shows more generations than its
proxy log, or before a claim rests on a budget a model could step around.

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
deadline is next changed. 2026-11-07: F.3's process `wall` is timed on the same clock.

**Final reply omits moves and pre-existing work.** Recorded forms: a reply
silent about `rm tests/test_hello.py`; a reply claiming to have created files
a previous run left behind (`files: []`, one passing command); dead code and
an environment mutated to make a named command pass. The completion fact
makes "exits 0" the goal. The handoff and the Worker's parent test run are
the measured answers; schema-2 records (M.5) make the gap countable.
*Reopens when* records show two or more runs whose final reply claims success
with `filesMissingAtEnd` non-empty or `lastCommand` not `ok`.

**Empty-final nudge misses announce-and-stop turns.** The guard nudges only
when a turn ends with no text. The A17 rung 5 miss ended with "Now let's run
the tests again." and no tool call: the turn had text, so no nudge fired and
the run stopped unfinished. A check for a final turn that announces an action
without making a tool call would catch it, but it is a guard change on a
single observed miss in 30 Mode runs (A14, A17). *Reopens when* a second
announce-and-stop miss is recorded in a ladder phase or a run record.

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

**Ollama backend (was M.4).** GGUF weights, a Modelfile, a tool-call check,
provider templates for both hosts and a ladder rerun;
[`docs/backends/ollama.md`](docs/backends/ollama.md) lists what a port needs.
Only oMLX has been run. *Reopens when* a machine without Apple Silicon is on
hand to run the ladder against it. Restored 2026-10-20: LC.2 chose llama.cpp,
so this entry is not taken and its condition still stands.

**Versioned assessments (was M.7D).** Four independent dimensions (behavior,
verification, completion, report support) as a sidecar beside each run's
`run.json`, originals preserved;
[approved spec](docs/superpowers/specs/2026-10-11-m7d-versioned-assessment-design.md),
[superseded plan](docs/superpowers/plans/archive/2026-10-11-m7d-versioned-assessment.md).
Retired on 2026-10-13 as instrument work the current checks already cover
([triage](docs/superpowers/research/2026-10-13-roadmap-triage.md)). *Reopens when* a decision is blocked because two arms tie
on pass/fail but differ in verification or report, and the existing `check`
fields cannot show it.

**Fresh context at a send-back.** Fable's trace analysis locates 228,160 of
Base's proxy/trace token gap after first settle, about 21% of total charged
output. Removing that charge is a counterfactual, not a measured saving or a
prediction of a new median. Resetting context can increase rereading, reasoning
and mistakes; the earlier replayed-thinking ablation raised output by 73%.
Tool-output trimming is a separate intervention. Existing server-control and
brief-reasoning candidates come first
([review](docs/superpowers/research/2026-11-09-phase-worker-review.md)).
*Reopens when* a corrected, bounded phase trial still shows compaction dominating
cost after the applicable existing candidates are screened; compare one reset
policy against corrected Base with identical acceptance and all-attempt costs.

**Stall handlers judged on stalls.** Bounded commands recorded 0/122 stalls;
plain Vanilla 25/130 across reboot batches. These pooled totals are descriptive;
R.1 step three's matched 0/24 versus 4/24 did not meet its quality-only rule.
Retain bounded commands in the explicit phase candidate; F.8 owns its default
clamp fix. *Reopens when* phase traces justify a handler comparison: fix stall,
strict-quality and cost rules before a deciding run, with n justified by the
question. R.1b first screens the relevant existing candidate. A dormant hook
does not establish uselessness; shown-test/foreground stalled on log-following
in 5/24. [Census, pairing and limits](docs/superpowers/research/2026-11-09-phase-worker-review/stalls.md).

**`check/compile-import` needs a failure to guard.** R.1's Screen 2 could not
judge it at n = 3: it never acted, as no write failed to compile or import in three sessions, and a
`SyntaxError` showed in 1 of Screen 1's 15. *Reopens when* a tier's traces
show a compile or import failure in 2 or more of 12 sessions.

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
From Paul's pitch to Andre (2026-10-20). *Reopens when* Satyrn Education is ready to host the
lessons (the Learning Center phase is archived).

**Model-parameter impact on eval results.** What temperature, `top_p`, `top_k`
and context do to rung scores is unmeasured; the lesson that teaches a setting
needs that evidence, and the settings come from a checked-in project file so an
arm can differ by one value ([spec](docs/superpowers/specs/2026-10-20-learning-center-design.md)
§12). *Reopens when* an R cycle needs a sampling setting
and the harness runs the suite twice with one parameter changed.

**Dashboard and replay.** PR #1/#4's dependency-free server, feed and replay page watch, launch and steer runs. Removed in F.1 (nothing loaded it); restore with `git checkout 63b6563 -- dashboard extensions/mellum-feed.ts extensions/mellum-replay.ts extensions/mellum-control.ts`. *Reopens when* a live run needs operator control that the trace and `/mellum last` cannot show, or a lesson asks the learner to replay a turn. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md), [Flow triage](docs/superpowers/research/2026-10-24-flow-triage.md).

**Content-tool-call assist.** PR #2's extension promotes a tool call the model emitted inside text content to a real call, gated on known tool names. Removed in F.1 (nothing loaded it); restore with `git checkout 63b6563 -- extensions/content-tool-call-assist scripts/patch-pi.sh`. A `message_end` handler could do the same in-process. *Reopens when* a suite or ladder run records a stall where the model emits a valid call in text and never reaches the tool field. [harvest](docs/superpowers/research/2026-10-24-pr-harvest-index.md), [PR digest](docs/superpowers/research/2026-10-20-pr-digest.md).

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
(feeding phases one at a time, or pointing each at its own spec), so an R cycle
can measure it.

**Hard's status label and ID checks still use Medium's original predicate.** F.7 corrected Medium's
rejection of `Status: Open` and added a direct-and-route ID check, keeping Hard out of scope. Hard's
roadmap has the same wording and its hidden Phase 4 file is the same as Medium's was, so it shares
the false failure and the coverage hole ([note](docs/superpowers/research/2026-11-09-f7-qualify-acceptance.md)).
*Reopens when* R.3 is scheduled, or a Hard run misses a resolve or reopen check.

**Two hidden checks can still fail a valid build.** F.7 held Medium's hidden grader to its two
repairs. Its review found that `_post_forms` compares a form action exactly, so a `url_for` action
rendering `http://testserver/...` fails on Medium and on Easy's `f7-roadmap` bundle, while the
mediated tests accept it; and the board heading must equal `Complaints Board` exactly, so
`<h1>Complaints Board <small>today</small></h1>` fails. Fix under a new grader identity.
**2026-11-09, F.8:** the exact heading check is also in Easy's `f7-roadmap` Phase 2, so R.1a can meet it.
*Reopens when* R.1a is about to start, R.2 grades Medium Phase 3 or 4, Easy's bundle is first used on
Phase 3 or later, or a run misses one of these checks on a build that meets its roadmap.

**Session cleanup has not run on Linux.** `stopSessionProcesses` finds what a session left running by
reading process environments with `ps axeww`; F.8 kept it and its tests have run only on macOS, so the
review's "exercise cleanup on Linux" is still open ([F.8 note](docs/superpowers/research/2026-11-09-f8-phase-boundary.md)).
No Docker. *Reopens when* this branch is pushed and CI runs on `ubuntu-latest`, or a Linux pod is approved.
