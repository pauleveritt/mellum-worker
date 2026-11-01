---
title: Check the Setup
number: S3
time: 3 min read · 1 min to run
track: lessons
position: 3
prerequisites: [getting-started/base-pi-on-llamacpp]
authors: [Andre van Zuydam]
backends: [none]
---

# S3 · Check the Setup

The worker's numbers only hold if the model server and Pi's provider entry
match the measured settings. `/mellum check` compares both against the frozen
values and tells you, line by line, what is off.

!!! abstract "Overview"

    **Questions**

    - How do I know my server and Pi agree with the measured settings?
    - Which differences matter, and which are only worth noting?

    **Objectives**

    - Run the check in Pi and from the terminal, and read its findings.
    - Tell a failing difference from an informational one.

![A small robot with a wrench untangling a knotted cable running between a laptop and a small server box](../../assets/illustrations/troubleshoot.webp){ .illustration }

## Problem

The recipe's results were measured at particular settings. If your server
serves a different context window, or Pi sends a different sampling value, your
runs are not the ones the lessons measured — and you will not know, because
nothing warns you. A quiet mismatch looks like the worker simply behaving
differently.

## Eval case

`/mellum check` reads two sources and compares them with the frozen expected
values: the model server (GET requests only — it never changes anything) and
the host's provider entry in Pi's `models.json`. Per-request values Pi sends
must match exactly — the sampling trio is `1 / 0.95 / 20` — or the check
**fails**. Server-only values that any client of the same model could change
are reported as **info**, not failures.

## Evidence of the problem

Without the check you compare by eye across two files and a running server,
and the values that matter most — the ones Pi sends on every request — are the
easiest to miss. A wrong `max_context_window` or a sampling value off by a
step changes what the model does on long tasks, silently.

## Solution

In Pi:

```text
/mellum check
```

From the terminal, with `--host pi` to read Pi's own provider entry (and
`--json` for machine-readable output):

```text
node scripts/mellum.mjs check --host pi
```

A difference reads like this, naming the key, what it found and what it
expected:

```text
Mellum server settings differ: max_context_window 32768 (expected 56000). Run /mellum check.
```

## Validation

A clean check reports no failing differences and exits `0`; the terminal form
sets a non-zero exit code when any finding is a failure, so you can gate on it.
A run that lists only `info` differences is fine — those are server-only
values, and the exit code stays `0`.

## Interpretation

Run `/mellum check` first, before you trust any run's numbers, and again
whenever you change the server or the provider entry. Treat a failure as "these
are not the measured settings" and fix it before reading results; treat an
info line as "another client could have set this" and decide whether it
matters for your run. The check only reads — it never edits your server or
your config.

### Run it yourself

From your checkout, against the Pi provider entry:

```bash
node scripts/mellum.mjs check --host pi
```

!!! success "Key points"

    - `/mellum check` compares the server and Pi's provider entry with the measured settings.
    - Per-request values must match exactly (sampling `1 / 0.95 / 20`) or the check fails.
    - Server-only values are reported as info, not failures.
    - The terminal form exits non-zero on a failure, so you can gate on it; it only reads.
