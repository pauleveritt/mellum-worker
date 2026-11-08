import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import test from "node:test";
import layoutUnit from "../remedies/prompt/name-the-layout.ts";
import worker from "../extensions/mellum-worker.ts";
import host from "../extensions/mellum-remedies.ts";

process.env.HOME = mkdtempSync(`${tmpdir()}/task-prompt-home-`);
process.env.MELLUM_MODE_RUNS = "0";
const text = (m) => typeof m.content === "string" ? m.content : (m.content ?? []).map((b) => b.text ?? "").join("");

// Models the documented Pi hook boundaries; the real worker, unit and remedy
// controller run unchanged. User/custom messages are converted just as Pi does.
function rig() {
	const handlers = {}, commands = {}, events = new EventEmitter();
	const pending = [], transcript = [], sent = [];
	let stamp = 0;
	const ctx = {
		model: { provider: "llamacpp", id: "Mellum2.1-12B-A2.5B-Thinking" },
		modelRegistry: { find: () => ({ provider: "llamacpp", id: "Mellum2.1-12B-A2.5B-Thinking" }) },
		ui: { notify() {}, setStatus() {} },
	};
	const pi = {
		events,
		on(name, fn) { (handlers[name] ??= []).push(fn); },
		registerCommand(name, def) { commands[name] = def; },
		getActiveTools: () => ["read", "bash"],
		setActiveTools() {}, setModel: async () => true,
		sendMessage(message, options) { sent.push({ message, options }); pending.push({ role: "custom", ...message, timestamp: ++stamp }); },
	};
	async function fire(name, event) {
		let result;
		for (const fn of handlers[name] ?? []) {
			const out = await fn(event, ctx);
			if (out !== undefined) {
				result = name === "before_agent_start" && out.message
					? { messages: [...(result?.messages ?? []), out.message] } : out;
				if (name === "context") event = { ...event, ...out };
				if (name === "before_provider_request") event = { payload: out };
			}
		}
		return result;
	}
	return {
		pi, ctx, transcript, sent, fire,
		command: (name, args) => commands[name].handler(args, ctx),
		async start(prompt) {
			const out = await fire("before_agent_start", { messageType: "user", prompt, systemPrompt: "Pi system" });
			transcript.push({ role: "user", content: [{ type: "text", text: prompt }], timestamp: ++stamp }, ...pending.splice(0));
			for (const message of out?.messages ?? []) transcript.push({ role: "custom", ...message, timestamp: ++stamp });
			await fire("agent_start", {});
		},
		async payload() {
			transcript.push(...pending.splice(0));
			const messages = (await fire("context", { messages: transcript.slice() }))?.messages ?? transcript.slice();
			const payload = { model: "m", messages: [{ role: "system", content: "Pi system" }, ...messages.map((m) => m.role === "custom" ? { role: "user", content: m.content } : m)], tools: [{ name: "read" }] };
			return (await fire("before_provider_request", { payload })) ?? payload;
		},
	};
}

