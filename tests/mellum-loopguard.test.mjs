import assert from "node:assert/strict";
import test from "node:test";

import loopguard from "../extensions/mellum-loopguard.ts";

/** Drive the extension's default export with a fake `pi`, returning the tool_call handler pi would call. */
function handlerFor() {
	let handler;
	loopguard({ on: (ev, fn) => { if (ev === "tool_call") handler = fn; } });
	return handler;
}

test("loopguard blocks an exact-repeat runaway at the loop-breaker threshold", () => {
	const h = handlerFor();
	let blockedAt = 0;
	for (let i = 1; i <= 8 && !blockedAt; i++) {
		if (h({ toolName: "ls", input: { path: "." } })?.block) blockedAt = i;
	}
	assert.equal(blockedAt, 6); // threshold 5 → the 6th identical call is blocked
});

test("loopguard blocks a VARYING-arg runaway via the step budget (the exact-match breaker misses it)", () => {
	// The measured pathology: a model re-issues reads with a DISTINCT arg every time, so no call
	// is ever identical and the loop-breaker never fires. The step budget is the arg-agnostic
	// backstop that caps total calls and forces the phase to stop and emit.
	const h = handlerFor();
	let blockedAt = 0;
	for (let i = 1; i <= 400 && !blockedAt; i++) {
		if (h({ toolName: "ls", input: { path: `./probe_${i}` } })?.block) blockedAt = i;
	}
	assert.ok(blockedAt > 40, "the budget must sit above a healthy phase's call count");
	assert.ok(blockedAt <= 66, `capped at the budget, blocked at ${blockedAt}`);
});

test("loopguard does not block a healthy read phase (many DISTINCT reads, under budget)", () => {
	const h = handlerFor();
	for (let i = 0; i < 40; i++) {
		const d = h({ toolName: "read", input: { path: `file_${i}.py` } });
		assert.ok(!d?.block, `distinct read ${i} must not be blocked`);
	}
});
