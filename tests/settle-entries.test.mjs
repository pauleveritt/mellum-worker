import assert from "node:assert/strict";
import test from "node:test";

import guards from "../extensions/mellum-guards.ts";
import quality from "../extensions/mellum-quality.ts";
import verify from "../extensions/mellum-verify.ts";
import emptyTurn from "../remedies/nudge/empty-turn.ts";

const EMPTY_FINAL = { message: { role: "assistant", content: [], stopReason: "stop" } };
const redQuality = (pi) => quality(pi, { run: () => "app.py:3:1: F821 Undefined name `x`\n", cwd: "/tmp" });

/** A fake Pi whose settle merge is Pi 1.4.0's `emitBoundary` (runner.js:759): each handler sees the
 * entries so far in `event.entries`, and whatever entries it returns replace them. */
function fakePi() {
	const handlers = new Map();
	return {
		on(event, handler) {
			handlers.set(event, [...(handlers.get(event) ?? []), handler]);
		},
		async emit(event, payload) {
			for (const h of handlers.get(event) ?? []) await h(payload);
		},
		async settle() {
			let entries = [];
			let cont = false;
			for (const h of handlers.get("agent_before_settle") ?? []) {
				const result = await h({ type: "agent_before_settle", entries, continue: cont });
				if (result?.entries !== undefined) entries = result.entries;
				if (result?.continue !== undefined) cont = result.continue;
			}
			return { entries, continue: cont };
		},
	};
}

test("two red settle gates both reach the model, in load order", async () => {
	const pi = fakePi();
	redQuality(pi);
	guards(pi);
	await pi.emit("turn_end", EMPTY_FINAL);
	const { entries, continue: cont } = await pi.settle();
	assert.deepEqual(entries.map((e) => e.customType), ["mellum-quality", "mellum-guard"]);
	assert.equal(cont, true);
});

test("the empty-turn remedy keeps an earlier gate's message", async () => {
	const pi = fakePi();
	redQuality(pi);
	emptyTurn(pi);
	await pi.emit("turn_end", EMPTY_FINAL);
	const { entries } = await pi.settle();
	assert.deepEqual(entries.map((e) => e.customType), ["mellum-quality", "mellum-guard"]);
});

test("the mediated test keeps an earlier gate's message", async (t) => {
	const { mkdtempSync, writeFileSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const { join } = await import("node:path");
	const dir = mkdtempSync(join(tmpdir(), "mediated-src-"));
	writeFileSync(join(dir, "test_01_x.py"), "def test_x():\n    assert False\n");
	const saved = { test: process.env.MELLUM_MEDIATED_TEST, pytest: process.env.VERIFY_PYTEST };
	t.after(() => {
		for (const [k, v] of [["MELLUM_MEDIATED_TEST", saved.test], ["VERIFY_PYTEST", saved.pytest]]) {
			if (v === undefined) delete process.env[k];
			else process.env[k] = v;
		}
	});
	process.env.MELLUM_MEDIATED_TEST = join(dir, "test_01_x.py");
	process.env.VERIFY_PYTEST = "false"; // red without running pytest
	const { default: mediated } = await import("../remedies/check/mediated-test.ts");
	const pi = fakePi();
	redQuality(pi);
	mediated(pi);
	const { entries } = await pi.settle();
	assert.deepEqual(entries.map((e) => e.customType), ["mellum-quality", "mediated-test"]);
});

test("the verify gate keeps an earlier gate's message", async (t) => {
	const saved = { all: process.env.VERIFY_ALL, pytest: process.env.VERIFY_PYTEST };
	t.after(() => {
		for (const [k, v] of [["VERIFY_ALL", saved.all], ["VERIFY_PYTEST", saved.pytest]]) {
			if (v === undefined) delete process.env[k];
			else process.env[k] = v;
		}
	});
	process.env.VERIFY_ALL = "1";
	process.env.VERIFY_PYTEST = "false"; // a test command that always fails: the gate is red
	const pi = fakePi();
	redQuality(pi);
	verify(pi);
	const { entries } = await pi.settle();
	assert.deepEqual(entries.map((e) => e.customType), ["mellum-quality", "mellum-verify"]);
});
