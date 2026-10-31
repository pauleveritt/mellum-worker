# Learning Center design: an Andre/Paul site on small-model evidence

Date: 2026-10-20. Decided with Paul in chat (Superpowers brainstorming,
approved section by section). Inputs: Paul's Discord pitch to Andre van
Zuydam, the [PR digest](../research/2026-10-20-pr-digest.md), and these
choices: a local backend with re-run evidence, lessons published with
badges, a `learn/` directory, a mini harness first, a closing
Interpretation on every lesson, and the terms center, track and lesson.
Phases LC.1 onward in [`ROADMAP.md`](../../../ROADMAP.md) carry it out; the
first plan,
[LC.1](../plans/archive/2026-10-20-l1-learning-center-skeleton.md), shipped
the skeleton on 2026-10-20.

**2026-10-20, backend reversal.** The plan chose Ollama because a learner
need not own Apple Silicon, and the [Ollama port](../../backends/ollama.md)
stays the option for a machine without it. This machine runs llama.cpp, so
the Getting started track teaches that instead, and every Ollama reference
below reads llama.cpp. [llama.cpp is smoke-tested, not
measured](../../backends/llamacpp.md): one request round-tripped with tools
at 50k context on Q4_K_M (8.38 GB peak, 207 tok/s generation), no ladder
rung rerun, so its numbers are `screen` until LC.3 reruns them. Ollama
keeps its [backlog entry](../../../BACKLOG.md#ollama-backend-was-m4).

Not a measured change: the worker, prompt, extensions, guards and ladder
are untouched by this design. Evidence for lessons comes from runs that
later phases make and record in `evals/`.

## 1. Goals

- Walk a learner from base Pi on a local model to evidence-backed fixes for
  the problems small coding models have.
- Tell every finding the same way, so a learner can see what was measured
  and what was not.
- Turn this repo's history (Paul's phases M.1–M.7 and the A-series
  ablations) and Andre's PRs into lessons without overstating either.
- Credit the work as a collaboration and keep it portable: a later move to
  Satyrn Education should be a copy of the learner pages, not a rewrite.
  2026-10-20: originally "a copy of `learn/`"; the maintainer pages in
  `learn/project/` and the lesson code in `learn/code/` stay with this repo.

Non-goals: a reference manual for the worker (the README stays that), new
measured claims made by the site itself, PyCharm content (backlog), and
publishing SDD records as site pages.

## 2. Audience

Developers who want to run a small open coding model locally behind an
agent harness, on macOS, Linux or Windows. They know a terminal and Python
or Node. They do not need Apple Silicon to learn from the lessons: the
Getting started track is written against llama.cpp on this machine (Apple
Silicon, Metal), and the Ollama port on the backlog covers a machine
without it.

## 3. Glossary

These terms are fixed, and the site, this spec and the roadmap use no other
names for these units.

- **Learning Center**: the whole Zensical site under `learn/`.
- **Track**: a group of lessons with a recommended order. There are two:
  Getting started and Lessons.
- **Lesson**: one page that teaches one thing. Getting started lessons
  build on each other; a findings lesson stands alone and lists its
  prerequisites.
- **Six-step template**: Problem → Eval case → Evidence of the problem →
  Solution → Validation → Interpretation. Every findings lesson uses it.
- **Interpretation**: the closing narrative of a lesson: what the evidence
  means, how far its badges let you trust it, and what is still open.
- **Badge**: a label on each of steps 1–5 saying what the step rests on:
  `reference-run`, `cited`, `screen` or `conjecture` (section 6).
- **Reference run**: a preregistered ladder run on llama.cpp, recorded in
  `evals/`, made for a lesson.
- **Mini harness**: the small eval harness learners write in Getting
  started lesson 2, kept in `learn/code/`. It runs each task in an isolated
  directory through a private Pi profile and scores it with the task's
  tests. It is not the ladder.
