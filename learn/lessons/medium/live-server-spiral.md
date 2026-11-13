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

A redirect reads as the wrong number, so the model starts a server to see for
itself. And that server disagrees with the test client, so it curls, and
thrashes to the deadline. One guard keeps it in process.

!!! abstract "Overview"

    **Questions**

    - Why does a confused model spin up `uvicorn` and curl `localhost` instead of testing in process?
    - Why doesn't the foreground-server guard stop it, and what does?

    **Objectives**

    - Read a medium trace where the worker starts a server 28 to 55 times and never settles.
    - Switch on `guard/no-live-server`, read the two commands it refuses, and watch 3 of 3 reach the gate.

![A small robot running in a frantic circle around a humming server tower, chasing a looping cable, the test bench beside it untouched](../../assets/illustrations/live-server-spiral.webp){ .illustration }

## Problem

**Badge:** `screen`

A redirect comes back `303` where the model wanted `200`, and it doesn't believe
the number. So it does what a tired developer does at midnight. It starts a
server and curls it to see for itself. But the server it starts is a stranger:
it forks a second process that disagrees with the in-process test client, so the
curl settles nothing, so it starts another. The run spirals, 28 to 55 servers on
one task, and the stall guard pulls the plug before the work ever finishes. The
test bench was sitting right there the whole time.

## Eval case

**Badge:** `screen`

**The condition:** the medium suite (phases 1–4), built in a single pass with the
exit-gate on. The setup the Hard lessons use. **Before:**
`guard/foreground-server` only, which refuses a *foreground* server but waves the
backgrounded form through. **After:** the same plus `guard/no-live-server`. The
grader is the hidden oracle, summed across the four phases to 18.

## Evidence of the problem

**Badge:** `screen`

Gated, with no live-server guard, only **1 of 3** reps reached the exit-gate. The
other two thrashed in the spiral to the stall before they could settle
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
`guard/foreground-server` doesn't stop it. The model slips past with `nohup … &`,
`| tee`, and `.venv/bin/python app.py`, every one of them a start the foreground
guard lets through. The failure isn't a wrong file or a dropped requirement. It's
the whole session spent chasing a server it never needed.

## Solution

**Badge:** `screen`

One remedy unit, `guard/no-live-server`, shuts the spiral at both ends. Where
`foreground-server` blocks only a blocking start and even suggests the background
form, this one refuses **any** server start, foreground or background, and
**any** loopback curl, and sends the worker back to the in-process client. It's
stricter on purpose: a detached server is the spiral's fuel.

### The code

Switch it on live:

```text
/remedy on guard/no-live-server
```

The guard is two checks and the message each one hands back, quoted from the file
frozen at a commit
([`extensions/mellum-guards.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-guards.ts#L275-L301)):

```ts
export const liveServerGuard = (call) => {
	if (call.toolName !== "bash") return undefined;
	const command = commandOf(call.input);
	if (isServerStart(command)) {        // uvicorn / app.py, foreground OR backgrounded
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

`isServerStart` matches the start in any form. That one line is the whole
difference from `foreground-server`, which lets the backgrounded form through.
`isLocalHttpProbe` matches an HTTP client aimed at a loopback address, so a remote
fetch (`curl https://pypi.org/…`) still passes. Both step aside for a read-only
command that merely names a server, `grep uvicorn`, `cat app.py`, because naming
a thing isn't starting it. To screen it on a graded run, name it:
`--remedy guard/no-live-server`.

**Lesson check:** with the guard, 3 of 3 reached settle and scored 18/18; the full
gated one-pass rig is in the
[record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md).

## Validation

**Badge:** `screen`

Added to the gated one-pass stack on medium, n=3: **3 of 3 reached settle and
scored 18/18**, where the ungated stack had reached the gate on only 1 of 3. The
guard refused every reach. 5, 1 and 8 server starts and 0, 0 and 2 curls across
the three reps. And each rep stayed in process and came home
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-11-08-one-pass-vs-architect-loop.md)).
Rep 3 is the one to watch: the model reached for a live server ten times, was
turned back every time, and still passed cleanly at 91 requests with `guard=ok`.
On screen its own reasoning turned after a refusal. *the rule says not to start
servers, we need to fix the route*. And it went back to `TestClient`.

## Interpretation

The weakest badge is `screen`. A scratch n=3, a lead, not a `run_ladder` rate.
The guard does one thing, and it does it well: it keeps the run in process, so the
worker spends its turns on the code instead of a server, and reaches the point
where it can settle. It's the mirror of E4. There the guard was weight that never
fired; here, on the tier where the pathology actually lives, the same kind of
guard fires over and over and earns its keep. One wrinkle the pass rate hides: one
rep reached a correct 18/18 and then idled into the stall guard at the tail. The
pass is reliable; the clean exit is the next small lever. The evidence is
llama.cpp, the backend the course teaches.

### What to try next

A finish nudge once the build is correct, settle now, the tests pass, goes after
the tail stall without touching the pass rate. The risk is nudging a rep that
isn't actually done, so it wants the same n=3 gated screen to earn its place.

### Run it yourself

Load the guard on a medium run and read its block count in the record; the full
gated one-pass rig that produced the 3-of-3 is in the research note, not one
harness flag:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy guard/no-live-server --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - A small model meets an HTTP surprise, starts a server to debug it, and spirals there.
    - `guard/foreground-server` lets the backgrounded form through; `guard/no-live-server` shuts both ends.
    - With the guard, 3 of 3 reached settle at 18/18 against 1 of 3 ungated. A scratch screen, not a rate.
