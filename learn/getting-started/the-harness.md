---
title: The Harness
time: 5 min read · 30 min to run
track: getting-started
position: 4
prerequisites: [getting-started/eval-suites]
authors: [Paul Everitt, Andre van Zuydam]
backends: [llamacpp]
---

# The Harness

Every Easy lesson ran one command and trusted the score it printed. Here you
build a small harness of your own, a fresh directory, one Pi run and a score,
to see what the provided one does for you.

!!! abstract "Overview"

    **Questions**

    - What does a harness do between "run the model" and "here is a score"?
    - What would a score mean if a run could see its tests, or reuse another run's files?

    **Objectives**

    - Build a mini harness: a fresh directory per run, Pi on a task, a score.
    - Name what the provided harness adds: isolation, a hidden grader, `run.json`, a stall cutoff.
    - Run the provided harness once, then several times, and read what it kept.

![A small robot working inside a glass test box while an arm outside holds a clipboard and stopwatch](../assets/illustrations/build-a-harness.webp){ .illustration }

## Problem

**Badge:** `conjecture`

A harness runs a model on a task and scores the result. You have used
`learn/code/harness.py` for every Easy lesson, and its score line was the
evidence each lesson read. A score only means something if the instrument
behind it is sound: if a run could see the tests it is graded on, reuse a
previous run's files, or pick up your own `~/.pi` settings, the same line
would print and mean nothing.

## Eval case

**Badge:** `conjecture`

Bronze, in `learn/code/suites/easy/`: a base AgentClinic project, one prompt
asking for phase 1, and the tests that check it. The prompt goes to `pi -p` as
the request; nothing else about the suite is shown to the model.

**Before:** the provided harness, `learn/code/harness.py`. **After:** your
mini harness, on the same task, with the same profile.

## Evidence of the problem

**Badge:** `screen`

[The ditch session](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-the-ditch-session.md) is a run with no harness: one session, n = 1,
in a directory nobody reset, with tests the model wrote itself and no bound on
time. Its report claimed four passing tests that were never run, and the
first attempt ran fifteen minutes and took Node's heap with it. Nothing about
that session could be repeated or compared.

## Solution

**Badge:** `conjecture`

This page builds the instrument that measures every remedy, so it adds
none. Its check is that your harness scores a right answer PASS and a wrong
one FAIL.

Three things make a score mean something:

- **A fresh directory.** The task is copied into a run's own workspace, so a
  previous run's files cannot help or hurt it.
- **A private profile.** The child gets `PI_CODING_AGENT_DIR` pointing at a
  copy of `learn/code/profile/`, plus `--no-extensions --no-skills
  --no-context-files --no-approve`, so your `~/.pi` and this repo's
  `AGENTS.md` stay out of it.
- **Hidden tests.** A task's tests are copied into the workspace only after
  the child has exited. Until then the model cannot read what it will be
  graded on.

Your mini harness is those three, in order. From the repo, with the server
running (Linux / macOS):

```bash
repo=$PWD; suite=$repo/learn/code/suites/easy
run=$(mktemp -d); mkdir "$run/workspace"
# 1. A fresh directory, with the task's starting files and a private profile.
cp -R "$suite/base/." "$run/workspace/"
cp -R "$repo/learn/code/profile" "$run/profile"
# 2. Run Pi on the task, in that directory, with nothing of yours loaded.
(cd "$run/workspace" && PI_CODING_AGENT_DIR="$run/profile" pi -p --no-approve \
  --no-extensions --no-skills --no-prompt-templates --no-themes --no-context-files \
  --provider llamacpp --model Mellum2.1-12B-A2.5B-Thinking "$(cat "$suite/prompts/01.md")")
# 3. Score it: the tests arrive only after Pi has exited.
cp -R "$suite/grader" "$run/workspace/grader_tests"
(cd "$run/workspace" && PYTHONPATH=. uv run --with pytest pytest -q grader_tests) \
  && echo "easy: PASS ($run)" || echo "easy: FAIL ($run)"
```

That is a harness. The provided one does the same three steps and then the
things a mini one leaves out:

- **A recorder.** It loads `record-pi.mjs` into the child, which writes
  `trace.jsonl`: requests, tool calls, tool errors and the final message.
- **A run record.** `run.json` keeps the result with what it rested on:
  `passed`, `checks_ran` (did the hidden checks even run, or did they fail to
  import?), the failed checks, `stalled`, the arm and remedies.
- **Bounds.** A deadline (600 seconds by default) ends a session, and
  `--stall SECONDS` ends one whose single tool call has run that long with no
  result, a foreground server. Your mini harness waits forever. When this
  lesson's own `--suite easy` ran bare in the 2026-10-29 local 6-bit MLX smoke
  ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-10-29-local-lessons-smoke/README.md)),
  the cutoff did exactly that: two of three sessions ended on a `uvicorn` call
  that never returned (see [M4](../lessons/medium/run-long-commands-safely.md)).
