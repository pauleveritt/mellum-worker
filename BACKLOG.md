# Backlog: mellum-worker

Deferred work. Read [`ROADMAP.md`](ROADMAP.md) for what is in flight.

Every entry states a reopen condition; an entry over 1,200 characters owes a
research doc and shrinks to a summary, a link, and its reopen condition.
Resolved entries are removed once their outcome is recorded in a phase row or
a research doc that the row links. Cite entries by heading anchor, never by
line number.

Reopen conditions, not promises.

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

**Write-only guard: refuse writes outside the facts block's list.** Mode
forwards the `## Mellum` section's `Write only:` line as text; nothing
enforces it. On AgentClinic rungs 6–9 the text was enough: with the section
forwarded, 0/12 runs had a non-empty `outside_write_list`
([A19](docs/ladder/ablation-a19-facts-on/README.md)), against 8/12 with facts
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

**OpenCode port: measure it and record its runs (was M.3).** The OpenCode
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
hand to run the ladder against it.

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

**pi-subagents Worker: one-liners and an in-process child (were M.8, M.9).**
`async: false`, a re-dispatch line in the description and the intercom
opt-out ([A11](docs/ladder/ablation-a11-delegated-nointercom/README.md)); a
`mellum_worker(task)` tool through Pi's SDK
([cost note](docs/superpowers/research/2026-10-09-worker-cost-options.md) §2,
§3b). *Reopens when* M.12 does not retire the Pi Worker.

**Freeze-the-oracle exit gate.** Make "done" an external test the worker cannot
weaken, instead of its own final message. Promote the ladder's scorer checks —
`existing_tests_kept` (no existing test edited or removed; additions allowed)
and `outside_write_list` — into a runtime guard on the worker, and gate the
exit on an actual run of the frozen acceptance test with the failure
re-dispatched as the next "make this pass". M.11 supplies the external, complete
test but Excludes guard changes, so the unweakenable half is here
([note](docs/superpowers/research/2026-10-18-harness-exit-gate.md)).
*Reopens when* M.11's screen moves rung 9 and a trace shows a worker editing or
deleting a test to exit, or writing outside the allowed paths, on a run that
then scored as done.

**Benchmark a plain mlx_lm.server against oMLX, and sampling screens.** The
ladder now supports both (`--backend mlx-lm --base-url`, and
`--temperature`/`--top-p`; direct mode only), but no runs have been made. The
two servers cannot be made byte-identical — `thinking_budget`,
`max_tool_result_tokens` and penalty handling are oMLX server-only with no
mlx_lm.server equivalent — so an oMLX-vs-mlx-lm result is a harness finding
about servers, not a claim about the shipped worker; sampling sweeps are the
same, since the ladder is greedy by design ([sdd](docs/sdd.md)).
*Reopens when* someone runs a screen (a few rungs, a research note naming the
server's launch flags and n); a measured claim additionally needs a
preregistered run with the server differences pinned.
