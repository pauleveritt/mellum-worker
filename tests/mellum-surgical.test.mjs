import assert from "node:assert/strict";
import test from "node:test";

import {
	capVerdict,
	churnFraction,
	createSurgicalGuard,
	growthRatio,
	resolveCaps,
} from "../extensions/mellum-surgical.ts";

const line = (n) => Array.from({ length: n }, (_, i) => `line ${i}`).join("\n");

test("churnFraction and growthRatio measure real change, not reformatting", () => {
	assert.equal(growthRatio("a\nb", "a\nb\nc\nd"), 2); // 2 lines -> 4
	assert.equal(churnFraction("a\nb\nc", "a\nb\nc"), 0); // identical
	assert.ok(churnFraction("a\nb\nc\nd", "w\nx\ny\nz") > 0.9); // full rewrite
});

test("capVerdict: a small targeted change passes", () => {
	const before = line(20);
	const after = before.replace("line 5", "line 5 CHANGED") + "\nline 20 added";
	const v = capVerdict(before, after, { maxChurn: 0.5, maxGrowth: 3 });
	assert.equal(v.ok, true, v.reason);
});

test("capVerdict: a legit addition (new routes/fields) passes churn", () => {
	const before = line(20);
	const after = before + "\n" + line(12); // added ~12 lines, existing untouched
	const v = capVerdict(before, after, { maxChurn: 0.5, maxGrowth: 3 });
	assert.equal(v.ok, true, "adding to a file is not a clobber");
});

test("capVerdict: a full rewrite trips churn", () => {
	const before = line(40);
	const after = Array.from({ length: 40 }, (_, i) => `different ${i}`).join("\n");
	const v = capVerdict(before, after, { maxChurn: 0.5, maxGrowth: 3 });
	assert.equal(v.ok, false);
	assert.match(v.reason, /rewrote|regeneration/);
});

test("capVerdict: a tripled file trips growth (a duplicated copy)", () => {
	const before = line(10);
	const after = line(40);
	const v = capVerdict(before, after, { maxChurn: 0.9, maxGrowth: 3 });
	assert.equal(v.ok, false);
	assert.match(v.reason, /longer|copy/);
});

test("the guard allows a write to a NEW file (nothing to clobber)", () => {
	const guard = createSurgicalGuard({ maxChurn: 0.5, maxGrowth: 3 }, () => null);
	assert.equal(guard({ toolName: "write", input: { path: "new.py", content: line(50) } }), undefined);
});

test("the guard allows a small change and a legit addition to an existing file", () => {
	const before = line(20);
	const guard = createSurgicalGuard({ maxChurn: 0.5, maxGrowth: 3 }, () => before);
	assert.equal(guard({ toolName: "write", input: { path: "app.py", content: before + "\nx" } }), undefined);
});

test("the guard blocks a clobbering write (942 lines -> 2) and steers to edit", () => {
	const before = line(942);
	const guard = createSurgicalGuard({ maxChurn: 0.5, maxGrowth: 3 }, () => before);
	const decision = guard({ toolName: "write", input: { path: "app.py", content: "line 0\nline 1" } });
	assert.ok(decision?.block, "a near-total rewrite of an existing file is blocked");
	assert.match(decision.reason, /edit/);
	assert.match(decision.reason, /app\.py/);
});

test("the guard ignores non-write tools and non-string content", () => {
	const guard = createSurgicalGuard({ maxChurn: 0.5, maxGrowth: 3 }, () => line(50));
	assert.equal(guard({ toolName: "edit", input: { path: "app.py" } }), undefined);
	assert.equal(guard({ toolName: "write", input: { path: "app.py" } }), undefined);
});

test("resolveCaps reads MELLUM_SURGICAL, defaults, tolerates junk", () => {
	assert.deepEqual(resolveCaps(undefined), { maxChurn: 0.5, maxGrowth: 3 });
	assert.deepEqual(resolveCaps('{"maxChurn":0.8}'), { maxChurn: 0.8, maxGrowth: 3 });
	assert.deepEqual(resolveCaps("nope"), { maxChurn: 0.5, maxGrowth: 3 });
});

test("the default export wires tool_call and blocks a clobber", async () => {
	const { default: install } = await import("../extensions/mellum-surgical.ts");
	const handlers = {};
	install({ on: (name, fn) => { handlers[name] = fn; } }, { read: () => line(900) });
	assert.ok(handlers.tool_call, "registers tool_call");
	const decision = handlers.tool_call({ toolName: "write", input: { path: "big.py", content: "tiny" } });
	assert.ok(decision?.block);
});
