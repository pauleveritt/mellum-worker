---
title: Thinking in the Content Channel
tier: medium
number: M5
time: 6 min read · 15 min to run
track: lessons
position: 5
prerequisites: [lessons/medium/the-runaway-search]
authors: [Andre van Zuydam]
backends: [llamacpp]
---

# Thinking in the Content Channel

The model thinks in a channel of its own, and the agent reads it separately from
what the model says. When a serving stack mislabels the thinking as speech, it
comes back as words the model said. And poisons the next turn. A repair moves it
back where it belongs.

!!! abstract "Overview"

    **Questions**

    - Why does the model's reasoning sometimes show up as its reply?
    - Whose fault is it, the model, or the thing serving it, and what fixes it?

    **Objectives**

    - Recognise a turn that opens with a literal `<think>` tag in the content.
    - Switch on `context/repair-think-tags`, read what it moves, and see the turn read clean again.

![A small robot sorting a tangled ribbon of thought bubbles and speech bubbles into two separate trays](../../assets/illustrations/reasoning-as-text.webp){ .illustration }

## Problem

**Badge:** `screen`

The model keeps two channels: the reasoning it does for itself, and the reply it
hands back. The agent reads the reasoning from a field the server fills, and never
scans the reply text for it. That split is the serving stack's job. When a host's
streaming parser misses the split, the reasoning comes back as plain text in the
reply, opened by a literal `<think>` tag. The agent then shows the thinking as the
answer, and sends it back next turn as a thing the model said. The private thought
is now on the record as speech, and every turn after it reads a little more
confused.

## Eval case

**Badge:** `screen`

**The condition:** a host whose streaming parser mislabels reasoning after the
first turn, so reply text arrives opened by `<think>`. **Before:** the leak stands.
The thinking is shown and fed back as speech. **After:**
`context/repair-think-tags`, which at message end moves a leading `<think>…</think>`
out of the reply and back into a thinking block, so the session, the display and
the next request all match a correctly served one.

## Evidence of the problem

**Badge:** `screen`

On a LAN vLLM host the leak was almost total: **236 of 244** turns came back with
the reasoning spilled into the reply, every turn after the first. On a pinned vLLM
0.32.0 it was **0 of 136**. The same model, a serving stack that labels the
channel correctly
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lan-reasoning-leak.md)).
That gap is the tell: it isn't the model thinking out loud, it's the host handing
back the wrong channel, and the model that can't choose its serving stack pays for
it in every poisoned turn.

## Solution

**Badge:** `screen`

One unit, `context/repair-think-tags`, does the serving stack's missed job at the
agent. At message end it looks at the reply; if it opens with `<think>`, it splits
the tag off, puts the thinking into a proper thinking block, and leaves the real
reply behind. A reply with no leading tag is returned untouched. On a host that
serves the channel correctly, it does nothing at all. It repairs the serving, not
the model's behaviour, so it is a context fix, not a remedy for a pathology the
model owns.

### The code

Switch it on live:

```text
/remedy on context/repair-think-tags
```

The repair is a split on the reply text, quoted from the file frozen at a commit
([`extensions/mellum-think-tags.ts`](https://github.com/andrevanzuydam/mellum-worker/blob/eba20ef/extensions/mellum-think-tags.ts)):

```ts
export function splitThinkTags(message) {
	if (message.role !== "assistant" || !Array.isArray(message.content)) return message;
	const content = [];
	for (const part of message.content) {
		const text = part.type === "text" ? part.text ?? "" : "";
		if (!text.trimStart().startsWith("<think>")) { content.push(part); continue; }
		const body = text.trimStart().slice("<think>".length);
		const end = body.indexOf("</think>");
		// Labelled "reasoning", as the agent labels the reasoning it streamed itself.
		content.push({ type: "thinking", thinkingSignature: "reasoning", thinking: end < 0 ? body : body.slice(0, end) });
		const rest = end < 0 ? "" : body.slice(end + "</think>".length).replace(/^\s+/, "");
		if (rest) content.push({ type: "text", text: rest });
	}
	return content.length ? { ...message, content } : message;
}
```

It runs on a `message_end` hook. The thinking block it builds is labelled the way
the agent labels reasoning it streamed itself, so the block goes back to the server
under the right field and the next turn sees a clean record. To screen it on a
graded run, name it: `--remedy context/repair-think-tags`.

**Lesson check:** a `<think>r</think>ok` reply becomes a thinking block plus `ok`,
and a plain `ok` is left alone. Proven at the unit grain
([test](https://github.com/andrevanzuydam/mellum-worker/blob/main/tests/remedy-units.test.mjs)).

## Validation

**Badge:** `screen`

The measured gap settles the cause: 236 of 244 turns leaked on the mislabelling
host, 0 of 136 on the host that labels the channel correctly, same model
([record](https://github.com/andrevanzuydam/mellum-worker/blob/main/docs/superpowers/research/2026-10-29-lan-reasoning-leak.md)).
The unit test settles the repair: the leaked reply splits into a thinking block and
the real text, and a clean reply is returned unchanged. The claim is narrow and
honest. This fixes a serving fault, so on a host that already serves the channel
right it is inert, and the right first move is always to pin a serving stack that
does the job.

## Interpretation

The weakest badge is `screen`. The lesson is a context error that isn't the model's
fault at all: the reasoning is sound, the serving stack just hands it back on the
wrong channel, and the agent faithfully feeds the mistake forward. It belongs on
Medium because it is a session-spend failure you only see by reading the trace. A
turn that opens with `<think>` is the whole tell. The evidence is a vLLM host, not
llama.cpp; the repair is general, but the right fix, where you can reach it, is the
serving stack itself.

### Run it yourself

Load the repair on a medium run; on a correctly served host it will do nothing,
which is the point:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker --remedy context/repair-think-tags --grade --repeat 3 --deadline 1200
```

!!! success "Key points"

    - The model's reasoning and its reply are two channels; a serving stack can mislabel one as the other.
    - `context/repair-think-tags` moves a leaked `<think>` reply back into a thinking block at message end.
    - 236 of 244 turns leaked on one host, 0 of 136 on a correctly serving one. Pin the serving stack first.