for (const { install: layout, name: NAME } of [
 { install: layoutUnit, name: "prompt/name-the-layout" },
]) {
const injected = (messages) => messages.filter((m) => text(m).startsWith(`[Injected remedy: ${NAME}]\n`));
test(`${NAME}: layout is one visible injected message retained across tool requests, without rewriting the task`, async () => {
	const r = rig(); layout(r.pi);
	await r.start("Build the requested page.");
	const shown = injected(r.transcript);
	assert.equal(shown.length, 1);
	assert.equal(shown[0].customType, "Injected");
	assert.equal(shown[0].display, true);
	assert.deepEqual(r.transcript[0].content, [{ type: "text", text: "Build the requested page." }]);
	const first = await r.payload();
	r.transcript.push({ role: "assistant", content: [{ type: "text", text: "Working" }] }, { role: "toolResult", toolCallId: "read-1", content: [{ type: "text", text: "spec" }] });
	const second = await r.payload();
	assert.equal(injected(first.messages).length, 1);
	assert.equal(injected(second.messages).length, 1);
	assert.deepEqual(injected(first.messages), injected(second.messages));
	assert.deepEqual(first.messages[0], { role: "system", content: "Pi system" });
	assert.deepEqual(first.tools, [{ name: "read" }]);
});

test(`${NAME}: a new Vanilla task excludes the previous injection and gets one new transcript entry`, async () => {
	const r = rig(); layout(r.pi);
	await r.start("First task");
	await r.fire("agent_settled", {});
	await r.start("Second task");
	assert.equal(injected(r.transcript).length, 2);
	assert.equal(injected((await r.payload()).messages).length, 1);
});

test(`${NAME}: compaction retains one task instruction without appending another transcript entry`, async () => {
	const r = rig(); layout(r.pi);
	await r.start("Task");
	assert.equal(injected(r.transcript).length, 1);
	await r.payload();
	r.transcript.splice(0, r.transcript.length, { role: "user", content: "Compaction summary", timestamp: 100 });
	await r.fire("session_compact", {});
	assert.equal(injected((await r.payload()).messages).length, 1);
	assert.equal(injected((await r.payload()).messages).length, 1);
	assert.equal(injected(r.transcript).length, 0);
});

test(`${NAME}: worker span retains its brief and one injection across user turns, with no parent leakage`, async () => {
	const r = rig(); worker(r.pi, { fetch: async () => { throw Error("No network"); } }); layout(r.pi);
	await r.start("Parent task");
	assert.equal(injected((await r.payload()).messages).length, 0);
	await r.command("mellum", "on");
	await r.start("Implement the feature");
	const first = await r.payload();
	assert.ok(first.messages.some((m) => text(m) === "Implement the feature"), "on-marker must not hide the brief behind the injected message");
	assert.equal(injected(first.messages).length, 1);
	await r.fire("agent_settled", {});
	await r.start("Continue the same worker task");
	assert.equal(injected(r.transcript).length, 1, "one entry for the entire worker span");
	assert.equal(injected((await r.payload()).messages).length, 1);
	await r.command("mellum", "off");
	await r.start("Parent follow-up");
	assert.equal(injected((await r.payload()).messages).length, 0);
	await r.command("mellum", "on");
	await r.start("New worker task");
	assert.equal(injected(r.transcript).length, 2);
	assert.equal(injected((await r.payload()).messages).length, 1);
});

test(`${NAME}: live enable injects in the next request and disable removes it from outgoing context`, async () => {
	const r = rig(); await host(r.pi);
	await r.start("Task started with no remedies");
	assert.equal(injected((await r.payload()).messages).length, 0);
	await r.command("remedy", `on ${NAME}`);
	assert.equal(injected((await r.payload()).messages).length, 1);
	assert.equal(injected((await r.payload()).messages).length, 1);
	await r.command("remedy", `off ${NAME}`);
	assert.equal(injected((await r.payload()).messages).length, 0);
	await r.command("remedy", `on ${NAME}`);
	await r.start("Next task with remedy enabled");
	assert.equal(injected(r.transcript).length, 2);
	assert.equal(injected((await r.payload()).messages).length, 1);
	await r.command("remedy", `off ${NAME}`);
	assert.equal(injected((await r.payload()).messages).length, 0, "persisted custom messages must also be filtered when disabled");
});

test(`${NAME}: session changes discard the previous task's instruction`, async () => {
	const r = rig(); layout(r.pi);
	await r.start("Task in old session");
	await r.fire("session_start", {});
	r.transcript.length = 0;
	assert.equal(injected((await r.payload()).messages).length, 0);
	await r.start("Task in new session");
	assert.equal(injected(r.transcript).length, 1);
	assert.equal(injected((await r.payload()).messages).length, 1);
});

test(`${NAME}: enabling during a task publishes one visible instruction without starting another turn`, async () => {
	const r = rig(); await host(r.pi);
	await r.start("Already working");
	await r.command("remedy", `on ${NAME}`);
	assert.equal(injected((await r.payload()).messages).length, 1);
	// Pi flushes triggerTurn:false custom messages after the current turn.
	await r.payload();
	assert.equal(injected(r.transcript).length, 1, "late injection must also be visible in the transcript");
	assert.equal(injected(r.transcript)[0].display, true);
	await r.payload();
	assert.equal(injected(r.transcript).length, 1, "one publication, even across multiple requests");
	assert.deepEqual(r.sent.map((s) => s.options), [{ triggerTurn: false }]);
});

}

test("two task prompts keep independent visible messages", async (t) => {
 const { mkdtempSync: mk, writeFileSync } = await import("node:fs");
 const dir = mk(`${tmpdir()}/mediated-src-`);
 writeFileSync(`${dir}/test_01_x.py`, "def test_x():\n    pass\n");
 const saved = process.env.MELLUM_MEDIATED_TEST;
 t.after(() => { if (saved === undefined) delete process.env.MELLUM_MEDIATED_TEST; else process.env.MELLUM_MEDIATED_TEST = saved; });
 process.env.MELLUM_MEDIATED_TEST = `${dir}/test_01_x.py`;
 const { default: mediated } = await import("../remedies/check/mediated-test.ts");
 const r = rig();
 layoutUnit(r.pi);
 mediated(r.pi);
 await r.start("Implement the task");
 const messages = r.transcript.filter((m) => m.customType === "Injected");
 assert.deepEqual(messages.map((m) => m.details.remedy).sort(), ["check/mediated-test", "prompt/name-the-layout"]);
 assert.equal((await r.payload()).messages.filter((m) => text(m).startsWith("[Injected remedy:")).length, 2);
 assert.equal(text(r.transcript[0]), "Implement the task");
});
