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

The levels stack. Each adds phases to the one before, and the hidden grader runs
every phase that should exist by then — so the check count climbs as the app
grows.

| Phase the model builds | Easy | Medium | Hard |
| --- | :---: | :---: | :---: |
| 1 · Home page + shared layout | ● | ● | ● |
| 2 · Complaints board | | ● | ● |
| 3 · Add a complaint | | ● | ● |
| 4 · Resolve & reopen | | ● | ● |
| 5 · Archive & audit | | | ● |
| 6 · Database report (SQLite) | | | ● |
| 7 · Visits report | | | ● |
| 4 · Schema migrations | | | ● |
| **Hidden checks** | **4** | **18** | **34** |

No setup measured here has passed Hard yet.

### Easy — the home page · 4 checks

**Build**

- `app.py` exposes the FastAPI app as `app`.
- `templates/base.html`: HTML5 doctype, `lang="en"`, Bootstrap 5 from a CDN, a navbar linking Home (`/`) and Complaints (`/complaints`).
- `/` renders the exact tagline *"Come in. Sit down. Tell us about your human."*.
- `uv run --frozen python app.py` starts uvicorn with reload, only under `if __name__ == "__main__"`.

**Watch out** — the `do not start servers` rule: a foreground server that never returns burns a bare run to the deadline.

**Graded (4)** — doctype · `lang="en"` · `GET /` → 200 with the tagline · navbar links.

### Medium — the complaints board · 18 checks

*Easy, plus three more phases in one session.*

**Build**

- **Phase 2 — board:** `Complaint(agent_name, text)` in `models.py` (auto UTC `timestamp`); a seeded `complaints` list of 3–5, one exactly *"Scope creep never ends."*; `GET /complaints` renders a Bootstrap card each.
- **Phase 3 — add:** a form POSTs to `/complaints`, appends, and redirects **303** to the board, where it appears.
- **Phase 4 — resolve/reopen:** a unique, never-reused integer `id` (the constructor still works); an `open`/`resolved` status; resolve & reopen routes that redirect 303; a badge and button per card; the board order never changes.

**Watch out** — every new phase must keep the earlier ones green, and assigning the `id` in the route instead of on the model fails Phase 4 while all else passes.

**Graded (18)** — Easy's 4 · board heading / seed / details / layout / model / seed-count (6) · add form / 303 / appears (3) · id / status / order (5).

### Hard — the database · 34 checks

*Medium, plus three more phases and a real SQLite database (`data.db`), across eleven prompts.*

**Build**

- **Phase 5 — archive & audit:** archive only a *resolved* complaint (archiving an open one is **400**, no change); archived leaves the board but stays in the data; `models.audit` logs every transition with a strictly increasing `seq`; `/stats` returns the open count.
- **Phase 6 — tickets report:** open / archived / all-time cents as integers from `data.db`; "archived" is `archived_at IS NOT NULL`; every filter value bound; migrations covered by tests.
- **Phase 7 — visits report:** `/visits?from=&to=&min_minutes=&limit=` — inclusive range, minutes floor, grouped by agent, count / total / average minutes, sorted by total then name, limited; integers vs floats.
- **4 migrations** via `sqlite-utils migrate`: an index, a backfilled `resolved_at`, an `open_tickets` view, a `note` column.

**Watch out** — a concatenated SQL filter is a security fail; migrations must be idempotent; cents stay integers; the `seq` and never-reuse-`id` rules hold across archive too.

**Graded (34)** — Medium's 18 · Phase 5 archive / audit / stats (5) · Phase 6 sums / `archived_at` / integers (3) · visits filter + range (2) · migrations exist / recorded / re-runnable (6).

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

From a trusted checkout, run a level in Pi with `/challenge`. Switch on the
remedy units you want with `/remedy`, then run the tier:

```
/challenge easy
/remedy preset:easy
/challenge easy
```

