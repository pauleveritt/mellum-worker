import { test } from "node:test";
import assert from "node:assert/strict";

import { applyAdjustment, lastPrompt } from "../extensions/mellum-replay.ts";

test("applyAdjustment: appends the note to the system prompt, leaves the task", () => {
	const out = applyAdjustment({ system: "You make one test pass.", task: "Make X pass." }, "prefer edit over write");
	assert.match(out.system, /Replay adjustment: prefer edit over write/);
	assert.equal(out.task, "Make X pass.");
});

test("applyAdjustment: an empty adjustment is a no-op", () => {
	const p = { system: "S", task: "T" };
	assert.deepEqual(applyAdjustment(p, "   "), p);
});

test("lastPrompt: returns the most recent prompt event in the feed", () => {
	const feed = [
		JSON.stringify({ t: 1, kind: "prompt", system: "old", task: "old task" }),
		JSON.stringify({ t: 2, kind: "turn", think: "x" }),
		JSON.stringify({ t: 3, kind: "prompt", system: "new", task: "new task" }),
	].join("\n");
	const p = lastPrompt(feed);
	assert.equal(p.system, "new");
	assert.equal(p.task, "new task");
});
