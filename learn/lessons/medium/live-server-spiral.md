---
title: The Live-Server Spiral
tier: medium
number: M1
time: 7 min read · 40 min to run
track: lessons
position: 1
prerequisites: [lessons/easy/guards-you-didnt-need]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# M1 · The Live-Server Spiral

A redirect reads as the wrong status, so the model starts a server to see for
itself — and the server it starts disagrees with the test client, so it curls,
and thrashes there to the deadline. One guard keeps it in process.

!!! abstract "Overview"

    **Questions**

    - Why does a confused model spin up `uvicorn` and `curl localhost` instead of testing in process?
    - Why does the foreground-server guard not stop it, and what does?

    **Objectives**

    - Read a medium trace where the worker starts a server 28 to 55 times and never settles.
    - Switch on `guard/no-live-server`, read the two commands it refuses, and watch 3 of 3 reach the gate.

![A small robot chasing its own tail around a server tower while the test bench sits unused beside it](../../assets/illustrations/pathologies.webp){ .illustration }

## Problem

**Badge:** `screen`

A medium build hits an HTTP behaviour the model misreads — a `303` redirect it
expects to be `200`, a `TestClient` `422` its own route signature causes. Instead
of reading the status in process, the model debugs the way a human might: it
starts `uvicorn` or `python app.py` and `curl`s `localhost`. The live server it
starts forks a process that disagrees with the in-process test client, so the
curl confirms nothing, so it starts another. The run spirals — 28 to 55 server
starts on one task — and the stall guard kills it before it ever settles.

## Eval case

**Badge:** `screen`

**The condition:** the medium suite (phases 1–4), built in a single pass with the
exit-gate on — the setup the Hard lessons use. **Before:**
`guard/foreground-server` only, which refuses a *foreground* server but lets the
backgrounded form through. **After:** the same plus `guard/no-live-server`. The
grader is the hidden oracle, summed across the four phases to 18.

## Evidence of the problem

**Badge:** `screen`

Gated, with no live-server guard, only **1 of 3** reps reached the exit-gate —
the other two thrashed in the spiral to the stall before they could settle
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
`guard/foreground-server` does not stop it: the model evades with `nohup … &`,
`| tee`, and `.venv/bin/python app.py`, all of which the foreground guard lets
pass. The failure is not a wrong file or a dropped requirement — it is the whole
session spent chasing a server it did not need.

## Solution

**Badge:** `screen`

One remedy unit, `guard/no-live-server`, refuses the spiral at both ends. Where
`foreground-server` blocks only a blocking start and even suggests the background
form, this one refuses **any** server start — foreground or background — and
**any** loopback HTTP probe, and points the worker back at the in-process client.
It is stricter on purpose: a detached server is the spiral's fuel.

### The code

Switch it on live:

```text
/remedy on guard/no-live-server
```

The guard is two checks and the message each returns, quoted from the file frozen
at a commit
([`extensions/mellum-guards.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-guards.ts#L275-L301)):

```ts
export const liveServerGuard = (call) => {
	if (call.toolName !== "bash") return undefined;
	const command = commandOf(call.input);
	if (isServerStart(command)) {        // uvicorn / app.py — foreground OR backgrounded
		return { block: true, reason:
			"Do not start a server to test this. A live server forks a process that disagrees with the " +
			"in-process test client and sends the run into a spiral. Exercise the app the way the tests do: " +
			"TestClient(app, follow_redirects=False) and check response.status_code." };
	}
	if (isLocalHttpProbe(command)) {     // curl / wget / httpie to localhost / 127.0.0.1 / ::1
		return { block: true, reason:
			"Do not curl a local server. Probing a live server is the spiral that hangs the run. " +
			"Exercise the endpoint in process: TestClient(app).get('/...')." };
	}
	return undefined;
};
```

`isServerStart` matches the start in any form — that is the one line of
difference from `foreground-server`, which exempts the backgrounded form.
`isLocalHttpProbe` matches an HTTP client aimed at a loopback address, so a remote
fetch (`curl https://pypi.org/…`) still passes. Both step aside for a read-only
command that merely names a server (`grep uvicorn`, `cat app.py`). To screen it on
a graded run, name it: `--remedy guard/no-live-server`.

**Lesson check:** with the guard, 3 of 3 reached settle and scored 18/18; the
full gated one-pass rig is in the
[record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md).

## Validation

**Badge:** `screen`

Added to the gated one-pass stack on medium, n=3: **3 of 3 reached settle and
scored 18/18**, where the ungated stack reached the gate on only 1 of 3. The guard
refused every reach — 5, 1 and 8 server starts and 0, 0 and 2 curls across the
three reps — and each rep stayed in process and converged. Rep 3 is the sharp
case: the model reached for a live server ten times, was refused every time, and
still passed cleanly at 91 requests with `guard=ok`
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
On screen in rep 3 the worker's own reasoning turned after a refusal — *the rule
says not to start servers, we need to fix the route* — and it went back to
`TestClient`.

## Interpretation

The weakest badge is `screen` — a scratch n=3, a lead, not a `run_ladder` rate.
The guard does one thing: it keeps the run in process, so the worker spends its
turns on the code instead of a server, and reaches the point where it can settle.
It is the mirror of E4's lesson — there the guard was weight that never fired;
here, on the tier where the pathology appears, the same kind of guard fires
repeatedly and earns its place. One wrinkle the pass rate hides: one rep reached a
correct 18/18 and then idled into the stall guard at the tail — the pass is
reliable, the clean exit is the next small lever. The evidence is llama.cpp, the
backend the course teaches.

### What to try next

A finish nudge once the build is correct — settle now, the tests pass — targets
the tail stall without touching the pass rate; its risk is nudging a rep that is
not actually done, so it wants the same n=3 gated screen to test.

### Run it yourself

Load the guard on a medium run and read its block count in the record; the full
gated one-pass rig that produced the 3-of-3 is in the research note, not a single
harness flag:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy guard/no-live-server --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - A small model debugs an HTTP surprise by starting a server and curling it, and spirals there.
    - `guard/foreground-server` lets the backgrounded form through; `guard/no-live-server` refuses both ends.
    - With the guard, 3 of 3 reached settle at 18/18 against 1 of 3 ungated — a scratch screen, not a rate.
