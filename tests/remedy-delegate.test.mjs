import { test } from "node:test";
import assert from "node:assert/strict";

/** A fake Pi that records what a unit installs and lets a test drive the hooks. */
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

const textOf = (m) => (typeof m.content === "string" ? m.content : (m.content ?? []).map((p) => p.text ?? "").join(""));

test("delegate/collapse-handoffs installs one context hook and nothing else", async () => {
	const pi = fakePi();
	(await import("../remedies/delegate/collapse-handoffs.ts")).default(pi);
	assert.deepEqual(pi.events(), ["context"]);
	assert.equal(pi.handlers.context.length, 1);
	assert.equal(pi.tools.length, 0);
});

test("delegate/collapse-handoffs carries the metadata the remedies list needs", async () => {
	const { meta } = await import("../remedies/delegate/collapse-handoffs.ts");
	for (const key of ["pathology", "does", "evidence"]) assert.ok(meta[key].length > 0, `meta.${key} empty`);
});

test("delegate/collapse-handoffs leaves a context with no Mellum span alone", async () => {
	const pi = fakePi();
	(await import("../remedies/delegate/collapse-handoffs.ts")).default(pi);
	const plain = [{ role: "user", content: [{ type: "text", text: "hello" }] }, { role: "assistant", content: [{ type: "text", text: "hi" }] }];
	assert.equal(pi.fire("context", { messages: plain }), undefined);
});

test("delegate/collapse-handoffs replaces a finished [on…off] span with one handoff block", async () => {
	const pi = fakePi();
	(await import("../remedies/delegate/collapse-handoffs.ts")).default(pi);
	const messages = [
		{ role: "user", content: [{ type: "text", text: "add a cart route" }] },
		{ role: "user", content: [{ type: "text", text: "[mellum-worker on]" }] },
		{ role: "assistant", content: [{ type: "text", text: "done" }] },
		{ role: "user", content: [{ type: "text", text: "[mellum-worker off]" }] },
	];
	const out = pi.fire("context", { messages });
	assert.ok(out && Array.isArray(out.messages), "the hook returns rewritten messages");
	const joined = out.messages.map(textOf).join("\n");
	assert.ok(joined.includes("[mellum-worker handoff]"), "a handoff block replaces the span");
	assert.ok(joined.includes("add a cart route"), "the task is named in the handoff");
	assert.ok(!out.messages.some((m) => textOf(m).includes("[mellum-worker on]")), "the markers are gone");
});

test("delegate/collapse-handoffs leaves an open span (no off-marker) untouched", async () => {
	const pi = fakePi();
	(await import("../remedies/delegate/collapse-handoffs.ts")).default(pi);
	const messages = [
		{ role: "user", content: [{ type: "text", text: "[mellum-worker on]" }] },
		{ role: "assistant", content: [{ type: "text", text: "working" }] },
	];
	const out = pi.fire("context", { messages });
	// open span: collapseHandoffs passes the tail through unchanged (same content, no handoff block)
	const joined = (out?.messages ?? messages).map(textOf).join("\n");
	assert.ok(!joined.includes("[mellum-worker handoff]"), "an open span is not collapsed");
});
