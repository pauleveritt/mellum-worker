---
title: A Tool Result Too Big
tier: medium
number: M6
time: 5 min read · 15 min to run
track: lessons
position: 6
prerequisites: [lessons/medium/thinking-in-the-content-channel]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# A Tool Result Too Big

The model reads a whole file to find one line, and the file won't fit. So the
context fills, compacts, and the model reads it again. A unit trims the oversized
result and tells the model how to fetch only the part it needs.

!!! abstract "Overview"

    **Questions**

    - Why does reading a big file make the model read it twice?
    - How much of a result is worth keeping, and how does the model get the rest?

    **Objectives**

    - Follow a context that fills, compacts, and re-reads the same notes it just lost.
    - Switch on `context/trim-tool-output`, read the cap and the note it leaves, and watch the re-reads stop.

![A small robot trying to stuff an armful of thick books into a small backpack while pages spill out](../../assets/illustrations/context-overflow.webp){ .illustration }

## Problem

**Badge:** `screen`

The model wants one line and asks for the whole file. The result is too big for the
context to hold, so it crowds everything else out; the window fills, the agent
compacts to make room, and the thing the model was holding is gone. So it reads the
file again. In one context-overflow screen the model read eight notes whole,
compacted twice, and read the same eight notes a second time. A full lap, nothing
learnt, the budget half spent on carrying a file it only needed a line of.

## Eval case

**Badge:** `screen`

**The condition:** a session that reads a file or runs a command whose output is
larger than the context should hold. **Before:** the whole result lands in the
context and crowds it. **After:** `context/trim-tool-output`, which trims a result
over 8,000 characters, about 2,000 tokens, and appends a note on how to get the
rest. It trims only output the model asked to see: a `read`, `bash`, `grep`, `find`
or `ls`.

## Evidence of the problem

**Badge:** `screen`

The shape is a lap, not a crash: the context fills on an oversized read, compaction
throws the held content away, and the model re-reads what it just lost. The screen
behind this unit saw exactly that. Eight notes read whole, two compactions, the
eight notes read again. The lost work is invisible in the score; it shows up as
turns and context spent carrying bytes the model never needed.

## Solution

**Badge:** `screen`

One remedy unit, `context/trim-tool-output`, caps a single tool result at 8,000
characters and, where it cuts, leaves a note telling the model to fetch the part it
needs instead of the whole. The note is the important half: a trim with no way
forward just hides the file, but a trim that says *search it with `grep -n`, or read
a slice with offset and limit* turns a too-big read into a pointer the model can
act on.

### The code

Switch it on live:

```text
/remedy on context/trim-tool-output
```

The unit watches each tool result and rewrites one that runs over the cap, quoted
from the file frozen at a commit
([`remedies/context/trim-tool-output.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/remedies/context/trim-tool-output.ts#L15-L27)):

```ts
const LIMIT = 8000;                                      // ~2,000 tokens
const TRIMMED = new Set(["read", "bash", "grep", "find", "ls"]);

pi.on("tool_result", (event) => {
	if (!TRIMMED.has(event.toolName)) return undefined;
	const text = (event.content ?? []).filter((c) => c.type === "text").map((c) => c.text ?? "").join("");
	if (text.length <= LIMIT) return undefined;          // small enough, leave it
	const note = `\n\n[trimmed: showing ${LIMIT} of ${text.length} characters. ` +
		"Do not read the whole of it; get the part you need: search with `grep -n \"<what you need>\" <file>`, " +
		"or read a part with offset and limit.]";
	return { content: [{ type: "text", text: text.slice(0, LIMIT) + note }] };
});
```

The `TRIMMED` set is the restraint. Only output the model asked to see is cut, so a
file the model is *writing* is never trimmed out from under it. To screen it on a
graded run, name it: `--remedy context/trim-tool-output`.

**Lesson check:** a 40,571-character read is cut to 8,000 with a note that names
`grep -n` and `offset`. Proven at the unit grain
([test](https://github.com/andrevanzuydam/mellum-worker/blob/main/tests/remedy-units.test.mjs)).

## Validation

**Badge:** `screen`

The unit test pins it: a 40,571-character result is trimmed to 8,000, the note names
the ways to fetch the rest, a small result is left whole, and a file the model is
writing is never touched. That is the behaviour settled at n=1. The lap it prevents,
read, overflow, compact, re-read, was seen in the context-overflow screen; what
is owed is a preregistered run showing the trim holds the score while it saves the
turns, rather than a screen that only shows the overflow it targets.

## Interpretation

The weakest badge is `screen`. The error is a context one, pure and simple: the
model reaches for a whole file to answer a question about one line of it, and the
window can't carry the weight. The fix doesn't make the model smarter; it changes
what lands in the context, and hands back a pointer instead of a pile. It belongs on
Medium for the same reason the others do. You only see it by watching the session
spend its context, and the cheapest cure is to stop carrying what it doesn't need.

### Run it yourself

Load the trim on a medium run and watch the oversized reads shrink to a slice and a
note:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy context/trim-tool-output --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - An oversized read fills the context, compacts, and makes the model read the same file again.
    - `context/trim-tool-output` caps a result at 8,000 characters and leaves a note on how to get the rest.
    - It trims only output the model asked to see, so a file being written is never cut. Proven at the unit grain.