- **Private profile**: a lesson-local Pi agent directory that
  `PI_CODING_AGENT_DIR` points at, holding the generated `models.json` and
  only the extensions that lesson needs. A run uses it from a temporary
  copy, so `~/.pi` is untouched and one run cannot inherit another's setup.
- **Lesson bundle**: the files a lesson needs under `learn/code/`: the
  shared profile directory, the lesson's overlay, task fixtures and any
  recorder.

## 4. Tracks

### Getting started (fixed order)

The learner clones `mellum-worker` and works in the checkout: the profile,
harness and fixtures are repo files, and every command is `uv run` from the
repo root.

2026-10-20: the first plan assumed a learner installed a backend by hand and
the site stood alone. The harness, the private profile and the settings file
are repo code, so the lessons are taught from a clone; a hosted learner
would revisit this, not LC.2.

1. **Base Pi on llama.cpp.** Install `uv`; the root `pyproject.toml`'s
   `requires-python` is what makes `uv` fetch an interpreter on a machine
   that has none, and lesson 1 explains that file. Install llama.cpp for the
   platform, then `uv run scripts/backend.py start`, which reads
   `[tool.mellum]` and pulls `Q4_K_M` through llama.cpp's `-hf`; `chat`
   proves the server. Then point `PI_CODING_AGENT_DIR` at
   `learn/code/profile/` and run `pi` with `--no-extensions --no-skills
   --no-context-files --no-approve`, so the learner's own `~/.pi` is neither
   read nor written, and get an answer. Phase LC.2, which also does the port
   checklist (GGUF, serve command, tool-call check, provider profile).
2. **The ditch.** One loose prompt to build AgentClinic, driven by hand in a
   session; its transcript shows the ways the model fails — a confident final
   reply over a project that does not run, an empty final, a test edited to
   pass, files written outside the layout. The lesson states the rule the
   rest of the track rests on: before fixing, get evidence. No SDD teaching;
   the pathologies are named and the reference page linked. Phase LC.7.
3. **Make a mini harness.** Write `learn/code/harness.py`: each task is
   copied into a fresh directory, handed to a child `pi` with the private
   profile, scored by the task's tests, and its telemetry kept. Run it on one
   easy task and read the score line. Phase LC.3, shipped; the ditch renumbers
   the page to lesson 3.
4. **A suite and the telemetry.** Add the medium and hard tasks, watch base
   Pi pass easy and struggle on hard, and read the runs: turns, tool calls,
   tool errors and the final reply. One session is one observation, so the
   suite states its n and the lesson says why a rate comes from the ladder.
   The harness is the suite runner —
   `uv run learn/code/harness.py suite easy|medium|hard` prints one score
   line per task and where its runs are — so lesson 1 needs no separate
   front door. Validation grades through `uvx` from here. Phase LC.3A; the
   llama.cpp reference ladder run is LC.3B.

5. **The worker extension.** What a Pi extension is, the `mellum-worker`
   extension, and `/mellum` to invoke it. On the same AgentClinic session it
   behaves like the ditch — no remedy is taught yet; it is the vehicle the
   findings lessons improve. Phase LC.9.

Each lesson lists what it produces, so the next can start from the last
one's result.

2026-10-20: the ditch is inserted as lesson 2, so the shipped harness and
suite pages become lessons 3 and 4; they are renumbered when the ditch lands,
and the phase rows keep what they shipped.

**Sessions and repeats (LC.6).** A session is one isolated Pi context and workspace,
fed one or more prompts; the suite scores once, at the finish. More than one
prompt is how a learner drives a multi-step task. `--repeat N` runs a task N
times (default 1), every line states its n, and the suite counts sessions
rather than estimating a rate. The suite lesson says so: one session is one
observation, and rates come from the ladder.

### Lessons

One track for every findings lesson, from Paul's phases and ablations and
from Andre's pull requests, one idea per lesson. Every lesson stands alone;
the track index gives a recommended order, and each lesson lists Getting
started as its prerequisite plus any lesson it builds on.

