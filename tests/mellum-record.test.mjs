import assert from "node:assert/strict";
import test from "node:test";
import { PACKAGE_VERSION, promptVersionOf, runRecord, spanStats } from "../extensions/mellum-record.ts";

const span = [
	{ role: "user", content: [{ type: "text", text: "fix the cart" }] },
	{ role: "assistant", content: [{ type: "text", text: "done" }], stopReason: "stop", timestamp: 1000 },
];
const meta = { endedAt: Date.parse("2026-10-11T10:00:00Z"), cwd: "/p", model: "llamacpp/Mellum" };

test("runRecord with no kind writes kind mode and leaves facts out", () => {
	const rec = runRecord("fix the cart", span, meta);
	assert.equal(rec.kind, "mode");
	assert.equal(rec.schema, 2);
	assert.equal(rec.activation, "unknown");
	assert.equal("facts" in rec, false);
});

test("runRecord for the Worker writes kind worker, activation worker and facts null", () => {
	const rec = runRecord("fix the cart", span, { ...meta, kind: "worker", activation: "worker", facts: null });
	assert.equal(rec.kind, "worker");
	assert.equal(rec.activation, "worker");
	assert.equal(rec.facts, null);
	assert.equal(rec.version, PACKAGE_VERSION);
});

test("promptVersionOf finds the marker at the start of any line, after a preamble", () => {
	assert.equal(promptVersionOf("<!-- mellum-worker prompt v7 -->\nx"), "v7");
	assert.equal(promptVersionOf("You are a child subagent.\nThe parent owns it.\n<!-- mellum-worker prompt v5 -->\nYou edit"), "v5");
	assert.equal(promptVersionOf("first <!-- mellum-worker prompt v5 --> inline is not a marker"), "unknown");
	assert.equal(promptVersionOf("a\n<!-- mellum-worker prompt v2 -->\n<!-- mellum-worker prompt v9 -->"), "v2");
});


test("spanStats counts tool calls by name, tool errors from any tool, and the first write's time", () => {
	const call = (id, name, args = {}) => ({ type: "toolCall", id, name, arguments: args });
	const result = (id, isError = false) => ({ role: "toolResult", toolCallId: id, isError, content: [{ type: "text", text: isError ? "boom" : "ok" }] });
	const s = spanStats([
		{ role: "user", content: [{ type: "text", text: "task" }] },
		{ role: "assistant", content: [call("a", "read", { path: "x" }), call("b", "bash", { command: "ls nope" })], timestamp: 10_000 },
		result("a", true),
		result("b", true),
		{ role: "assistant", content: [call("c", "read", { path: "y" })], timestamp: 20_000 },
		result("c"),
		{ role: "assistant", content: [call("d", "write", { path: "y", content: "" })], timestamp: 41_000 },
		result("d"),
		{ role: "assistant", content: [call("e", "edit", { path: "y" })], timestamp: 50_000 },
		result("e"),
		{ role: "assistant", content: [{ type: "text", text: "done" }], stopReason: "stop", timestamp: 60_000 },
	]);
	assert.deepEqual(s.toolCalls, { read: 2, bash: 1, write: 1, edit: 1 });
	assert.equal(s.toolErrors, 2);
	assert.equal(s.firstWriteSeconds, 31);
});

test("spanStats with no write, or no timestamps, leaves firstWriteSeconds out; runRecord carries the three fields", () => {
	const noWrite = spanStats([{ role: "assistant", content: [{ type: "toolCall", id: "a", name: "read", arguments: {} }], timestamp: 1 }]);
	assert.equal(noWrite.firstWriteSeconds, undefined);
	assert.deepEqual(noWrite.toolCalls, { read: 1 });
	assert.equal(noWrite.toolErrors, 0);
	const noTime = spanStats([{ role: "assistant", content: [{ type: "toolCall", id: "a", name: "write", arguments: { path: "p" } }] }]);
	assert.equal(noTime.firstWriteSeconds, undefined);
	const rec = runRecord("fix the cart", span, meta);
	assert.deepEqual(rec.toolCalls, {});
	assert.equal(rec.toolErrors, 0);
	assert.equal("firstWriteSeconds" in rec, false);
	const withWrite = runRecord("t", [
		{ role: "assistant", content: [{ type: "toolCall", id: "w", name: "write", arguments: { path: "p" } }], timestamp: 5_000 },
	], meta);
	assert.equal(withWrite.firstWriteSeconds, 0);
	assert.deepEqual(withWrite.toolCalls, { write: 1 });
});

test("firstWriteSeconds is absent when the writing turn has no timestamp, and the clock starts at the first timed turn", () => {
	const write = { type: "toolCall", id: "w", name: "write", arguments: { path: "p" } };
	assert.equal(spanStats([
		{ role: "assistant", content: [{ type: "toolCall", id: "r", name: "read", arguments: {} }], timestamp: 1_000 },
		{ role: "assistant", content: [write] },
		{ role: "assistant", content: [{ ...write, id: "w2" }], timestamp: 9_000 },
	]).firstWriteSeconds, undefined);
	assert.equal(spanStats([
		{ role: "assistant", content: [{ type: "toolCall", id: "r", name: "read", arguments: {} }] },
		{ role: "assistant", content: [{ type: "toolCall", id: "r2", name: "read", arguments: {} }], timestamp: 2_000 },
		{ role: "assistant", content: [write], timestamp: 6_000 },
	]).firstWriteSeconds, 4);
});
