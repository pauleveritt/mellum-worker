---
title: Learn from Runs
number: S5
time: 3 min read · 1 min to run
track: lessons
position: 5
prerequisites: [start/see-the-last-run]
authors: [Andre van Zuydam]
backends: [none]
tryit: "Run a task or two with `/mellum`, then | `/mellum learn` — turn the runs into a `## Mellum` section for AGENTS.md"
---

# S5 · Learn from Runs

The same failures repeat until you tell the project about them. `/mellum learn`
reads your recent runs, names what went wrong, and suggests the `## Mellum`
lines your `AGENTS.md` is missing.

!!! abstract "Overview"

    **Questions**

    - How do I turn repeated run failures into project facts?
    - What does `/mellum learn` write, and where?

    **Objectives**

    - Summarise the last runs' failures and read the suggested facts.
    - Add them to `AGENTS.md` in Pi, or print them from the terminal.

![A small robot weighing four coloured badges on a balance scale, a magnifying glass in its hand](../../assets/illustrations/evidence.webp){ .illustration }

## Problem

Mode sends the small model your task and the worker prompt, but not your
conversation, skills or most of `AGENTS.md` — only a `## Mellum` section. Miss
that section and the model guesses the test command and bends the project to
fit, run after run. The fix is to write down what it keeps getting wrong, but
spotting the pattern across runs by hand is tedious.

## Eval case

`/mellum learn [n]` reads the run records for the current directory — the last
`n`, default 10 — and names what went wrong across them: a guessed test
command, a bent project, success claimed after a failed command, long runs,
foreground servers, settings drift. It then suggests the `## Mellum` lines your
`AGENTS.md` lacks, so the next run starts knowing what this run had to discover.

## Evidence of the problem

Without it, the signal is spread across many run records: the same guessed
command in three of them, the same stray `conftest.py` the model wrote to make
its own guess work. You would have to read each record and hold the pattern in
your head. The report does that reading for you:

```text
mellum learn: 4 runs in /home/user/proj (2026-10-01 to 2026-10-04)

- Project bent to fit in 3 runs: conftest.py, pyproject.toml, src/__init__.py; uv add httpx
```

## Solution

In Pi Mode, the last 10 runs or a count you give:

```text
/mellum learn
/mellum learn 25
```

In Pi it offers the suggested lines and adds them to `AGENTS.md`. From the
terminal it only reads and prints — it never writes a file — so you can review
first (`--n` for the count, `--json` for machine-readable output):

```text
node scripts/mellum.mjs learn --n 25
```

## Validation

In Pi, a successful run reports how many lines it added to `AGENTS.md`; if the
file changed while it was asking, it tells you to run `/mellum learn` again
rather than writing over the change. From the terminal you get the report and
the suggested `## Mellum` block printed, and your files are untouched.

## Interpretation

Run `/mellum learn` after a handful of runs in a project, read the suggested
section, and keep the lines that match what you saw — the test command above
all. It closes the loop the rest of the Start tier opens: [S1](turn-the-worker-on.md)
and [S2](run-one-task.md) run the work, [S4](see-the-last-run.md) reads one run,
and `learn` turns many runs into the facts that stop the next one repeating
them. The terminal form never writes, so it is safe to run anywhere; only the
Pi form edits `AGENTS.md`, and only with your go-ahead.

### Run it yourself

From a project directory with a few run records:

```bash
node scripts/mellum.mjs learn --n 25
```

!!! success "Key points"

    - `/mellum learn [n]` reads the last n runs (default 10) and names what went wrong.
    - It suggests the `## Mellum` lines your `AGENTS.md` lacks, so the next run starts knowing them.
    - In Pi it adds the lines to `AGENTS.md`; the terminal form only reads and prints.
    - The test command is the fact worth keeping most — it stops the model guessing one.
