import assert from "node:assert/strict";
import test from "node:test";

import {
	createQualityCheck,
	parseRuff,
	qualityMessage,
	resolveConfig,
} from "../extensions/mellum-quality.ts";

const F811 = "app.py:240:1: F811 Redefinition of unused `grade` from line 212";
const F821 = "report.py:9:12: F821 Undefined name `totals`";

test("parseRuff reads concise lines into violations and ignores the summary", () => {
	const out = `${F811}\n${F821}\nFound 2 errors.\n`;
	const violations = parseRuff(out);
	assert.equal(violations.length, 2);
	assert.deepEqual(violations[0], {
		file: "app.py",
		line: 240,
		col: 1,
		code: "F811",
		message: "Redefinition of unused `grade` from line 212",
	});
	assert.equal(violations[1].code, "F821");
});

test("parseRuff returns nothing for clean output", () => {
	assert.deepEqual(parseRuff("All checks passed!\n"), []);
	assert.deepEqual(parseRuff(""), []);
});

test("qualityMessage lists each violation and explains F811 when present", () => {
	const message = qualityMessage(parseRuff(`${F811}\n`));
	assert.match(message, /F811/);
	assert.match(message, /app\.py:240/);
	assert.match(message, /silently replaces/); // the shadow explanation
	assert.match(message, /fix/i);
});

test("qualityMessage omits the F811 note when there is no F811", () => {
	const message = qualityMessage(parseRuff(`${F821}\n`));
	assert.match(message, /F821/);
	assert.doesNotMatch(message, /silently replaces/);
});

test("the check nudges once per violation set, up to the cap, then settles", () => {
	const check = createQualityCheck(2, () => `${F811}\n`, "/ws");
	const first = check();
	assert.ok(first?.continue, "a violation produces a continuation");
	assert.equal(first.entries[0].customType, "mellum-quality");
	assert.match(first.entries[0].content, /F811/);
	assert.ok(check()?.continue, "second is still within the cap");
	assert.equal(check(), undefined, "the cap bounds the nudges");
});

test("the check settles quietly when the lint is clean", () => {
	const check = createQualityCheck(3, () => "", "/ws");
	assert.equal(check(), undefined);
});

test("the check degrades (never blocks) when ruff cannot run", () => {
	const missing = createQualityCheck(3, () => null, "/ws");
	assert.equal(missing(), undefined, "a null runner (ruff absent) must not block the worker");
	const threw = createQualityCheck(3, () => { throw new Error("ENOENT"); }, "/ws");
	assert.equal(threw(), undefined, "a throwing runner must not block the worker");
});

test("resolveConfig reads MELLUM_QUALITY, defaults, and tolerates junk", () => {
	assert.deepEqual(resolveConfig(undefined), { max: 2, select: "F,E9" });
	assert.deepEqual(resolveConfig('{"max":1,"select":"F"}'), { max: 1, select: "F" });
	assert.deepEqual(resolveConfig("not json"), { max: 2, select: "F,E9" });
});

test("the default export nudges from agent_before_settle on a real error", async () => {
	const { default: install } = await import("../extensions/mellum-quality.ts");
	const handlers = {};
	install({ on: (name, fn) => { handlers[name] = fn; } }, { run: () => `${F811}\n`, cwd: "/ws" });
	const decision = handlers.agent_before_settle({ context: { canContinue: false } });
	assert.ok(decision?.continue, "a settling run with a real error is sent back to fix it");
	assert.match(decision.entries[0].content, /F811/);
});

test("the default export settles quietly when the worker's code is clean", async () => {
	const { default: install } = await import("../extensions/mellum-quality.ts");
	const handlers = {};
	install({ on: (name, fn) => { handlers[name] = fn; } }, { run: () => "", cwd: "/ws" });
	assert.equal(handlers.agent_before_settle({ context: { canContinue: false } }), undefined);
});