The first line runs Easy once with nothing on — your baseline. The next two
switch on the whole Easy stack and run it again, so you can watch the score
move. `/challenge easy n=3` runs three times; `/challenge submit` opens a pull
request with the runs you pick. While it runs, the model's turns stream so you
see what it is doing, and the result reports the passes, the turns and the
wall-clock. See [Working With
Pi](../getting-started/working-with-pi.md#challenge-score-a-tier-with-the-remedies-you-have-on).

Change one thing at a time, run the same level again, and compare — that is
exactly how every [lesson](../lessons/index.md) is built.

**From the command line**, the same runs go through the harness directly:

```bash
uv run python learn/code/harness.py run --suite easy --repeat 3 --grade
uv run python learn/code/harness.py run --suite medium --remedy preset:easy --repeat 3 --grade
uv run python learn/code/harness.py run --suite hard --remedy preset:hard --extension path/to/yours.ts --repeat 3 --grade
```

`--suite` picks the tier, `--remedy` takes units or a preset, and `--repeat`
the count. Hard's orchestration (plan, examine, code, frozen gates) runs through
`learn/code/flow_run.py --suite hard`; the [Lessons](../lessons/index.md) show
how.

## Remedies you can try

You do not need to read all of these. Start from a preset — `/remedy
preset:easy` switches on the whole Easy stack at once — run the tier, and reach
for a single unit only when the trace shows a problem the preset missed. Each
row is one problem and the unit that answers it; the last column is the
`/remedy` command that switches it on in a live Pi.

<!-- remedies:start -->

| Pathology | Remedy unit | Evidence | Switch on |
| --- | --- | --- | --- |
| Starts `python app.py` in the foreground and the session hangs until its deadline | `guard/block-foreground-server`: Blocks a foreground server start and shows the background form | screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy | `/remedy on guard/block-foreground-server` |
| Repeats the same call over and over (245 identical `ls -R` calls in one run) | `guard/break-repeat-loops`: Blocks a call made 5 times in a row with nothing changed in between | ladder: part of the guard set behind phase 2b's 15/15 | `/remedy on guard/break-repeat-loops` |
| Keeps calling tools with no end, because Pi has no turn cap | `guard/cap-turns`: Blocks every call after a budget (default 200) and asks for a summary | dormant in the worker; unmeasured | `/remedy on guard/cap-turns` |
| Rewrites a whole file to change a few lines (942 lines became 2) | `guard/refuse-whole-file-rewrite`: Blocks `write` to an existing file and asks for `edit` | recorded once; dormant in the worker (its column never went non-zero) | `/remedy on guard/refuse-whole-file-rewrite` |
| Searches the whole machine (`grep -rl x /Users /var`) and hangs the run | `guard/stay-in-workspace`: Blocks a recursive search that names a path outside the workspace | screen: recorded hangs; searches only, writes are not covered | `/remedy on guard/stay-in-workspace` |
| Ends a turn with no reply and no tool call, part-way through the task | `nudge/nudge-empty-turn`: Restates the completion fact and asks for one more turn, at most 3 times | ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2) | `/remedy on nudge/nudge-empty-turn` |
| Guesses how to run the tests instead of using the project's own command | `context/add-project-facts`: Appends the project facts (AGENTS.md `## Mellum`, test command) to user messages | screen: 3/3 against 2/3 on Easy (2026-10-29); a null in the page's record | `/remedy on context/add-project-facts` |
| Reaches for tools it uses badly (subagents, todo lists) instead of reading and editing | `context/narrow-tools`: Keeps read, grep, find, ls, bash, edit and write, plus tools your units register; drops the rest | part of the Baseline Worker; not measured on its own | `/remedy on context/narrow-tools` |
| The serving stack returns reasoning as `<think>` text, and the model is fed it back as things it said | `context/repair-think-tags`: Moves a leading `<think>…</think>` in a reply into a thinking block, sent back as reasoning; leaves a correctly served reply alone | LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0 | `/remedy on context/repair-think-tags` |
| Reads more than the context holds, so Pi compacts it and the model loses what it read first | `context/trim-tool-output`: Trims a read, bash, grep, find or ls result over 8,000 characters and says how to search for the rest | context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again | `/remedy on context/trim-tool-output` |
| A long, procedural system prompt the small model follows instead of the files | `context/use-short-prompt`: Replaces the system prompt with the 643-character prompt in prompts/mellum-worker.md | screen: 3/3 against 1/3 on Easy (2026-10-29), 3/9 against 3/9 earlier; not decided | `/remedy on context/use-short-prompt` |
| Runs a server or watcher in the foreground and the session waits forever | `tool/background-long-commands`: Rewrites a long-running bash command to run in the background and returns its startup output | unit-tested; not measured on the suites | `/remedy on tool/background-long-commands` |
| Loses track of a long task part-way through | `tool/keep-a-plan`: Keeps a TODO.md the model writes, follows and amends on failures | unit-tested; not measured on the suites | `/remedy on tool/keep-a-plan` |
| Guesses an API it never saw (a post-cutoff library, a redirect status) | `tool/lookup-library-docs`: Adds a lookup tool over the installed packages' signatures and docs | unit-tested; not measured on the suites | `/remedy on tool/lookup-library-docs` |
| Finishes with lint or type errors the grader counts as a fail | `check/check-code-quality`: Runs the quality checks before the model may finish | unit-tested; not measured on the suites | `/remedy on check/check-code-quality` |
| Builds a multi-phase app in one go and breaks earlier phases | `workflow/spec-driven-flow`: Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py) | flow runs 2026-10-29: Easy 4/4, Medium 18/18, Hard 30/34 (n = 1) | `/remedy on workflow/spec-driven-flow` |

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
