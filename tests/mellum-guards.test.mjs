import assert from "node:assert/strict";
import { appendFileSync, mkdtempSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

// Nothing in this file may write ~/.pi/agent or reach a server: recording is off unless a test turns it on.
process.env.MELLUM_WORKER_RUNS = "0";
const noServer = () => Promise.reject(new Error("no server in tests"));

import { createLoopBreaker, createStepBudget, newFileOnlyWrite, confineSearch, isTreeWalk, absolutePathArgs } from "../extensions/mellum-guards.ts";

test("confineSearch blocks a recursive search that reaches outside the workspace", () => {
	const guard = confineSearch("/work/ws");
	// the exact pathology that hung the Flint run: grep -r across the whole machine
	const d = guard({ toolName: "bash", input: { command: 'grep -rl "totalCents" /Users /var/tmp /work/ws' } });
	assert.ok(d?.block);
	assert.match(d.reason, /outside your workspace/i);
	assert.match(d.reason, /\/Users/);
});

test("confineSearch allows a tree-walk confined to the workspace", () => {
	const guard = confineSearch("/work/ws");
	assert.equal(guard({ toolName: "bash", input: { command: "grep -rl pattern ." } }), undefined); // relative
	assert.equal(guard({ toolName: "bash", input: { command: "find /work/ws/src -name '*.py'" } }), undefined); // under root
	assert.equal(guard({ toolName: "bash", input: { command: "cat /etc/hosts" } }), undefined); // not a tree-walk
});

test("isTreeWalk detects find/recursive grep/rg/ls -R, not a plain grep", () => {
	assert.ok(isTreeWalk("find / -name x"));
	assert.ok(isTreeWalk("grep -rl x /Users"));
	assert.ok(isTreeWalk("grep -R x ."));
	assert.ok(isTreeWalk("rg pattern /var"));
	assert.ok(isTreeWalk("ls -R /"));
	assert.ok(!isTreeWalk("grep pattern app.py")); // non-recursive grep is fine
	assert.ok(!isTreeWalk("cat /etc/hosts"));
});

test("absolutePathArgs finds absolute tokens but not quoted sed regexes", () => {
	assert.deepEqual(absolutePathArgs("grep -rl x /Users /var/tmp ."), ["/Users", "/var/tmp"]);
	assert.deepEqual(absolutePathArgs("sed 's/a/b/' file.txt"), []); // the regex starts with a quote, not /
});

test("write to an existing path is blocked with the fact", () => {
	const guard = newFileOnlyWrite((p) => p === "a.py");
	assert.equal(guard({ toolName: "write", input: { path: "b.py" } }), undefined);
	const decision = guard({ toolName: "write", input: { path: "a.py" } });
	assert.ok(decision.block);
	assert.match(decision.reason, /replaces the entire file/);
});

test("loop breaker trips on the sixth identical call, success or not", () => {
	const guard = createLoopBreaker(20, 5);
	const call = { toolName: "read", input: { path: "x" } };
	for (let i = 0; i < 5; i++) assert.equal(guard(call), undefined);
	assert.ok(guard(call).block);
});

test("loop breaker ignores differing calls", () => {
	const guard = createLoopBreaker(20, 5);
	for (let i = 0; i < 10; i++) assert.equal(guard({ toolName: "read", input: { path: `f${i}` } }), undefined);
});

test("step budget blocks after N calls", () => {
	const guard = createStepBudget(2);
	const call = { toolName: "ls", input: {} };
	assert.equal(guard(call), undefined);
	assert.equal(guard(call), undefined);
	assert.ok(guard(call).block);
});

test("empty-final nudge fires only on an assistant turn with no text and no tool call, up to the cap", async () => {
	const { createEmptyFinalNudge } = await import("../extensions/mellum-guards.ts");
	const nudge = createEmptyFinalNudge(2);
	const empty = { role: "assistant", content: [{ type: "thinking", thinking: "..." }] };
	const withText = { role: "assistant", content: [{ type: "text", text: "Done." }] };
	const withCall = { role: "assistant", content: [{ type: "toolCall", name: "read" }] };
	assert.equal(nudge(withText), undefined);
	assert.equal(nudge(withCall), undefined);
	assert.equal(nudge({ role: "user", content: "hi" }), undefined);
	const first = nudge(empty);
	assert.ok(first.continue);
	assert.equal(first.entries[0].type, "custom_message");
	assert.match(first.entries[0].content, /exits 0/);
	assert.ok(nudge(empty).continue);
	assert.equal(nudge(empty), undefined);
});

test("MELLUM_GUARDS env overrides ENABLED for live smokes", async () => {
	const { resolveEnabled } = await import("../extensions/mellum-guards.ts");
	assert.deepEqual(resolveEnabled({ emptyFinalNudge: 2 }, '{"stepBudget":1}'), { stepBudget: 1 });
	assert.deepEqual(resolveEnabled({ emptyFinalNudge: 2 }, undefined), { emptyFinalNudge: 2 });
	assert.deepEqual(resolveEnabled({ emptyFinalNudge: 2 }, "not json"), { emptyFinalNudge: 2 });
});

test("adapter nudges from agent_before_settle when the last assistant turn was empty", async () => {
	const { default: install } = await import("../extensions/mellum-guards.ts");
	const handlers = {};
	install({ on: (name, fn) => { handlers[name] = fn; } }, { fetch: noServer });
	const empty = { role: "assistant", content: [{ type: "thinking", thinking: "..." }, { type: "text", text: "\n\n" }] };
	const done = { role: "assistant", content: [{ type: "text", text: "Done." }] };
	handlers.turn_end({ message: empty, context: { canContinue: false }, outcome: "completed" });
	const first = handlers.agent_before_settle({ context: { canContinue: false }, outcome: "completed" });
	assert.ok(first?.continue, "empty last turn must trigger a continuation");
	handlers.turn_end({ message: done, context: { canContinue: false }, outcome: "completed" });
	assert.equal(handlers.agent_before_settle({ context: { canContinue: false }, outcome: "completed" }), undefined);
});

test("loop breaker forgets repeats once an edit, write, or bash call may have changed the result", () => {
	const guard = createLoopBreaker(20, 5);
	const read = { toolName: "read", input: { path: "x" } };
	for (let i = 0; i < 5; i++) assert.equal(guard(read), undefined);
	assert.equal(guard({ toolName: "edit", input: { path: "x", edits: [] } }), undefined);
	assert.equal(guard(read), undefined, "a re-read after an edit is not a repeat");
	for (let i = 0; i < 4; i++) assert.equal(guard(read), undefined);
	assert.ok(guard(read).block, "five unbroken repeats after the edit still trip it");
});

test("an edit/test loop never trips the loop breaker", () => {
	const guard = createLoopBreaker(20, 5);
	for (let i = 0; i < 12; i++) {
		assert.equal(guard({ toolName: "edit", input: { path: "a.py", edits: [{ oldText: String(i) }] } }), undefined);
		assert.equal(guard({ toolName: "bash", input: { command: "uv run --offline pytest -q" } }), undefined);
	}
});

test("empty-final nudge leaves aborted or errored turns alone", async () => {
	const { createEmptyFinalNudge } = await import("../extensions/mellum-guards.ts");
	const nudge = createEmptyFinalNudge(3);
	const content = [{ type: "thinking", thinking: "..." }];
	assert.equal(nudge({ role: "assistant", stopReason: "aborted", content }), undefined);
	assert.equal(nudge({ role: "assistant", stopReason: "error", content }), undefined);
	assert.ok(nudge({ role: "assistant", stopReason: "stop", content }).continue);
});

test("createGuardSet bundles tool_call, turn_end and settle decisions with fresh state", async () => {
	const { createGuardSet } = await import("../extensions/mellum-guards.ts");
	const set = createGuardSet({ loopBreaker: true, emptyFinalNudge: 1 });
	const read = { toolName: "read", input: { path: "x" } };
	for (let i = 0; i < 5; i++) assert.equal(set.toolCall(read), undefined);
	assert.ok(set.toolCall(read).block, "sixth identical call is blocked");
	set.turnEnd({ message: { role: "assistant", content: [{ type: "thinking", thinking: "." }] } });
	assert.ok(set.beforeSettle()?.continue, "empty final turn is nudged");
	assert.equal(set.beforeSettle(), undefined, "nudge is consumed");
	const fresh = createGuardSet({ loopBreaker: true });
	assert.equal(fresh.toolCall(read), undefined, "a new set has no memory of the old one");
});

// ---- the Worker run recorder -------------------------------------------------------------

const BRIEF = "Add a greeting to app.py. Test command: uv run pytest -q";
const SYSTEM = "<!-- mellum-worker prompt v7 -->\nYou are a bounded coding worker.";
const ctx = { mode: "json", model: { provider: "omlx", id: "mellum" } };
const textBlock = (text) => ({ type: "text", text });
const call = (id, name, args) => ({ type: "toolCall", id, name, arguments: args });
const assistant = (content, extra = {}) => ({ role: "assistant", content, stopReason: "stop", timestamp: 1000, usage: { input: 10, cacheRead: 0, output: 5 }, ...extra });
const result = (id, text, isError = false) => ({ role: "toolResult", toolCallId: id, isError, content: [textBlock(text)] });
const tmpFile = () => join(mkdtempSync(join(tmpdir(), "mellum-guards-")), "runs.jsonl");
const lines = (file) => readFileSync(file, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));

