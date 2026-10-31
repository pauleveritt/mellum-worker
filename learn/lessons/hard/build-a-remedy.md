---
title: Build a Remedy
tier: hard
number: H6
time: 5 min read · 30 min to build · 1 h to run
track: lessons
position: 6
prerequisites: [lessons/hard/build-a-tool]
authors: [Andre van Zuydam]
backends: [vllm]
---

# H6 · Build a Remedy

Every remedy in this course is one unit that corrects one named failure. This
last lesson shows how one is built, tested and submitted, with the E1 loop
breaker as the template, and your file is the after.

!!! abstract "Overview"

    **Questions**

    - What is a remedy unit, in code, and what does it hook into?
    - How do I test one without a model, and how do I submit it?

    **Objectives**

    - Write a guard on `tool_call` that returns `{ block, reason }`, or a nudge.
    - Fill in the `meta` record the remedies list is generated from.
    - Test the unit against a fake `pi`, run a level with it, and open a pull request.

![A small robot fitting a new section of guard rail along a path, a toolbox beside it and a flag ahead](../../assets/illustrations/build-a-remedy.webp){ .illustration }

## Problem

**Badge:** `conjecture`

You named a failure in a trace and no row in the remedies list fixes it.
Rewording the prompt lands unreliably on a small model; a unit that refuses
the bad call, or asks for one more turn, does not depend on the model
behaving.

## Eval case

**Badge:** `conjecture`

**Before:** `--remedy preset:hard`. **After:** the same line plus your unit,
loaded with `--extension`. The lesson's own challenge is a task only a new
remedy can pass; it is not built yet (planned), so for now both
runs are on Bronze and Silver.

## Evidence of the problem

**Badge:** `conjecture`

Nothing here is measured. The template unit's own pathology is recorded (245
identical `ls -R` calls in one run); yours starts as a failure you can point
to in a `trace.jsonl` ([S0](../start-here.md#reading-a-real-failure)).

## Solution

**Badge:** `conjecture`

**Remedy unit:** none: you write it; the template is `remedies/guard/break-repeat-loops.ts`, wired by `remedies/install.ts`.

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

The whole template unit:

```ts
export const meta: UnitMeta = {
	pathology: "Repeats the same call over and over (245 identical `ls -R` calls in one run)",
	does: "Blocks a call made 5 times in a row with nothing changed in between",
	lesson: "",
	evidence: "ladder: part of the guard set behind phase 2b's 15/15",
};

export function install(pi: PiLike, opts: { window?: number; threshold?: number } = {}): void {
	installGuard(pi, createLoopBreaker(opts.window, opts.threshold));
}

export default (pi: PiLike) => install(pi);
```

- **A guard** is a function from a tool call to a decision. `installGuard`
  puts it on `tool_call`: return `{ block: true, reason }` to refuse, with a
  reason the model can act on, or `undefined` to allow.
- **A nudge** hooks the end of a turn instead: `nudge/nudge-empty-turn` returns
  a decision from `agent_before_settle` to ask for one more turn.
- **`meta`** feeds the remedies list: the pathology in plain words, what the
  unit does, the lesson that teaches it (empty if none) and its evidence,
  stated honestly.
- **Where:** `remedies/<kind>/<name>.ts` in your fork, or anywhere, loaded
  with `--extension`.
- **Test** it like `tests/remedy-units.test.mjs`: a fake `pi` that records
  `on` handlers, then fire `tool_call` and assert it blocks the bad call and
  allows a good one. Show the test failing before the unit exists.

??? example "A reference solution"

    Try your own first. This guard keeps the acceptance test unweakenable
    ([H3](dont-trust-the-self-exit.md)): it refuses edits and writes to test files.

    ```ts
    import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

    export const meta: UnitMeta = {
    	pathology: "Edits the acceptance test until it passes instead of fixing the code",
    	does: "Refuses edit and write calls on files under tests/",
    	lesson: "H6",
    	evidence: "none yet",
    };

    export default (pi: PiLike) =>
    	installGuard(pi, (call) => {
    		if (call.toolName !== "edit" && call.toolName !== "write") return undefined;
    		const path = String((call.input as any)?.path ?? "");
    		if (!/(^|\/)tests\//.test(path)) return undefined;
    		return { block: true, reason: `${path} is the acceptance test and cannot change. Fix the code so it passes.` };
    	});
    ```

    Its test, in the style of `tests/remedy-units.test.mjs`:

    ```js
    const pi = fakePi();
    (await import("../remedies/guard/keep-tests.ts")).default(pi);
    assert.equal(pi.fire("tool_call", { toolName: "edit", input: { path: "tests/test_app.py" } })?.block, true);
    assert.equal(pi.fire("tool_call", { toolName: "edit", input: { path: "app.py" } }), undefined);
    ```

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. Your unit passes this lesson when its challenge
fails with the *before* line and passes with yours. Until then, submit what a
reviewer can check: by pull request, the unit and its test, the `run.json` of
every session before and after, and a note on the failure it fixes. A
submitted remedy that measurably helps is the start of a new lesson.

## Interpretation

The weakest badge is `conjecture`: a unit is a claim until its before and
after are run. This is the end of the track. You now have every tool and
remedy the course teaches, `preset:hard`, and the means to add your own:
everything [The Challenge](../../challenge/index.md) needs.

### Run it yourself

Test the unit, then run before and after with your file:

```bash
node --test tests/remedy-units.test.mjs
uv run python learn/code/harness.py run --suite medium --remedy preset:hard --repeat 3 --grade
uv run python learn/code/harness.py run --suite medium --remedy preset:hard --extension path/to/your-remedy.ts --repeat 3 --grade
```

!!! success "Key points"

    - A remedy unit is a default export taking `pi`, one hook (a guard on `tool_call` or a nudge), and a `meta` record.
    - Test it with a fake `pi` before any model sees it: it blocks the bad call and allows a good one.
    - Submit the unit, its test, the before and after `run.json` files and a note by pull request; then take on The Challenge.
