---
title: Reading More Than Fits
tier: easy
number: E2
time: 4 min read · 10 min to run
track: lessons
position: 2
prerequisites: [lessons/easy/reasoning-as-text]
authors: [Andre van Zuydam]
backends: [vllm]
---

# E2 · Reading More Than Fits

A model that reads every long file whole fills its context, and Pi compacts it by summarising away what it read first. One unit trims a tool result that is too big and tells the model how to search for the part it needs.

!!! abstract "Overview"

    **Questions**

    - What happens when a session reads more than its context window holds?
    - How do I keep a model from reading everything whole?

    **Objectives**

    - Run a task over eight long notes and read `compactions` in `run.json`.
    - Add `context/trim-tool-output` and see the session finish without a compaction.

![A small robot trying to stuff an armful of thick books into a small backpack while pages spill out](../../assets/illustrations/context-overflow.webp){ .illustration }

## Problem

**Badge:** `screen`

Every tool result goes into the context, and the context has a window: 64k
tokens on the host this course is checked on. A model that reads each file
whole, however long, runs into it. Pi does not stop there: it compacts the
context, asking the model to summarise its own history, and carries on with
the summary. Whatever the summary leaves out is gone. The model then reads
the same files again, fills the window again, and is compacted again.

## Eval case

**Badge:** `screen`

**The condition:** a task that needs a fact from each of eight long notes,
about 80,000 tokens together, against a 64k window. **Before:** Pi with
`context/repair-think-tags` (from E1). **After:** the same plus
`context/trim-tool-output`. Both run the lesson's own challenge,
`learn/challenges/context-overflow/`: eight 40 KB design notes, each naming
its project's owner only in its last section; write `owners.md` with all
eight. The challenge's `record.json` requires `compactions` to be 0.

## Evidence of the problem

**Badge:** `screen`

Two screens on the LAN host, one session each. Without the unit, the first
read all eight notes whole, was compacted twice and read eight notes again;
the second was compacted six times, peaked at 45,244 tokens, made 49
requests and wrote a wrong list. With the unit, the session was never
compacted, peaked at 4,918 tokens and finished in 13 requests with every
owner right.

## Solution

**Badge:** `screen`

**Remedy unit:** `context/trim-tool-output`; apply it with `--remedy context/trim-tool-output`.

**Lesson check:** held on 2026-10-30: FAIL → PASS on the LAN host, one session per arm ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-10-30-context-overflow-check/README.md)).

The unit watches every `read`, `bash`, `grep`, `find` and `ls` result. One
over 8,000 characters (about 2,000 tokens) is cut to its first 8,000, with a
note saying how much was cut and how to get the rest: search with
`grep -n "<what you need>" <file>`, or read a part with `offset` and
`limit`. The model then asks for the lines it needs instead of the whole
file. Results that fit pass through unchanged, and `edit` and `write` are
never touched.

## Validation

**Badge:** `reference-run`

The preregistered lesson check, 2026-10-30, one session per arm on the LAN
host: without the unit the session compacted 13 times, peaked at 50,720
tokens, made 99 requests and wrote a wrong list; with
`context/trim-tool-output` it never compacted, peaked at 5,326 tokens and
passed in 13 requests
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-10-30-context-overflow-check/README.md)).
With the two screens, the session without the unit compacted in 3 of 3
sessions. This shows the trim works for this task on this host, not where
the threshold should sit for every task.

## Interpretation

The weakest badge is `screen`. Compaction is a safety net, not a fix: it
keeps a session alive by throwing away what the model read, and a small
model then reads it again. The cheaper move is to read less. A real
codebase has the same shape as this challenge, long files with the one line
you need somewhere inside, so the habit the unit teaches is the one to keep:
search first, read a part, never the whole by default.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suites-dir learn/challenges --suite context-overflow --remedy context/repair-think-tags --repeat 1 --deadline 900 --stall 180
uv run python learn/code/harness.py run --suites-dir learn/challenges --suite context-overflow --remedy context/repair-think-tags,context/trim-tool-output --repeat 1 --deadline 900 --stall 180
```

!!! success "Key points"

    - A context has a window; reading every long file whole fills it.
    - Pi compacts a full context, and the model loses what it read first; `run.json`'s `compactions` counts it.
    - `context/trim-tool-output` cuts an oversized result and points the model at searching for the part it needs.
