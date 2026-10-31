---
title: Build a Tool
tier: hard
number: H5
time: 5 min read · 30 min to build · 1 h to run
track: lessons
position: 5
prerequisites: [lessons/hard/best-of-n]
authors: [Andre van Zuydam]
backends: [vllm]
---

# H5 · Build a Tool

Every tool in this course is a small TypeScript file that hands the model one
new capability. This lesson takes the smallest real one, lookup, apart and has
you write your own, and your file is the after.

!!! abstract "Overview"

    **Questions**

    - What is a tool, in code, and how does Pi offer it to the model?
    - Where does my own tool go, and how do I load it into a run?

    **Objectives**

    - Read the anatomy of `pi.registerTool`: name, description, parameters, `execute`.
    - Write a tool of your own with a `meta` record, in the shape of a remedy unit.
    - Load it with `--extension` on top of `preset:hard` and run a level.

![A small robot at a workbench assembling a new tool, a blueprint pinned on the wall above](../../assets/illustrations/build-a-tool.webp){ .illustration }

## Problem

**Badge:** `conjecture`

The model can only do what its tools let it do. When it keeps failing for want
of something it cannot see (an installed library's real defaults, a fixture's
real columns), no prompt line gives it that. A tool can: one call, one bounded
answer.

## Eval case

**Badge:** `conjecture`

**Before:** `--remedy preset:hard`. **After:** the same line plus
`--extension your-tool.ts`, your own file. The lesson's own challenge is a
task only a new tool can pass; it is not built yet (planned), so
for now both runs are on Bronze and Silver.

## Evidence of the problem

**Badge:** `conjecture`

Nothing here is measured. `lookup` exists because the model guessed an API it
never saw, such as a redirect status default; as a remedy it is unit-tested
but not measured on the suites. Your tool starts from the same place: a
failure you named in a trace ([S0](../start-here.md#reading-a-real-failure)).

## Solution

**Badge:** `conjecture`

**Remedy unit:** none: you write it; the worked example is `extensions/mellum-knowledge.ts` (`lookup`, packaged as `tool/lookup-library-docs`).

**Lesson check:** not built yet. A small challenge of this lesson's own,
failing without the remedy and passing with it, is planned; until
then the evidence below is the suites'.

A tool file has a default export that takes `pi` and registers the tool.
Here is `lookup`'s call, abridged (the real one also takes `k` and
`rebuild`, and warms its index on `session_start`):

```ts
pi.registerTool({
	name: "lookup",
	label: "Docs lookup",
	description: "Look up a library API in the INSTALLED packages … Use it BEFORE guessing an unfamiliar API …",
	parameters: { type: "object", properties: { query: { type: "string", description: "the API/library question" } }, required: ["query"], additionalProperties: false },
	async execute(_id: string, params: any) {
		const text = await runLookup(String(params?.query ?? ""), 4, process.cwd());
		return { content: [{ type: "text", text }] };
	},
});
```

- **`description`** is the only instruction the model gets: say what it
  returns and when to call it.
- **`parameters`** is a JSON schema; keep it small, since a small model writes
  long arguments badly.
- **`execute`** returns text. Bound it, and say so when nothing was found.

Give your file the shape of a remedy unit, a default export taking `pi` and a
`meta` record (`pathology`, `does`, `lesson`, `evidence`), and put it
anywhere. One trap: `context/narrow-tools` keeps only the seven worker tools
and drops every other tool from the request, `lookup` included. If your line
carries it, the model never sees your tool.

??? example "A reference solution"

    Try your own first. This one gives the model the test result without the
    noise: it runs the tests and returns only the tail.

    ```ts
    import { spawn } from "node:child_process";

    export const meta = {
    	pathology: "Reads a long test log and loses the failure in it",
    	does: "Adds run_tests: runs pytest and returns the last 40 lines",
    	lesson: "H5",
    	evidence: "none yet",
    };

    export default function (pi: any): void {
    	pi.registerTool({
    		name: "run_tests",
    		label: "Run tests",
    		description: "Run the project's tests and return the last 40 lines of output. Call it after every change.",
    		parameters: { type: "object", properties: {}, additionalProperties: false },
    		async execute() {
    			const text = await new Promise<string>((resolve) => {
    				const child = spawn("uv", ["run", "python", "-m", "pytest", "-q"], { cwd: process.cwd() });
    				let out = "";
    				child.stdout.on("data", (c: Buffer) => (out += c.toString()));
    				child.stderr.on("data", (c: Buffer) => (out += c.toString()));
    				child.on("close", () => resolve(out.trim().split("\n").slice(-40).join("\n") || "(no output)"));
    				child.on("error", (e) => resolve(`(could not run tests: ${e.message})`));
    			});
    			return { content: [{ type: "text", text }] };
    		},
    	});
    }
    ```

## Validation

**Badge:** `conjecture`

Not measured as a lesson yet. No arm has run, so there is no n to report. Your tool passes this lesson when its challenge
fails with the *before* line and passes with yours; until that challenge
exists, a pass on Bronze or Silver shows the tool runs, not that it helped.
Read the trace for your tool's calls before you credit it.

## Interpretation

The weakest badge is `conjecture`: this lesson teaches a shape, not a result.
A tool earns its place the way every remedy here did: name the failure, add
one thing, and show the before and after on the same command.

### Run it yourself

Before, then after with your file:

```bash
uv run python learn/code/harness.py run --suite medium --remedy preset:hard --repeat 3 --grade
uv run python learn/code/harness.py run --suite medium --remedy preset:hard --extension path/to/your-tool.ts --repeat 3 --grade
```

!!! success "Key points"

    - A tool is a default export that calls `pi.registerTool` with a name, a description, a schema and `execute`.
    - The description is the model's only instruction for it; keep the parameters small and the output bounded.
    - Load your file with `--extension`, and leave `context/narrow-tools` out or it drops your tool.
