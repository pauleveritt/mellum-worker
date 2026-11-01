---
title: See the Last Run
number: S4
time: 3 min read · 1 min to run
track: lessons
position: 4
prerequisites: [start/run-one-task]
authors: [Andre van Zuydam]
backends: [none]
tryit: "First run something, e.g. `/mellum Do the task in TASK.md` | `/mellum last` — see that run as a table"
---

# S4 · See the Last Run

After the worker runs, you want to know what it actually did — turns, requests,
what passed — without digging through files. `/mellum last` prints the newest
run as a table, with no model call.

!!! abstract "Overview"

    **Questions**

    - How do I read what the worker's last run did, out of its own context?
    - How can I ask a follow-up about that run?

    **Objectives**

    - Show the newest run as a table in Pi and from the terminal.
    - Explain why the table goes into your session, not the worker's.

![A small robot kneeling with a magnifying glass over a long paper scroll, one spot on it circled in coral](../../assets/illustrations/read-the-failure.webp){ .illustration }

## Problem

A run leaves a record on disk, but reading it means finding the right file and
parsing JSON. You want the headline — did it pass, how many turns, how long —
at a glance, and you want it in a form you can ask a question about, without
spending the small model's context or a fresh model call to get it.

## Eval case

`/mellum last` finds the newest run record at or under the current directory —
whether it came from Mode (`/mellum on`) or a one-shot Worker task — and prints
it as a Markdown table. It makes no model call: it only reads the record. In
your main session the table goes into the conversation, so you can follow up
with a short question like "why the slow start?". While Mellum Mode is on, it
arrives as a notification instead, kept out of the worker's context.

## Evidence of the problem

Without it, "how did that run go?" means locating the run directory, opening
`run.json`, and reading `passed`, `requests` and `wall` by hand — and if you
want to ask about it, pasting the numbers into a prompt yourself. The record
is right there, but not in front of you.

## Solution

In Pi:

```text
/mellum last
```

From the terminal (`--json` for machine-readable output, `--file` to point at
a specific records file):

```text
node scripts/mellum.mjs last
```

The table names the run's mode, time and directory, then one row per metric:

```text
mellum last: Mode (one-shot), 2026-10-12 11:21, /home/user/ac-demo

| Metric | Value |
|---|---|
```

## Validation

You see the newest run's table with its metrics filled in. If run records are
off (`MELLUM_MODE_RUNS=0`) or nothing has run under this directory, `/mellum
last` says so plainly rather than showing an empty table — a bare-Pi run that
wrote no record is reported as "no record", not as a failure.

## Interpretation

Use `/mellum last` right after a run to read the outcome, and in your main
session to turn it into a question — the table is in context, so the next
prompt can reason about it. For failures, pair it with the reading order from
[S0 · Start Here](../start-here.md): `passed`, then `checks_ran` and `stalled`,
before the missed checks. To look across several runs rather than the last one,
use [S5 · Learn from Runs](learn-from-runs.md).

### Run it yourself

From a directory that has a run record:

```bash
node scripts/mellum.mjs last
```

!!! success "Key points"

    - `/mellum last` prints the newest run under the current directory as a table, with no model call.
    - In your main session it goes into the conversation, so you can ask a follow-up; while Mode is on it is a notification.
    - It covers both Mode and one-shot Worker runs.
    - No record under this directory is reported as "no record", not a failure.
