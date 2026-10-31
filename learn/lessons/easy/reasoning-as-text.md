---
title: Reasoning Returned as Text
tier: easy
number: E1
time: 4 min read · 3 min to run
track: lessons
position: 1
prerequisites: [lessons/start-here]
authors: [Andre van Zuydam]
backends: [vllm]
---

# E1 · Reasoning Returned as Text

Some serving stacks hand a thinking model's reasoning back as ordinary reply text, and Pi feeds it to the model again as things it said. One unit puts the reasoning back where it belongs, before anything else runs.

!!! abstract "Overview"

    **Questions**

    - Where does a thinking model's reasoning go, and who separates it from the reply?
    - What happens when the serving stack gets that wrong?

    **Objectives**

    - Run a session on a host that returns reasoning as `<think>` text, and read `reasoning_as_text` in `run.json`.
    - Add `context/repair-think-tags` and see the record come back clean.

![A small robot sorting a tangled ribbon of thought bubbles and speech bubbles into two separate trays](../../assets/illustrations/reasoning-as-text.webp){ .illustration }

## Problem

**Badge:** `screen`

A thinking model writes its reasoning first and its answer after. The
serving stack (here vLLM's reasoning parser) splits the two: the reasoning
goes in a field of its own, the answer in the reply. Pi reads reasoning
only from that field. When the parser misses, the reasoning arrives inside
the reply, opened by a literal `<think>`. Pi shows it as the answer, and on
every later request sends it back to the model as things it said, not as
its own reasoning.

## Eval case

**Badge:** `screen`

**The condition:** a host whose streaming reasoning parser misses every turn
after the first, the LAN vLLM host this course is checked on. **Before:**
bare Pi. **After:** bare Pi plus `context/repair-think-tags`. Both run the
lesson's own challenge, `learn/challenges/reasoning-as-text/`: a small
calculator with tests. The code is easy on purpose; what fails is in the
record. The challenge's `record.json` requires `reasoning_as_text` to be 0,
so a session that was fed its reasoning back as text fails even when its
tests pass.

## Evidence of the problem

**Badge:** `screen`

On the LAN host, 236 of 244 assistant turns across eight harness sessions
came back with their reasoning as text; each session's first turn was the
only clean one. On the pinned vLLM 0.32.0 host, 0 of 136 turns did. Two
screens of this challenge on the LAN host, one session each: without the
unit, `reasoning_as_text` was 6 and then 8, with the hidden tests passing
both times ([note](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lan-reasoning-leak.md)).

## Solution

**Badge:** `screen`

**Remedy unit:** `context/repair-think-tags`; apply it with `--remedy context/repair-think-tags`.

**Lesson check:** held on 2026-10-30: FAIL → PASS on the LAN host, one session per arm ([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-10-30-reasoning-as-text-check/README.md)).

At the end of each reply, the unit moves a leading `<think>…</think>` out of
the reply text and into a thinking block labelled as reasoning, which is
how Pi stores reasoning it received correctly. Pi then shows it as thinking
and sends it back to the server in the reasoning field. A reply without a
leading `<think>` is left exactly as it was, so on a correct host the unit
does nothing.

It is the first unit because every later lesson runs on the same host: from
here on, every before line lists it, so this failure is shown once and then
kept fixed.

## Validation

**Badge:** `reference-run`

The preregistered lesson check, 2026-10-30, one session per arm on the LAN
host: without the unit the session failed on its record
(`reasoning_as_text` 7, its tests passing); with
`context/repair-think-tags` it was 0 and the session passed
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/evals/2026-10-30-reasoning-as-text-check/README.md)).
With the two screens, the bare session was fed its reasoning as text in
3 of 3 sessions on this host. This shows the repair works on this host,
not how often parsers miss elsewhere.

## Interpretation

The weakest badge is `screen`. Not every failure is the model's: from the
outside a misparsed reply looks like a model that talks to itself. The
record tells them apart, which is why the harness counts
`reasoning_as_text` from the history the model was actually sent. The cure
for the cause is on the server (vLLM 0.32.0 with `--reasoning-parser qwen3`
does not miss); the unit is the repair you can apply in Pi when the server
is not yours to change.

### Run it yourself

Before, then after:

```bash
uv run python learn/code/harness.py run --suites-dir learn/challenges --suite reasoning-as-text --repeat 1 --deadline 600 --stall 120
uv run python learn/code/harness.py run --suites-dir learn/challenges --suite reasoning-as-text --remedy context/repair-think-tags --repeat 1 --deadline 600 --stall 120
```

!!! success "Key points"

    - The serving stack, not the model, separates reasoning from the reply; when it misses, the model is fed its own reasoning as things it said.
    - `run.json`'s `reasoning_as_text` counts the turns that reached the model that way.
    - `context/repair-think-tags` puts the reasoning back, and every later lesson keeps it on.
