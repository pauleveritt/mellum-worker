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

**The mediated test, cheaper.** An external, complete test, shown to the
worker and re-run at settle (`check/mediated-test`). 2026-11-08, R.1 (Easy,
counted, n = 24): 15 and 18 of 24 full passes against Vanilla's none, at 47
and 61 median requests against 21, so it lost on budget; 32 of 48 sessions
ended on budget, most after reaching 13/13
([R.1 note](docs/superpowers/research/2026-11-07-r1-easy-remedies.md)). The
earlier rung 9 plan and Andre's `--acceptance-test` are in
[`ARCHIVE.md`](ARCHIVE.md#the-m-series-closed-2026-10-20) and the
[digest](docs/superpowers/research/2026-10-20-pr-digest.md). *Reopens when* a
variant that stops at green, re-dispatches less, or tracks the oracle more
closely is ready for a preregistered Easy batch against Vanilla.

**Stall handlers judged on stalls.** In R.1 step three (n = 24) Vanilla stalled
in 4 sessions; `guard/foreground-server` and `tool/bounded-commands` in none.
Step one's stall rule would have admitted both, but step three judged only
quality, and they missed it
([table](evals/2026-11-07-r1-step-three/table.md)). *Reopens when* a cycle
builds a tier's Base (R.2's Medium, or Easy again): preregister a batch that
judges each handler on stalls at n = 24. Screen `guard/foreground-log-follow`
again too: Screen 1 dropped it at n = 3, and mediated+fg-server then stalled on
`tail -f` in 5 of 24.

**`check/compile-import` needs a failure to guard.** It never acted in R.1's
Screen 2: no write failed to compile or import in three sessions, and a
`SyntaxError` showed in 1 of Screen 1's 15. *Reopens when* a tier's traces
show a compile or import failure in 2 or more of 12 sessions.

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