Paul's ten are mined from M.1–M.7 and the A-series in a digest like the PR
digest, written in phase LC.4 before any lesson. Andre's ten come from the
[PR digest](../research/2026-10-20-pr-digest.md) in phase LC.5, in the
proposed order for him to review: idea 9 (a clean negative result), then
1, 2, 6, 3, 4, 5, 7, 8, 10. They are gated on his consent (section 9).

## 5. Lesson template

### Front matter

Every lesson page starts with:

```yaml
---
title: The worker decides when it is done
track: lessons          # getting-started | lessons
position: 2             # recommended order within the track
prerequisites: [getting-started/harness]
authors: [Andre van Zuydam, Paul Everitt]
backends: [omlx, mlx-lm] # where the badged evidence ran; llama.cpp once re-run
---
```

`prerequisites` lists page paths without `.md`. `authors` is who did the
work the lesson tells, not who wrote the page. Getting started lessons use
the same front matter and need not follow the six steps.

### The six steps

Each findings lesson has six `##` sections in this order, with these
names:

1. **Problem**: what a small model does wrong, in one paragraph a learner
   can recognise from their own runs.
2. **Eval case**: the rung or task that reproduces it, and how it is
   scored, with a link to the code.
3. **Evidence of the problem**: the runs that show it, with n and backend.
4. **Solution**: the change, with a link to the commit or file.
5. **Validation**: what shows the change holds — the test suite and static
   analysis (`ruff`, `pyrefly`, and one complexity tool from LC.3) for a code
   change, the ladder runs for a setting, with the command and what it said.
6. **Interpretation**: a short narrative, no badge.

Steps 1–5 each open with one badge. A negative result keeps the template:
Validation shows the test, the analysis or the run that still fails.

2026-10-20: step 5 replaced "Evidence it worked" with Validation, a test
suite plus static analysis, because a lesson's fix is proved by what runs,
not by prose saying it helped. The template page and this spec changed
together; the step was named "Evidence it worked" when LC.1 shipped.

### Interpretation rules

- It names the weakest badge among steps 1–5 that its conclusion relies
  on, and states nothing stronger than that badge supports.
- It says which backend the evidence came from when that differs from the
  learner's (llama.cpp).
- It ends with what is still open: the run that would upgrade the weakest
  badge, or the question the evidence cannot answer.
- It is commentary: no new numbers appear in it.

## 6. Evidence badges

| badge | means | needs |
| --- | --- | --- |
| `reference-run` | a preregistered run on llama.cpp, made for this lesson | a record in `evals/`, a preregistration, raw evidence in a `research-*` release |
| `cited` | an existing record on oMLX or mlx-lm | a record in `evals/` or a research note on `main` |
| `screen` | a few targeted runs or one observation | a research note, or a PR note or commit message cited by name |
| `conjecture` | no run behind it | reasoning, design, unit tests only |

For steps 1, 2 and 4 the badge is the strongest evidence the statement
rests on; for steps 3 and 5 it is the strength of the evidence itself.

**Upgrading a badge.** Each lesson whose steps 3 or 5 are below
`reference-run` gets a roadmap item for the run. When the run lands, the
lesson's badge, numbers and Interpretation change in the same commit as
the record, with a dated line under the Interpretation saying what
changed. A run that weakens a claim downgrades the badge the same way. A
badge never changes without a linked record.

A badge is the first line of its section, written as **Badge:** followed by
the badge name in inline code, so it renders the same on GitHub and in
Zensical. The convention is defined once in `learn/about/evidence.md`;
styling it is later work and needs no change to lessons.

## 7. Site layout