async function installDefault(fetchImpl = noServer) {
	const { default: install } = await import("../extensions/mellum-guards.ts");
	const handlers = {};
	install({ on: (name, fn) => { handlers[name] = fn; } }, { fetch: fetchImpl });
	return handlers;
}
const sequence = () => [
	{ message: assistant([call("c1", "bash", { command: "uv run pytest -q" })], { stopReason: "toolUse" }), toolResults: [result("c1", "1 failed", true)] },
	{ message: assistant([call("c2", "edit", { path: "app.py", edits: [] })], { stopReason: "toolUse" }), toolResults: [result("c2", "ok")] },
	{ message: assistant([call("c3", "write", { path: "new.py", content: "x" })], { stopReason: "toolUse" }), toolResults: [result("c3", "ok")] },
	{ message: assistant([call("c4", "bash", { command: "uv run pytest -q" })], { stopReason: "toolUse" }), toolResults: [result("c4", "1 passed")] },
	{ message: assistant([{ type: "thinking", thinking: "..." }]) },
	{ message: assistant([textBlock("Done: app.py, new.py. 1 passed.")]) },
];

async function runThroughPi(handlers) {
	const returns = [];
	const out = (name, value) => returns.push([name, JSON.stringify(value) ?? "undefined"]);
	const read = { toolName: "read", input: { path: "x" } };
	for (let i = 0; i < 6; i++) out("tool_call", handlers.tool_call(read, ctx));
	for (const { message, toolResults = [] } of sequence()) {
		out("turn_end", handlers.turn_end({ message, toolResults }, ctx));
		out("agent_before_settle", handlers.agent_before_settle({ context: { canContinue: false } }, ctx));
	}
	return returns;
}

test("the default export applies the guards through Pi's listeners", async () => {
	const returns = await runThroughPi(await installDefault());
	assert.ok(returns.some(([name, v]) => name === "tool_call" && v.includes('"block":true')), "the loop breaker did block");
	assert.ok(returns.some(([name, v]) => name === "agent_before_settle" && v.includes('"continue":true')), "the nudge did fire");
});
