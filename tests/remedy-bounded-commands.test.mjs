import { test } from "node:test";
import assert from "node:assert/strict";

/** A fake Pi that records the hooks a unit installs, then drives them. */
function fakePi() {
	const handlers = {};
	const tools = [];
	return {
		handlers,
		tools,
		on(event, handler) { (handlers[event] ??= []).push(handler); },
		registerTool(tool) { tools.push(tool); },
		events() { return Object.keys(handlers).sort(); },
		fire(event, payload) { return handlers[event]?.map((h) => h(payload)).find((r) => r !== undefined); },
	};
}

async function installed() {
	const unit = await import("../remedies/tool/bounded-commands.ts");
	const pi = fakePi();
	unit.default(pi);
	return { unit, pi };
}

test("tool/bounded-commands installs one tool_call hook and registers no tool", async () => {
	const { pi } = await installed();
	assert.deepEqual(pi.events(), ["tool_call"]);
	assert.equal(pi.handlers.tool_call.length, 1);
	assert.equal(pi.tools.length, 0);
});

test("tool/bounded-commands gives a bash call without a timeout Pi's own bound, and never blocks", async () => {
	const { unit, pi } = await installed();
	const event = { toolName: "bash", input: { command: "uv run --frozen python app.py" } };
	assert.equal(pi.fire("tool_call", event), undefined);
	assert.equal(event.input.timeout, unit.DEFAULT_TIMEOUT_SECONDS);
	assert.equal(unit.DEFAULT_TIMEOUT_SECONDS, 30);
});

test("tool/bounded-commands keeps a timeout the model chose, up to the cap", async () => {
	const { pi } = await installed();
	const event = { toolName: "bash", input: { command: "uv sync --frozen", timeout: 90 } };
	pi.fire("tool_call", event);
	assert.equal(event.input.timeout, 90);
});

test("tool/bounded-commands caps a chosen timeout below the harness stall cutoff", async () => {
	// The overnight's one bound-arm stall: the model set timeout 300 on `uvicorn --reload`.
	const { unit, pi } = await installed();
	const event = { toolName: "bash", input: { command: "uvicorn app:app --reload", timeout: 300 } };
	pi.fire("tool_call", event);
	assert.equal(event.input.timeout, unit.MAX_TIMEOUT_SECONDS);
	assert.equal(unit.MAX_TIMEOUT_SECONDS, 120);
});

test("tool/bounded-commands leaves other tools alone", async () => {
	const { pi } = await installed();
	const event = { toolName: "read", input: { path: "app.py" } };
	pi.fire("tool_call", event);
	assert.deepEqual(event.input, { path: "app.py" });
});

test("tool/bounded-commands carries the metadata the remedies list is generated from", async () => {
	const { unit } = await installed();
	for (const key of ["pathology", "does", "lesson", "evidence"]) assert.equal(typeof unit.meta[key], "string");
	for (const key of ["pathology", "does", "evidence"]) assert.ok(unit.meta[key].length > 0, key);
});

test("tool/bounded-commands takes its seconds from MELLUM_BOUND_SECONDS when set", async () => {
	const unit = await import("../remedies/tool/bounded-commands.ts");
	const pi = fakePi();
	process.env.MELLUM_BOUND_SECONDS = "10";
	try { unit.default(pi); } finally { delete process.env.MELLUM_BOUND_SECONDS; }
	const event = { toolName: "bash", input: { command: "python app.py" } };
	pi.fire("tool_call", event);
	assert.equal(event.input.timeout, 10);
});

test("tool/bounded-commands clamps a configured MELLUM_BOUND_SECONDS to the cap", async () => {
	// F.8: MELLUM_BOUND_SECONDS=300 installed 300 when the model set none, past the 120 s cap.
	const unit = await import("../remedies/tool/bounded-commands.ts");
	const pi = fakePi();
	process.env.MELLUM_BOUND_SECONDS = "300";
	try { unit.default(pi); } finally { delete process.env.MELLUM_BOUND_SECONDS; }
	const event = { toolName: "bash", input: { command: "python app.py" } };
	pi.fire("tool_call", event);
	assert.equal(event.input.timeout, unit.MAX_TIMEOUT_SECONDS);
});

test("tool/bounded-commands gives the bound to a chosen timeout that is not a positive number", async () => {
	// Pi runs a bash call with no timeout at all unless the timeout is above 0.
	const { unit, pi } = await installed();
	for (const bad of [0, -1, Number.NaN, Number.POSITIVE_INFINITY, "600", "soon", true]) {
		const event = { toolName: "bash", input: { command: "uvicorn app:app", timeout: bad } };
		pi.fire("tool_call", event);
		assert.equal(event.input.timeout, unit.DEFAULT_TIMEOUT_SECONDS, String(bad));
	}
});

test("tool/bounded-commands ignores a MELLUM_BOUND_SECONDS that is not a positive number", async () => {
	const unit = await import("../remedies/tool/bounded-commands.ts");
	for (const bad of ["0", "-5", "soon", ""]) {
		const pi = fakePi();
		process.env.MELLUM_BOUND_SECONDS = bad;
		try { unit.default(pi); } finally { delete process.env.MELLUM_BOUND_SECONDS; }
		const event = { toolName: "bash", input: { command: "python app.py" } };
		pi.fire("tool_call", event);
		assert.equal(event.input.timeout, unit.DEFAULT_TIMEOUT_SECONDS, bad);
	}
});