```text
zensical.toml                 # [project] site_name, docs_dir = "learn", nav
learn/
  index.md                    # home: what the center is, where to start
  about/                      # the center explained (section 8)
  glossary.md
  credits.md
  lesson-template.md          # the six-step template, copyable
  getting-started/index.md    # + lesson pages from LC.2, LC.3
  lessons/index.md            # all findings lessons, one page each
  code/                       # lesson code, not published as pages
    profile/models.json       # generated from [tool.mellum]
    record-pi.mjs             # lesson recorder (LC.3)
    tasks/                    # easy (LC.3), medium and hard (LC.3A)
  project/                    # maintainer docs: how this project works
```

- `zensical.toml` sits at the repo root with `docs_dir = "learn"`
  (Zensical cannot use `.`). `site/` is the build output and is ignored by
  Git.
- `learn/code/` is excluded from pages with `exclude_docs`; lessons show
  its files with snippets.
- `learn/project/` is maintainer documentation, not a learner track; the
  Satyrn copy takes the learner pages only. `learn/code/profile/models.json`
  is generated from `[tool.mellum]`, and a test fails when the two disagree.
- Lessons link to `evals/` records, research notes and code through
  GitHub URLs on `main`, so SDD records stay unpublished and still render
  on GitHub (`docs/sdd.md`, "Docs are a presentation layer").
- Navigation is by track; each track's `index.md` lists its lessons in the
  recommended order with each lesson's weakest badge.

## 8. About the Learning Center

Four pages in `learn/about/` explain the center itself. They are written in
LC.1, before any lesson, and kept current as the center grows.

- **`index.md`, What this is**: what the center teaches, who it is for, how
  it grew out of mellum-worker and the ladder, and that it is a
  collaboration between Andre van Zuydam and Paul Everitt.
- **`how-to-read.md`, How to read a lesson**: tracks and their order,
  standalone lessons and prerequisites, the six steps, what an
  Interpretation is and is not, and a worked walk through one lesson.
- **`evidence.md`, Evidence and badges**: the four badges, what each needs,
  why a backend is named, how a badge is upgraded or downgraded, and why a
  `screen` is a lead and not a rate.
- **`contributing.md`, Contributing a lesson**: how a lesson is proposed
  (an idea in a digest first), reviewed (claims checked against linked
  records), and published; the consent rule for attributed lessons; how to
  write an Interpretation that stays within its badges.

## 9. Attribution and consent