- **Clean-up and tamper checks.** It ends every process the session left
  behind, and marks a run whose grader files the model touched.
- **Several prompts, one session.** A task holds one prompt (`task.md`) or
  several (`prompts/01-*.md`, sorted by name). Several prompts run in **one
  session**: one workspace, one trace and one Pi session id, with the prompts
  sent in order. Scoring happens once, at the finish, never between prompts.

**What the runner sends.** The runner does not start llama.cpp.
`scripts/backend.py` owns the server; the runner copies `learn/code/profile`
into the run and points the child Pi at that private copy. The copy is
generated from `[tool.mellum]` in the root `pyproject.toml`, so these are the
values a run actually sends: `temperature 1.0`, `top_p 0.95`, `top_k 20`,
`max_tokens 16384`, with a `context 50000`.

| Layer | Setting | Value |
| --- | --- | --- |
| Server | context | 50000 (`n_ctx 50176` when measured) |
| Pi request | temperature | 1.0 |
| Pi request | top_p | 0.95 |
| Pi request | top_k | 20 |
| Pi request | max_tokens | 16384 |
| Pi request | context window | 50000 |

These are Pi's out-of-the-box sampled settings, not greedy decoding. The
llama.cpp reference run used a different, greedy block; the suite runs are
not that run.

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. The
mini harness above was run only with a stand-in for Pi on a toy suite: it
printed PASS for a correct answer and FAIL for a wrong one. It has not been
run against the model.

Check the provided harness the same way, by running it and reading what it
kept. `uv run learn/code/harness.py run --suite easy` runs one Bronze task and
prints a score line:

```text
easy: PASS (n=1; run /var/folders/...; 1 request, 3 tool calls, 0 tool errors)
```

`n=1` is one session: one workspace, one trace, one score. That is the
default, and it is an observation, not a rate. With `--repeat 3`, each repeat
starts from a fresh workspace; the lines are tagged `[1/3]` and the summary is
`easy: 3/3 sessions passed`. Two or three sessions are still a lead, not a
rate; [Eval suites and the telemetry](eval-suites.md) explains
why, and a rate needs a preregistered run with its arms and n fixed first.

The run directory keeps everything the score rested on:

- `prompt.txt`: exactly what the child was asked;
- `workspace/`: what it wrote, with the tests copied in once it exited;
- `profile/`: the private Pi profile used for this run;
- `trace.jsonl`: the recorder's rows: requests, tool calls, tool errors and
  the final message;
- `run.json`: the result and the record it rests on.

`PASS` means the tests passed. `FAIL` still leaves the run in place and prints
the test tail, so you can see whether the model wrote nothing, wrote the wrong
thing, or wrote something the tests could not import.

A suite may also ship a **spec variant**: the same project with its phased
requirements laid out another way. `--specs joined|split` runs the suite with
that variant's prompts and workspace, and the run record carries `specs`, so
two arms are told apart by the record rather than by memory. Only a suite with
`spec-variants/` has them; `medium` (Silver) ships `joined`, whose briefs
point at one `specs/roadmap.md`, and `split`, whose briefs each point at their
own `specs/phase-4.md`. Without the flag the suite runs exactly as shipped.

## Interpretation

The weakest badge is `conjecture`: the guarantees are design, checked by the
harness's unit tests, not a before-and-after run. Your mini harness is a
teaching tool; `learn/code/harness.py` is the measured instrument, and findings
lessons cite the suites. What transfers is the question to ask of any score:
was the directory fresh, were the tests hidden, and what did the run keep?

The numbers you produce here are for you while you learn. They are not
preregistered and they run on one machine; a lesson's `reference-run` is the
preregistered version of the same run, and the reference run on llama.cpp is
a separate phase.

### Run it yourself

The server from [Base Pi on llama.cpp](base-pi-on-llamacpp.md)
is needed once; then the provided harness, its argv only, once, several times,
and with a spec variant:

```bash
uv run scripts/backend.py start
uv run learn/code/harness.py run --suite easy --dry-run
uv run learn/code/harness.py run --suite easy
uv run learn/code/harness.py run --suite easy --repeat 3
uv run learn/code/harness.py run --suite medium --specs split --repeat 3
```

Then run your mini harness from the Solution on the same task, and compare
its run directory with the provided one's.

!!! success "Key points"

    - A harness is three steps: a fresh directory, the model run in it, and a score from tests it could not see.
    - The provided harness adds what a mini one leaves out: a trace, `run.json`, a deadline and a stall cutoff.
    - One session is an observation, not a rate; `--repeat` gives a lead, and a rate needs a preregistered run.
