# Glossary

Terms are linked on their first occurrence in each page by
[`zensical-glossary`](https://pypi.org/project/zensical-glossary/). The source
of truth is this page; do not hand-link a term in prose.

![A small robot leafing through a large open dictionary on a reading stand](assets/illustrations/glossary.webp){ .illustration }

## The course

### Learning Center

The whole Zensical site under `learn/`.

### Track

A group of lessons with a recommended order: Getting started and Lessons.

### Lesson

One page that teaches one thing. Getting started steps build on each other;
a findings lesson stands alone and lists its prerequisites.

### Six-step template

Problem → Eval case → Evidence of the problem → Solution → Validation →
Interpretation. Every findings lesson uses it.

### Interpretation

The closing narrative of a lesson: what the evidence means, how far its
badges let you trust it, and what is still open.

### Challenge

<!-- zensical-glossary-aliases: The Challenge, Easy, Medium, Hard, Tier -->
The three levels learners attempt to test what they have learnt: Easy (one
prompt, 13 hidden checks), Medium (four prompts, 18 checks) and Hard (eleven
prompts, 34 checks). Each level is a **tier**. They are the eval suites `easy`,
`medium` and `hard`; [The Challenge](challenge/index.md) explains how to attempt
them.

### Phase

The container a set of feature cycles runs in: the Learning Center (`LC`), and
historically the `M` series. A phase has no plan of its own. Not the same as a
suite phase, which is one step of a multi-phase eval task such as the hard
suite's seven.

### Feature cycle

One roadmap row inside a phase, named `LC.13A`. It runs the SDD cycle (
brainstorm, spec, plan, execute, review/close) and delivers one lesson, or,
when its Ships cell says so, housekeeping or infrastructure. "Phase" was the
older name for a row and means the same thing wherever it survives in a
record.

## Evidence and badges

### Badge

A label on each of steps 1–5 saying what the step rests on: `reference-run`,
`cited`, `screen`, or `conjecture`.

### Screen

A badge for a few targeted runs, or one observation, that is not a rate. A
screen can show that a problem exists; it cannot establish a remedy’s effect.

### Cited

A badge for an existing oMLX or mlx-lm record in `evals/` or a research
note. It is stronger than a screen and weaker than a `reference-run`.

### Reference-run

A preregistered run on llama.cpp, made for a lesson, on the suites the course
teaches. Earned with a preregistration written before the run, the record in
`docs/superpowers/research/`, and raw evidence in a `research-*` release.

### Conjecture

A badge for no run: reasoning, design or unit tests only.

### Pathology

A way a small model has been observed to fail on an agentic task, recorded with
the run that shows it and the shape that answers it. [The Pathologies
page](pathologies.md) keeps the list; an entry without an observation behind it
is a hypothesis, not a pathology.

## Experiments and arms

### Baseline lesson

Until 2026-10-29, the n=3 comparison of Vanilla Pi and the Baseline Worker on
easy, medium and hard. S0 Start Here now teaches reading
Vanilla Pi's failures and naming what went wrong; the worker is a preset, not a lesson.

### Mellum mode

The state `/mellum on` switches on and `/mellum off` switches off. While it is
on, the session's model is Mellum, and every request leaves out the turns from
before mode began, so Mellum sees only its own task. The worker also counts the
span's requests, tool calls and output tokens. Turning it off restores the
previous model and writes the span's run record. A headless run turns it on at
session start with `MELLUM_MODE=1`, which is what the `worker` arm sets. Mode
changes no prompt, tool or guard; remedy units do that.

### Thin worker

The `/mellum` worker with Mellum mode on and nothing else: the command tool and
the mode machinery. It bundles nothing: no prompt swap, no tool narrowing, no
facts, no guards; those are remedy units. The `worker` arm, and what
`/challenge <tier>` runs before you switch any unit on.

### Base stack

Base for short: the thin worker plus the few remedy units that give later
remedies a fair chance, such as a stall handler, so a session is not lost before
the remedy under test can act (`--arm worker --remedy preset:base`). The units
are earned in R.1, each by beating plain Vanilla, and plain Vanilla stays in the
batch as the anchor. Not the Baseline Worker, the old bundle.

### Baseline Worker

The worker as it was until LC.29 (2026-10-31): Mellum mode plus a bundled
prompt, tool narrowing, project facts and guards. Records, lessons and
scoreboard rows from before then mean this bundle. The bundle now lives as
`preset:baseline-worker`, so today's Baseline Worker is the thin worker plus that
preset.

### Vanilla Pi

<!-- zensical-glossary-aliases: Baseline Pi, plain Pi -->
Pi with no worker extension and no remedies: Pi’s base system prompt, the
built-in tools and no worker guards or facts. The `vanilla` arm, the floor, and
what `/challenge <tier>:vanilla` runs. Not the `bare` arm, which loads the
worker extension with mode off.

### Arm

One configuration in an experiment. The arms are `vanilla` (no worker
extension, the floor), `bare` (the worker extension loaded but mode off; it
sends Vanilla's requests, but it is not Vanilla), `worker` (the thin worker,
Mellum mode on) and `strip-thinking`. A harness run with no `--arm` is `bare`,
so a counted run names its arm. To remove one remediation you drop a
`--remedy` unit from the stack — that is the ablation now, not a per-arm knob.

### Floor

The simplest arm: Vanilla Pi with no worker extension and no remedies — the
baseline every remedy is measured against. The `vanilla` arm.

Also the roadmap's first phase (F): the floor plus the worker as a command tool that
adds nothing by default, so `bare` and `worker` send Pi's own tools and no hidden prompt
text. Every later unit's effect can then be credited to that unit.

### Enforcement

<!-- zensical-glossary-aliases: persuasion -->
A guarantee made through a Pi extension hook — a gate that refuses, a check that runs, a
payload that is exactly what the command line names — as opposed to persuasion, prompt
text that asks the model to behave. Persuasion has a role on top of a bounded worker;
enforcement is what bounds it. Budget guardrails (turns, context size, time) are enforced too.

### Ablation

A comparison that drops one unit from a `--remedy` stack to measure that unit.
An ablation measures the removed part; it is not a lesson module. (The old
per-arm ablations went with the worker's bundle.)

### Remedy

A change that corrects one pathology. Each remedy is a remedy unit, taught by
one lesson. The worker bundles none of them; a tier's remedies are a preset of
units switched on with `--remedy`.

### Remedy unit

One remedy in one file under `remedies/<kind>/`: a guard, a nudge, a context
change, a check or one of our tools. It installs one behaviour on Pi's hooks
and nothing else, and exports a `meta` record (the pathology, what it does,
its lesson, its evidence) that the remedies list is generated from. Load it
with `--remedy <kind>/<name>`.

### Preset

A named list of remedy units, loaded with `--remedy preset:<name>`.
Each tier's preset is the measured stack for that tier, built on the one
before it. R.1 measured `base` and `easy` against Vanilla Pi on Easy's 13
checks and left both empty: no unit won within the 20% budget limit.
`medium` and `hard` hold four units carried from before the oracle repair;
treat them as placeholders until R.2 and R.3 measure them. `preset:baseline-worker` is the explicit set of units that
reconstructs the worker's old, pre-decoupling bundle.

### Before and after

The two states every lesson shows of one command. Before is everything the
tier has added up to this lesson, written as one `--remedy` line; after adds
this lesson's one unit.

### Lesson check

A lesson's test: its own small challenge fails with the before line and passes
with the after line, at a preregistered n. A passing check also confirms the
pathology on the host it ran on.

### Tool

A capability the model can call. Pi enables four by default — `read`, `bash`,
`edit`, `write` — with `find`, `grep`, `ls`, `glob` and `codemode` in the
registry but off unless switched on; our tool units add `lookup` and others. A
remedy changes behaviour; a tool adds a capability.

### Nudge

A message a nudge unit sends after a turn ends without text or a tool call,
asking the model to continue. `nudge/empty-turn` allows three per run.

### Empty-final nudge

The specific guard for an empty final turn: `agent_before_settle` sees no
text and no tool call and returns `continue: true` with a restatement of the
completion fact, up to three times.

### Loop breaker

The guard that blocks the next identical tool call after five repeats with
nothing changed in between. An edit, write or bash call clears the memory.

### Guard

A function wired to an event that observes a tool call or a turn and decides
whether to block it or ask for one more request. The loop breaker and the
empty-final nudge are guards; they are code, not metadata.

### Stall handler

A remedy unit that keeps a command which never returns, such as a server started
in the foreground or a `tail -f`, from holding the session until the stall
cutoff: `tool/bounded-commands` bounds every bash call, and the foreground-server
and log-follow guards refuse the command before it runs.

### Settle check

A check that runs when the model tries to finish (`agent_before_settle`) and, while
it is red, sends the model back with a message instead of letting the session
settle. Each one adds its message to the earlier ones, and runs its command under
a timeout that stops the whole process group.

### Mediated test

<!-- zensical-glossary-aliases: mediated tests -->
An acceptance test the model did not write: written from the spec by whoever hands
the work over, shown to the model once per task, and rerun from a frozen copy
outside the project before the model may finish. Editing or deleting the copy the
model saw changes nothing. The `check/mediated-test` unit; a suite's tests live in
`mediated/`. Its two halves are also units of their own: `check/mediated-test-show`
only shows the test, and `check/mediated-test-settle` only reruns it at settle.

### Held pod

One rented GPU machine kept running for a whole batch, so its weights and build are
set up once. Its numbers carry its own host card and do not pool with another
machine's.

### Session user

The unprivileged account a held pod runs each session as. It owns the session's
workspace and nothing else, and cannot read the checkout, the grader or the
acceptance tests it is about to be judged on.

### Compile/import check

The `check/compile-import` unit: a `.py` write that does not compile comes back as
a failed write, and at settle every module the session wrote must import.

### Strip thinking

Removing earlier assistant reasoning from the payload the worker sends, so the
next request cannot see what the model thought before. Off by default: on this
backend the prefix cache absorbs repeated reasoning, and removing it made runs
60% slower (A12). The worker's `MELLUM_STRIP_THINKING=1` opens the seam so the
claim can be measured, and the harness arm is `--arm strip-thinking`.

### Spec variant

An alternative layout of a suite's project and the prompts that go with it,
selected with `--specs` and recorded in the run as `specs`. It changes how the
same requirements are laid out (one joined `specs/roadmap.md` against one file
per phase) so an arm can hold everything else fixed.

### Greedy

Decoding with `temperature 0`, `top_p 1`, `top_k 0` and a fixed seed. The
llama.cpp reference run used greedy; the suite baseline used sampled values.

### Sampled

Decoding with a temperature above zero. The suite runs use
`temperature 1.0`, `top_p 0.95`, `top_k 20`, the values in the private Pi
profile.

## Suites and measurement

### Mini harness

The small eval harness learners build in Getting started step 3, kept in
`learn/code/`. It is not the ladder.

### Ladder

The staged eval rig in `ladder/`: it runs the model through rungs of rising
difficulty and records the pass rate at each. The measured numbers come from
here.

### Rung

One stage of the ladder — a single task at a fixed difficulty the model is
scored on.

### Eval suite

A project under `learn/code/suites/`: a base project, the constitution
(mission, tech stack, roadmap, `AGENTS.md`), ordered prompts, a hidden grader
and expected test IDs.

### Session

One run of one suite: one workspace, one trace and one score. `--repeat 3`
means three sessions, and every score line states its n.

### Grader

The hidden tests run externally against disposable application copies after the
model exits, under trusted dependencies and pytest configuration.

### Grader identity

The selected assertion revision, digest of its trusted inputs, and execution
policy recorded with a new score. Historical briefs and grader revisions are
separate inputs; a record without this identity has unknown grader provenance.

### Strict pass

A run that passes the independent hidden checks, the project's required tests
with the supplied tests preserved, and the quality gates. Passing the hidden
checks alone is a full pass, not necessarily a strict pass.

### Cost per strict pass

The total cost of every attempt divided by the number of strict passes, including
failed, retried and budget-ended attempts in the cost. Name the unit: charged
output tokens, requests, time or money. Itemise censored spend separately and
retain it in total economic cost; keep censored quality results apart.
Zero strict passes gives no finite empirical ratio. This metric needs a success
rate and per-attempt spending limit beside it.

### Accepted phase

A requested roadmap phase whose current acceptance, prior-phase regression
checks, supplied-test integrity and quality checks have passed under trusted
verification. Its checkpoint can seed the next requested phase. This is the
target workflow; a model's final message alone does not establish acceptance.

### Expected IDs

The test IDs that must have successful structured pytest outcomes for a suite to
pass. Missing, skipped and uncollected tests cannot silently pass.

### Canary

A marker in `grader/` that shows the model touched the grader. A contaminated
session is not a pass.

### Qualification

The check that a suite’s grader separates `known-good` from `known-broken`:
the first must pass and the second must fail.

### Turns

Model replies that came back in a session: the assistant messages in the trace
that did not end in an error or abort. The table’s `Turns` is their mean over n.

### Requests

Every request the harness’s Pi sent the model, counted from the trace’s
`provider_request` rows. A retried, errored or deadline-killed request is a
request but not a turn, so requests can exceed turns.

### Failed checks

Expected test IDs that did not appear as `PASSED` in the grader run. They are
not the same as failed sessions. A run records them by name and groups them by
grader module, so a suite whose graders are one file per phase reports which
phase's checks are missing, not only how many.

### Checks did not run

A run whose hidden checks never executed: pytest stopped on a collection error,
usually because the workspace lacks a module the graders import, so every
expected ID counts as missing. The record carries `checks_ran: false` beside the
count, so a table cannot read it as the worker failing every check. The session
still fails; it just says why.

### Wall

Seconds the session’s Pi processes ran, measured by the harness around each
process (`execution.json`), not read from trace timestamps, which stop at a
hang. It is a suite total; divide by the number of prompts before comparing
suites of different length.

### Session completion

How a session ended, apart from how good its work is: `settled` (Pi exited
cleanly), `stalled`, `budget` (it spent its session budget), `wall_safety` (the
hang-guard ended it; a censored run), `deadline` (an explicit `--deadline` ended
it) or `error` (a non-zero exit or a last reply that errored). A run record’s
`completion` field.

### Session budget

The requests and output tokens one session may spend, set per tier in the
suite’s `budget.json` (Easy: 64 requests, 32,000 output tokens) and enforced by
a proxy between Pi and llama-server, which answers 429 once either is spent. A
session that spends it ends as `budget` and counts: it is graded on what it
built. `run.json` records the limits and what was spent.

### Censored run

A run the hang-guard (`wall_safety`, 1,200 s) ended. Wall time depends on the
host, so such a run is reported on its own line and never averaged in with the
rest; `run.json` says `censored: true`.

### Host card

The record `learn/code/conformance.py` writes after checking the live model
server against the pin card (`learn/code/host/pins.json`): its build, weights,
flags and slots, capacity, the tool-call protocol, stability, numerics (Metal
against CPU on the same build, within 1%) and the tool versions. A counted run
needs a card that passed, for the server that is live.

### Counted run

A harness run given `--host-card`: the host gate checked the card against the
live server before any session started, and `run.json` says `counted: true`. A
run without a card still runs (a lesson, `/challenge`) and says `counted: false`;
only counted runs back a claim.

### Output tokens

The sum of the model’s output tokens in a session, from the trace usage.

## Pi and agents

### Pi

The coding agent this course runs the model inside: it holds the system prompt,
the tools and the loop, and the worker is one extension loaded into it. From
earendil-works.

### Pi extension

A TypeScript module exporting a default factory that registers commands,
tools or event handlers inside the Pi process.

### Project trust

Pi's decision on whether to load a folder's own resources: `.pi/extensions`,
project settings, skills and prompts. Pi asks at startup, and `/trust` saves
the decision for later Pi processes. It decides what loads, not what a tool
call can reach; `AGENTS.md` loads either way.

### Hook

A point where an extension can observe or change a run. `pi.on` registers
handlers for these points.

### Event

A named lifecycle occurrence such as `before_provider_request`, `tool_call` or
`agent_before_settle`.

### Callback

A handler registered for an event. Its return value is part of the event’s
contract: it may block a tool, replace a payload or request a continuation.

### Main agent

The model and session holding the plan. In this center’s local lessons it is
also Mellum; that isolates the worker role, not what a large parent gains.

### Parent model

The model that owns the session before `/mellum` runs and receives the
handoff afterward. Also called the main agent.

### Handoff block

The one message the parent model receives for a finished worker span, in place
of the worker's every read, edit and command: a summary line, the files
written, the commands run, the last output, and the worker's reply. Produced by
the `delegate/collapse-handoffs` remedy.

## AI terms

### Agent

A system that uses a model to choose and carry out actions toward a goal.

### Agent loop

The repeated cycle of observing, deciding, acting, and checking results.

### API

An interface that lets software communicate with a model or another service.

### Completion

The output generated by a model.

### Context

All the information supplied to the model for a response.

### Context window

The maximum amount of information a model can handle in one interaction, measured in tokens.

### Embedding

A numerical representation that captures useful features and relationships in data.

### Eval

Evaluation, or eval: a test used to measure a model’s or agent’s quality, accuracy, or behavior.

### Fine-tuning

Additional training that adjusts a model’s weights for particular tasks, styles, or behaviors.

### Grounding

Connecting a response to specific evidence or data.

### Hallucination

An incorrect or invented output presented as though it were reliable.

### Harness

The software that calls the model, supplies context, executes tools, and manages permissions.

### Inference

Running a trained model to generate an output.

### Latency

The time it takes to receive a response.

### LLM

Large language model: a model trained on large amounts of data to process and generate language.

### Agent memory

Information saved outside the model and retrieved for later use.

### Working memory

The model's own earlier reasoning, replayed in the request, that it uses to
keep a plan across tool calls. Removing it from the history makes the model
re-derive that plan.

### Multimodal

Able to process or generate more than one type of content, such as text, images, or audio.

### N-gram

A sequence of *n* neighboring items, usually words or tokens.

### Weights

Also called parameters: the learned numbers inside a model that shape its outputs.

### Pretraining

The initial broad training that builds a model’s general capabilities.

### Prompt

The input given to a model, including questions, instructions, or examples.

### RAG

Retrieval-augmented generation: retrieving relevant information and adding it to the model’s context before it answers.

### System instructions

Instructions that define the model’s role, boundaries, and behavior.

### Temperature

A setting that influences randomness when selecting output tokens.

### Token

A piece of text, such as a word, part of a word, or punctuation.

### Token ID

The number assigned to a token in a tokenizer’s vocabulary.

### Tokenizer

The system that converts text into token IDs and back again.

### Tool calling

A model producing a structured request for software to perform an action.

### Training

The process of adjusting a model’s weights using data.

### Vector

A list of numbers used to represent information mathematically.
