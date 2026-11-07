import { test } from "node:test";
import assert from "node:assert/strict";

import { parseOverride, applyOverride } from "../extensions/mellum-override.ts";

test("parseOverride: reads system and append; blanks and junk are no-override", () => {
	assert.deepEqual(parseOverride('{"system":"be terse"}'), { system: "be terse" });
	assert.deepEqual(parseOverride('{"append":"also cite files"}'), { append: "also cite files" });
	assert.deepEqual(parseOverride('{"system":"  "}'), {});
	assert.deepEqual(parseOverride("not json"), {});
});

test("applyOverride: system replaces the existing system prompt", () => {
	const msgs = [
		{ role: "system", content: "original" },
		{ role: "user", content: "do the task" },
	];
	const out = applyOverride(msgs, { system: "replaced" });
	assert.equal(out[0].content, "replaced");
	assert.equal(out[1].content, "do the task");
	assert.equal(msgs[0].content, "original"); // input not mutated
});

test("applyOverride: append adds to the existing system prompt", () => {
	const out = applyOverride([{ role: "system", content: "base" }], { append: "extra" });
	assert.equal(out[0].content, "base\n\nextra");
});

test("applyOverride: inserts a system message when none exists", () => {
	const out = applyOverride([{ role: "user", content: "hi" }], { system: "you are a worker" });
	assert.equal(out[0].role, "system");
	assert.equal(out[0].content, "you are a worker");
	assert.equal(out[1].role, "user");
});

test("applyOverride: system wins, then append is added onto it", () => {
	const out = applyOverride([{ role: "system", content: "old" }], { system: "new", append: "note" });
	assert.equal(out[0].content, "new\n\nnote");
});

test("applyOverride: no override leaves the messages untouched", () => {
	const msgs = [{ role: "system", content: "keep" }];
	assert.equal(applyOverride(msgs, {}), msgs);
});
