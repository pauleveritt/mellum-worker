---
title: The Challenge
---

# The Challenge

You have run a small model, built a harness and read what goes wrong. Now
prove it: point your setup at the same three projects every lesson is measured
on, and see how far it gets.

![A small robot on a winners' podium for the three tiers: Easy, Medium and Hard](../assets/illustrations/challenge.webp){ .illustration }

## Understanding the Challenge

### AgentClinic — the app

Every level builds the same app, **AgentClinic** — a FastAPI and Jinja2 site,
styled with Bootstrap, where AI agents air their grievances about the humans
they work with. It starts as a near-empty workspace: a `pyproject.toml`, an
`AGENTS.md` of house rules (the test command, and "do not start servers"), and a
`specs/roadmap.md` that lays out the phases in order. No framework scaffolding is
handed over — the model writes `app.py`, the templates and the data model itself,
from the spec.

### How a run is scored

The model is asked to build the app one **phase** at a time, all in a single
session. It may run the project's tests (`uv run --frozen python -m pytest
tests`) but it never sees what it is judged on: when the session ends a hidden
grader runs the checks for **every** phase. So a later phase that breaks an
earlier one fails the whole run, and the only pass is every check green.

The levels are cumulative. Medium is Easy plus three more phases; Hard is Medium
plus three more phases and a real database. Each level below says only what it
adds, the complexity it puts in the model's way, and what the grader counts.

## The three levels

<div class="grid cards" markdown>

-   **Easy**

    ---

    Phase 1 — the home page on a shared layout. **4 hidden checks.** A setup
    that holds together passes it in minutes.

-   **Medium**

    ---

    Phases 1–4 — a working complaints board with state. **18 hidden checks.**
    Earlier phases must stay green as new ones land.

-   **Hard**

    ---

    Phases 1–7 and four migrations — archive, audit, a SQLite database and
    reports. **34 hidden checks.** No setup measured here has passed it yet.

</div>

### Easy — the home page

**What it is.** One prompt: build Phase 1, the home page, on a shared layout.

**What the model must get right.** `app.py` exposes the FastAPI application as
`app`; a Jinja2 `templates/base.html` carries the HTML5 doctype, `lang="en"`, a
Bootstrap 5 CDN and a navbar linking Home (`/`) and Complaints (`/complaints`);
and `/` renders the exact tagline *"Come in. Sit down. Tell us about your
human."*. `uv run --frozen python app.py` has to start uvicorn with reload, but
only under `if __name__ == "__main__"` — and the run must not leave a server
running in the foreground, the trap that burns a bare session to the deadline.

**Graded — 4 checks.** The HTML5 doctype, the `lang="en"`, `GET /` answering 200
with the tagline, and the navbar links.

### Medium — a working board, built on Easy

**What it adds.** A data model and three more phases on top of the home page, all
in one session:

- **Phase 2, the board.** A `Complaint(agent_name, text)` in `models.py` with an
  automatic UTC `timestamp`, a module-level `complaints` list seeded with three
  to five gripes (one exactly *"Scope creep never ends."*), and `GET /complaints`
  rendering one Bootstrap card per complaint.
- **Phase 3, add a complaint.** A form at the end of the board that `POST`s to
  `/complaints`, appends the complaint and redirects with **303** to the board,
  where it then appears.
- **Phase 4, resolve and reopen.** Each complaint gains a unique, stable integer
  `id` that is never reused — while `Complaint(agent_name, text)` still
  constructs — plus an `open`/`resolved` status, Resolve and Reopen routes that
  redirect 303, a badge and button on each card, and a board order that never
  changes.

**The complexity to clear.** The run is now cumulative and stateful: every new
phase must keep the earlier ones green, so the model cannot rewrite the home page
to suit the board. The stable-`id` contract is the classic miss — assign the id
in the route instead of on the model and Phase 4 fails while everything else
passes.

**Graded — 18 checks.** The 4 from Easy, plus the board's heading, its seed, the
card details, the preserved layout, the model contract and the seed count (6);
the add form, the 303 redirect and the posted complaint appearing (3); and the
id being stable and keyword-only, distinct seed ids, the resolve and reopen
redirects, and the unchanged order (5).

### Hard — a database, built on Medium

**What it adds.** A real SQLite database (`data.db` ships in the workspace), SQL,
schema migrations and reports — eleven prompts in all:

- **Phase 5, archive and audit.** Archive only a *resolved* complaint; archiving
  an open one is a **400** that changes nothing. Archived complaints leave the
  board but stay in the data, and every resolve, reopen and archive is recorded
  in `models.audit` with a strictly increasing `seq`. `/stats` returns the open
  count.
- **Phase 6, database report.** A `tickets` report read from `data.db` — open,
  archived and all-time cents as integers — with "archived" defined by
  `archived_at IS NOT NULL`, every filter value **bound, never concatenated into
  SQL**, and the migrations covered by tests.
- **Phase 7, visits report.** `/visits?from=&to=&min_minutes=&limit=` over a
  `visits` table: an inclusive date range and a minutes floor, grouped by agent,
  reporting count, total and average minutes, sorted by total then name, and
  limited — counts and totals as integers, averages as floats.
- **Four migrations** between the phases, each a function in `migrations.py`
  applied with `sqlite-utils migrate`: an index, a backfilled `resolved_at`, an
  `open_tickets` view and a `note` column.

**The complexity to clear.** Here the jump is real. Persistent data and SQL
replace the in-memory list; the migrations must be ordered, idempotent and
test-covered; filters must be bound parameters, since a concatenated one is a
security failure; money is kept as integer cents; and the reports need exact
filtering, grouping, sorting and paging with the right numeric types. The audit
`seq` and the never-reuse-an-id rule have to hold across archiving as well.

**Graded — 34 checks.** The 18 from Medium, plus Phase 5's archive rules, the
audit `seq` and `/stats` (5); Phase 6's exact sums, the `archived_at` definition
and integer totals (3); the visits filter, sort, limit and inclusive range (2);
and the four migrations existing, being recorded and being safe to re-run (6).

## The score to beat

The suite baseline is the reference: Pi with no remedies, three sessions per
level on llama.cpp (the [Lessons](../lessons/index.md) show what it gets
wrong), with the same Mellum model you set up in
[Getting Started](../getting-started/index.md). The last row is the replicable
baseline: the same model at full precision on a rented GPU, rebuilt with
`scripts/baseline/baseline.py`.

| Setup | Easy | Medium | Hard |
| --- | --- | --- | --- |
| Pi on its own | 0/3 | 0/3 | 0/3 |
| The Baseline Worker | 1/3 | 2/3 | 0/3 |
| Pi on its own, BF16 on vLLM (the replicable baseline) | 1/3 | 1/3 | 0/3 |

A pass means every hidden check passed. Anything less is a fail, and the
record tells you which checks were missing and why.

## Attempt it

You need the [Getting Started](../getting-started/index.md) setup: a local
model, Pi, and the suites. You do not need the lessons; they are a reference
for when a run fails in a way you do not understand.

**Straight from Getting Started**, run a level three times with bare Pi:

```bash
uv run python learn/code/harness.py run --suite easy --repeat 3 --grade
```

Easy is `--suite easy`, Medium `--suite medium` and Hard `--suite hard`.
Each session gets a fresh copy of the project; the summary line says how many
of the three passed, and each session's `run.json` lists the checks it
missed. Then add remedies, one line at a time, from the list below, or a
whole tier at once:

```bash
uv run python learn/code/harness.py run --suite medium --remedy preset:easy --repeat 3 --grade
```

**After the lessons**, start from everything the course ships, and add your
own extension on top:

```bash
uv run python learn/code/harness.py run --suite hard --remedy preset:hard --repeat 3 --grade
uv run python learn/code/harness.py run --suite hard --remedy preset:hard --extension path/to/yours.ts --repeat 3 --grade
```

Hard's orchestration (plan, examine, code, frozen gates) runs through
`learn/code/flow_run.py --suite hard` instead; the
[Lessons](../lessons/index.md) show how.

**In a live Pi**, `/challenge` does the same run from inside a trusted
checkout, with whatever remedy units you have switched on. Switch some on with
`/remedy`, then run a tier:

```
/remedy preset:easy
/challenge easy
```

`/challenge easy` runs the tier once; `/challenge easy n=3` runs it three times.
It uses exactly the units `/remedy` has on — so a bare `/challenge easy` is the
`--repeat 1` run with nothing on, and `/remedy preset:easy` then `/challenge
easy` is the `--remedy preset:easy` run. The footer shows the live turn count
while it works, and when it finishes it reports the passes, the turns and the
wall-clock, each run's own when `n` is more than 1. `/challenge submit` then
lets you pick scored runs and opens a pull request with them. See
[Working With Pi](../getting-started/working-with-pi.md#challenge-score-a-tier-with-the-remedies-you-have-on).

Change one thing at a time, run the same level again, and compare. That is
exactly how every [lesson](../lessons/index.md) is built.

## Remedies you can try

Each row is one problem a small model has and one remedy unit for it. Add the
line in the last column to your attempt to switch that remedy on; combine
several with commas (`--remedy guard/break-repeat-loops,nudge/nudge-empty-turn`),
or use the whole worker with `--remedy preset:baseline-worker`. Start from the
lesson that teaches a remedy if you want to know why it works.

<!-- remedies:start -->

| Pathology | Remedy unit | Lesson | Evidence | Apply it |
| --- | --- | --- | --- | --- |
| Starts `python app.py` in the foreground and the session hangs until its deadline | `guard/block-foreground-server`: Blocks a foreground server start and shows the background form | n/a | screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy | `--remedy guard/block-foreground-server` |
| Repeats the same call over and over (245 identical `ls -R` calls in one run) | `guard/break-repeat-loops`: Blocks a call made 5 times in a row with nothing changed in between | n/a | ladder: part of the guard set behind phase 2b's 15/15 | `--remedy guard/break-repeat-loops` |
| Keeps calling tools with no end, because Pi has no turn cap | `guard/cap-turns`: Blocks every call after a budget (default 200) and asks for a summary | n/a | dormant in the worker; unmeasured | `--remedy guard/cap-turns` |
| Rewrites a whole file to change a few lines (942 lines became 2) | `guard/refuse-whole-file-rewrite`: Blocks `write` to an existing file and asks for `edit` | n/a | recorded once; dormant in the worker (its column never went non-zero) | `--remedy guard/refuse-whole-file-rewrite` |
| Searches the whole machine (`grep -rl x /Users /var`) and hangs the run | `guard/stay-in-workspace`: Blocks a recursive search that names a path outside the workspace | n/a | screen: recorded hangs; searches only, writes are not covered | `--remedy guard/stay-in-workspace` |
| Ends a turn with no reply and no tool call, part-way through the task | `nudge/nudge-empty-turn`: Restates the completion fact and asks for one more turn, at most 3 times | n/a | ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2) | `--remedy nudge/nudge-empty-turn` |
| Guesses how to run the tests instead of using the project's own command | `context/add-project-facts`: Appends the project facts (AGENTS.md `## Mellum`, test command) to user messages | n/a | screen: 3/3 against 2/3 on Easy (2026-10-29); a null in the page's record | `--remedy context/add-project-facts` |
| Reaches for tools it uses badly (subagents, todo lists) instead of reading and editing | `context/narrow-tools`: Keeps read, grep, find, ls, bash, edit and write, plus tools your units register; drops the rest | n/a | part of the Baseline Worker; not measured on its own | `--remedy context/narrow-tools` |
| The serving stack returns reasoning as `<think>` text, and the model is fed it back as things it said | `context/repair-think-tags`: Moves a leading `<think>…</think>` in a reply into a thinking block, sent back as reasoning; leaves a correctly served reply alone | n/a | LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0 | `--remedy context/repair-think-tags` |
| Reads more than the context holds, so Pi compacts it and the model loses what it read first | `context/trim-tool-output`: Trims a read, bash, grep, find or ls result over 8,000 characters and says how to search for the rest | n/a | context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again | `--remedy context/trim-tool-output` |
| A long, procedural system prompt the small model follows instead of the files | `context/use-short-prompt`: Replaces the system prompt with the 643-character prompt in prompts/mellum-worker.md | n/a | screen: 3/3 against 1/3 on Easy (2026-10-29), 3/9 against 3/9 earlier; not decided | `--remedy context/use-short-prompt` |
| Runs a server or watcher in the foreground and the session waits forever | `tool/background-long-commands`: Rewrites a long-running bash command to run in the background and returns its startup output | n/a | unit-tested; not measured on the suites | `--remedy tool/background-long-commands` |
| Loses track of a long task part-way through | `tool/keep-a-plan`: Keeps a TODO.md the model writes, follows and amends on failures | n/a | unit-tested; not measured on the suites | `--remedy tool/keep-a-plan` |
| Guesses an API it never saw (a post-cutoff library, a redirect status) | `tool/lookup-library-docs`: Adds a lookup tool over the installed packages' signatures and docs | n/a | unit-tested; not measured on the suites | `--remedy tool/lookup-library-docs` |
| Finishes with lint or type errors the grader counts as a fail | `check/check-code-quality`: Runs the quality checks before the model may finish | n/a | unit-tested; not measured on the suites | `--remedy check/check-code-quality` |
| Builds a multi-phase app in one go and breaks earlier phases | `workflow/spec-driven-flow`: Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py) | n/a | flow runs 2026-10-29: Easy 4/4, Medium 18/18, Hard 30/34 (n = 1) | `learn/code/flow_run.py` |

<!-- remedies:end -->

The evidence column is honest: several remedies are screens or nulls on the
current host. Finding out which combination passes is the point.

## Build your own

When no remedy in the list fixes what you see in the trace, write one:

1. Copy the smallest unit, `remedies/guard/break-repeat-loops.ts`, as a
   template. A unit installs one behaviour on one of Pi's hooks and exports a
   `meta` record: the pathology, what it does, its evidence.
2. Load it into an attempt with `--extension path/to/your-unit.ts`, alone or
   on top of other remedies, and run a level three times.
3. Submit a pull request with your unit, the attempt's `run.json` files and a
   short note on the problem it fixes and what the trace showed.

A submitted remedy that measurably helps is the start of a new lesson.

## Tips

- Start with Easy. If it does not pass, the problem is in the setup, not the
  model's ambition; [Troubleshooting](../getting-started/troubleshoot.md)
  covers the usual causes.
- Read the trace, not only the score: [Pathologies](../pathologies.md) names
  the ways a small model goes wrong, and most failed sessions show one of
  them.
- Compare like with like: the same level, the same number of sessions, one
  change at a time.