- `learn/credits.md` says the Learning Center is "a collaboration between
  Andre van Zuydam and Paul Everitt" and mentions Tina4, Andre's project,
  whose developer skill supplied the `mellum-dev` coding principles
  (PR #1, `dd3a7c2`), with a link.
- Every lesson's `authors` names whose work it tells.
- **Consent gate.** No lesson attributed to Andre is published, and the site
  is not deployed publicly, until Andre says yes in writing (a PR comment or
  issue is enough; it is linked from LC.5's Status cell). Until then the
  site builds locally only. LC.1–LC.4 do not depend on his PRs. 2026-10-20:
  Andre consented in Discord (per Paul); a linkable quote is owed before an
  Andre-attributed lesson publishes.
- A lesson that cites an unmerged PR links the PR and the commit, not a
  branch, so the citation stays stable.

## 10. Phases

| phase | ships |
| --- | --- |
| LC.1 | `zensical.toml`, home, About pages, glossary, credits, track index pages, lesson template, badge convention; local build — shipped 2026-10-20 |
| LC.2 | Getting started lesson 1, lesson 1's toolchain, the root `pyproject.toml` and `scripts/backend.py` replacing the Justfile, the private profile, and the maintainer pages |
| LC.3 | Getting started lesson 2: the mini harness and its recorder, one easy task, the score line |
| LC.3A | Getting started lesson 3: the medium and hard tasks, the suite, telemetry, validation grading |
| LC.3B | The ladder takes a provider, base URL and model, and a rung-1 smoke drives llama.cpp |
| LC.3C | A preregistered llama.cpp reference run, recorded in `evals/` |
| LC.4 | A digest of Paul's phases, the track index, and one phase row per lesson |
| LC.5 | Andre's track: index and consent, adding one phase row per approved idea |
| LC.6 | The harness takes sessions with one or more prompts, `--repeat`, and n on every line |
| LC.7 | The ditch, and the harness and suite pages renumbered to lessons 3 and 4 |
| LC.7A | The Pathologies page, linked from the ditch |
| LC.8 | One worker: retire the pi-subagents Worker and rename Mode to Mellum Worker |
| LC.8A | Drop the OpenCode port and its skill phases |
| LC.9 | Lesson 5: a Pi extension, the `mellum-worker` extension, and `/mellum` |
| LC.10+ | One phase per findings lesson, in track order |

2026-10-20: the M series closed and its last two phases moved to the
backlog; its rows are archived in `ROADMAP-M.md`. PR #1 remains a candidate
for the mediated test, and the Andre track tells its story without deciding it.

## 11. Risks

- **llama.cpp numbers differ from oMLX.** Every badge names its backend; a
  `cited` oMLX number is never presented as what the learner will see. The
  reverse holds once LC.3 reruns the ladder: a llama.cpp number is not an
  oMLX claim.
- **Interpretation overreaches.** The rules in section 5 apply, and review
  checks each Interpretation against its weakest badge.
- **Re-runs pile up.** Badges, not gating: lessons publish with the badges
  they have, and runs are roadmap items.
- **Andre declines or changes scope.** The Andre track waits or is dropped; nothing
  else changes.
- **The mini harness drifts from the ladder.** It is a teaching tool;
  findings lessons cite the ladder only.
- **The learner's Pi setup leaks into a run.** Every lesson passes its own
  `PI_CODING_AGENT_DIR` and `--no-*` flags; the harness assembles a profile
  per run and prints where, so a run differs by task, not by install.
- **Zensical is young.** Pages are plain Markdown with front matter, so a
  move to another generator is cheap, and the learner pages are a copy.

## 12. Model settings, lesson profiles and validation

**Settings live in the project.** Temperature, `top_p`, `top_k`, `max_tokens`
and context live under `[tool.mellum]` in the root `pyproject.toml`, and
`scripts/backend.py` and the mini harness read them with `tomllib`. An eval
arm is the same run with one value changed, so a lesson can show the setting
beside its result. The Justfile that shipped on `main` on 2026-10-20
hardcoded temperature 1 and `top_p` 0.95; LC.2 retires it before either
reaches a release, and `docs/backends/llamacpp.md` records that.

**One generated profile.** `learn/code/profile/models.json` is written from
`[tool.mellum]` — provider, model, context, `max_tokens` and sampling
params — and a test fails when the committed file and the generator
disagree, so the server, `chat` and Pi read the same numbers. Nobody
hand-edits sampling in two places.

**Each lesson owns its Pi setup.** A lesson never reads or writes `~/.pi`:
it names a profile directory through `PI_CODING_AGENT_DIR` and launches Pi
with `--no-extensions --no-skills --no-prompt-templates --no-themes
--no-context-files --no-session --no-approve`, adding back only what the
lesson teaches. The harness assembles the profile in a fresh temporary
directory for every run, so runs differ by task, not by what the learner
installed.

**Validation grading, from LC.3.** A lesson's Validation step runs the test
suite, then static analysis through `uvx`: `ruff`, `pyrefly`, and one
complexity tool. `radon` (6.0.1) and `complexipy` (8.1.0) both install
under `uvx`; LC.3's plan picks one and fixes its thresholds, so this spec
commits to the shape and the plan to the numbers. LC.2 ships the
toolchain — `uv`, `uvx`, `ruff`, `pyrefly` — as lesson 1's prerequisite, so
a later lesson grades without a setup tangent.

## Excluded

Building the site (LC.1), any run, any lesson text, merging Andre's PRs,
PyCharm content and the Satyrn Education refactor (both backlog), and any
change to the worker, prompt, guards or ladder.
