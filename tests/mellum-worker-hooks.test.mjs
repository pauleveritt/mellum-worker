import assert from "node:assert/strict";
import test from "node:test";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import install from "../extensions/mellum-worker.ts";
import { checkSetup, formatFindings, loadExpected, providerEntry } from "../extensions/mellum-check.ts";

// No test reads or writes the real ~/.pi/agent: activation reads $HOME/.pi/agent/models.json
// for the server URL, and the run record defaults to $HOME/.pi/agent.
process.env.HOME = mkdtempSync(`${tmpdir()}/mellum-home-`);
// No test touches the network: every install gets a fetch, by default one with no server.
const noServer = async () => {
	throw new TypeError("fetch failed: no server in tests");
};

const MODEL = { provider: "omlx", id: "Mellum2.1-12B-A2.5B-Thinking-6bit" };

function fakePi({ registryHasModel = true } = {}) {
	const handlers = {};
	let commands = {};
	const pi = {
		on: (name, fn) => { handlers[name] = fn; },
		registerCommand: (name, def) => { commands[name] = def; },
		getActiveTools: () => ["read", "subagent"],
		setActiveTools: () => {},
		setModel: async () => true,
		sendMessage: () => {},
		sendUserMessage: () => {},
	};
	const ctx = {
		model: { provider: "anthropic", id: "parent" },
		modelRegistry: { find: (p, id) => (registryHasModel && p === MODEL.provider && id === MODEL.id ? MODEL : undefined) },
		ui: { notify: () => {} },
	};
	install(pi, { fetch: noServer });
	return { handlers, ctx, mellum: (args) => commands.mellum.handler(args, ctx) };
}

const read = { toolName: "read", input: { path: "x" } };
const emptyTurn = { message: { role: "assistant", content: [{ type: "thinking", thinking: "." }] } };

test("falls back to the session's model when the oMLX one is absent", async () => {
	const { ctx, mellum } = fakePi({ registryHasModel: false });
	ctx.model = { provider: "llamacpp", id: "Mellum2.1-12B-A2.5B-Thinking" };
	const notes = [];
	ctx.ui = { notify: (m) => notes.push(m) };
	await mellum("on");
	assert.ok(notes.some((m) => m.startsWith("mellum-worker on: llamacpp/Mellum2.1-12B-A2.5B-Thinking")), JSON.stringify(notes));
	assert.ok(!notes.some((m) => m.includes("not found")), JSON.stringify(notes));
});

test("guard hooks are inert while mode is off", () => {
	const { handlers } = fakePi();
	for (let i = 0; i < 8; i++) assert.equal(handlers.tool_call(read), undefined);
	handlers.turn_end(emptyTurn);
	assert.equal(handlers.agent_before_settle(), undefined);
});

test("guard hooks are live while mode is on", async () => {
	const { handlers, mellum } = fakePi();
	await mellum("on");
	for (let i = 0; i < 5; i++) assert.equal(handlers.tool_call(read), undefined);
	assert.ok(handlers.tool_call(read)?.block);
	handlers.turn_end(emptyTurn);
	assert.ok(handlers.agent_before_settle()?.continue);
});

test("guard state is fresh for each span", async () => {
	const { handlers, mellum } = fakePi();
	await mellum("on");
	for (let i = 0; i < 5; i++) handlers.tool_call(read);
	await mellum("off");
	await mellum("on");
	assert.equal(handlers.tool_call(read), undefined, "the new span does not remember the old reads");
});

test("activating with the model missing from the registry leaves mode and guards off", async () => {
	const { handlers, mellum } = fakePi({ registryHasModel: false });
	await mellum("on");
	for (let i = 0; i < 8; i++) assert.equal(handlers.tool_call(read), undefined);
	assert.equal(handlers.before_provider_request({ payload: { messages: [] } }), undefined);
});

test("context hook is dormant when no mellum span exists, and collapses when one does", () => {
	const { handlers } = fakePi();
	const plain = [{ role: "user", content: [{ type: "text", text: "hi" }] }];
	assert.equal(handlers.context({ messages: plain }), undefined);
	const t = (text) => ({ role: "user", content: [{ type: "text", text }] });
	const messages = [t("hi"), t("[mellum-worker on]"), t("task"), { role: "assistant", content: [{ type: "text", text: "done" }] }, t("[mellum-worker off]"), t("next")];
	const out = handlers.context({ messages });
	assert.ok(out && Array.isArray(out.messages));
	assert.ok(out.messages.length < messages.length);
});

test("/mellum off notifies a one-line summary of the span", async () => {
	const notes = [];
	const handlers = {};
	let commands = {};
	const pi = {
		on: (name, fn) => { handlers[name] = fn; },
		registerCommand: (name, def) => { commands[name] = def; },
		getActiveTools: () => ["read"],
		setActiveTools: () => {},
		setModel: async () => true,
		sendMessage: () => {},
		sendUserMessage: () => {},
	};
	const ctx = {
		model: { provider: "anthropic", id: "parent" },
		modelRegistry: { find: () => MODEL },
		ui: { notify: (msg, level) => notes.push([msg, level]) },
	};
	install(pi, { fetch: noServer });
	await commands.mellum.handler("on", ctx);
	handlers.before_provider_request({ payload: { messages: [] } }, ctx);
	handlers.before_provider_request({ payload: { messages: [] } }, ctx);
	handlers.tool_call({ toolName: "bash", input: { command: "node --test" } });
	handlers.turn_end({ message: { role: "assistant", usage: { output: 300 }, content: [{ type: "toolCall", id: "1", name: "bash", arguments: { command: "node --test" } }] } });
	handlers.turn_end({ message: { role: "assistant", usage: { output: 100 }, content: [{ type: "text", text: "done" }] } });
	await commands.mellum.handler("off", ctx);
	const line = notes.map(([m]) => m).find((m) => m.startsWith("mellum-worker off:"));
	assert.ok(line, `no summary notify; got ${JSON.stringify(notes)}`);
	assert.match(line, /2 requests, 1 tool call, 400 output tokens, \d+ s/);
});

test("/mellum off appends one run record line to the file named by MELLUM_MODE_RUNS, and 0 disables it", async () => {
	const { mkdtempSync, readFileSync, existsSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const { join } = await import("node:path");
	const dir = mkdtempSync(join(tmpdir(), "mellum-runs-"));
	const file = join(dir, "nested", "runs.jsonl");
	const makePi = () => {
		const handlers = {};
		let commands = {};
		const pi = {
			on: (name, fn) => { handlers[name] = fn; },
			registerCommand: (name, def) => { commands[name] = def; },
			getActiveTools: () => ["read"], setActiveTools: () => {}, setModel: async () => true, sendMessage: () => {}, sendUserMessage: () => {},
		};
		const ctx = { model: { provider: "anthropic", id: "parent" }, modelRegistry: { find: () => MODEL }, ui: { notify: () => {} } };
		install(pi, { fetch: noServer });
		return { handlers, ctx, mellum: (a) => commands.mellum.handler(a, ctx) };
	};
	const span = [
		{ role: "user", content: [{ type: "text", text: "fix the cart" }] },
		{ role: "user", content: [{ type: "text", text: "[mellum-worker on]" }] },
		{ role: "assistant", timestamp: Date.now(), usage: { output: 12 }, content: [{ type: "toolCall", id: "1", name: "bash", arguments: { command: "node --test" } }] },
		{ role: "toolResult", toolCallId: "1", toolName: "bash", content: [{ type: "text", text: "pass" }] },
		{ role: "assistant", timestamp: Date.now(), usage: { output: 5 }, content: [{ type: "text", text: "ok" }] },
	];
	process.env.MELLUM_MODE_RUNS = file;
	try {
		const a = makePi();
		await a.mellum("on");
		a.handlers.context({ messages: span });
		await a.mellum("off");
		const lines = readFileSync(file, "utf8").trim().split("\n");
		assert.equal(lines.length, 1);
		const rec = JSON.parse(lines[0]);
		assert.equal(rec.task, "fix the cart");
		assert.equal(rec.requests, 2);
		assert.deepEqual(rec.commands, [{ command: "node --test", failed: false, mutates: false }]);
		assert.equal(rec.model, `${MODEL.provider}/${MODEL.id}`);
		process.env.MELLUM_MODE_RUNS = "0";
		const b = makePi();
		await b.mellum("on");
		b.handlers.context({ messages: span });
		await b.mellum("off");
		assert.equal(readFileSync(file, "utf8").trim().split("\n").length, 1, "disabled: nothing appended");
	} finally {
		delete process.env.MELLUM_MODE_RUNS;
	}
});

function recordingPi({ mode, hasUI, fetch = noServer } = {}) {
	const handlers = {};
	let commands = {};
	const calls = { setModel: [], sendMessage: [], notify: [] };
	const pi = {
		on: (name, fn) => { handlers[name] = fn; },
		registerCommand: (name, def) => { commands[name] = def; },
		getActiveTools: () => ["read"], setActiveTools: () => {},
		setModel: async (m) => { calls.setModel.push(m); return true; },
		sendMessage: (m, o) => { calls.sendMessage.push(m); if (m.customType === "mellum-last") (calls.lastOptions ??= []).push(o); }, sendUserMessage: () => {},
	};
	const ctx = { model: { provider: "anthropic", id: "parent" }, modelRegistry: { find: () => MODEL }, ui: { notify: (m, l) => calls.notify.push([m, l]) } };
	if (mode !== undefined) ctx.mode = mode;
	if (hasUI !== undefined) ctx.hasUI = hasUI;
	install(pi, { fetch });
	return { handlers, ctx, calls, mellum: (a) => commands.mellum.handler(a, ctx) };
}

test("run record reconstructs the span from the last context snapshot plus the turns after it", async () => {
	const { mkdtempSync, readFileSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const { join } = await import("node:path");
	const file = join(mkdtempSync(join(tmpdir(), "mellum-runs-")), "runs.jsonl");
	process.env.MELLUM_MODE_RUNS = file;
	try {
		const { handlers, mellum } = recordingPi();
		await mellum("on");
		// context fires before each request; the final assistant turn arrives only via turn_end
		const before = [
			{ role: "user", content: [{ type: "text", text: "fix the cart" }] },
			{ role: "custom", customType: "mellum-worker", content: "[mellum-worker on]" },
			{ role: "assistant", timestamp: 1000, usage: { output: 10 }, content: [{ type: "toolCall", id: "1", name: "bash", arguments: { command: "node --test" } }] },
			{ role: "toolResult", toolCallId: "1", toolName: "bash", isError: true, content: [{ type: "text", text: "fail 1" }] },
		];
		handlers.context({ messages: before });
		handlers.turn_end({ message: { role: "assistant", timestamp: 2000, usage: { output: 7 }, content: [{ type: "toolCall", id: "2", name: "edit", arguments: { path: "cart.js" } }] } });
		handlers.context({ messages: [...before, { role: "assistant", timestamp: 2000, usage: { output: 7 }, content: [{ type: "toolCall", id: "2", name: "edit", arguments: { path: "cart.js" } }] }, { role: "toolResult", toolCallId: "2", toolName: "edit", content: [{ type: "text", text: "ok" }] }] });
		handlers.turn_end({ message: { role: "assistant", timestamp: 3000, usage: { output: 5 }, content: [{ type: "text", text: "done" }] } });
		await mellum("off");
		const rec = JSON.parse(readFileSync(file, "utf8").trim());
		assert.equal(rec.task, "fix the cart");
		assert.equal(rec.requests, 3, "the turn after the last context snapshot is counted once");
		assert.equal(rec.usage.output, 22);
		assert.deepEqual(rec.files, ["cart.js"]);
		assert.equal(rec.lastCommand, "failed");
		assert.equal(rec.finalReply, "done");
		assert.equal(rec.wallSeconds, 2);
	} finally {
		delete process.env.MELLUM_MODE_RUNS;
	}
});

test("a failing record write warns but never disturbs deactivation", async () => {
	const { mkdtempSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	process.env.MELLUM_MODE_RUNS = mkdtempSync(join_(tmpdir(), "mellum-runs-")); // a directory, so appendFile fails
	try {
		const { handlers, ctx, calls, mellum } = recordingPi();
		await mellum("on");
		handlers.context({ messages: [{ role: "user", content: [{ type: "text", text: "t" }] }, { role: "user", content: [{ type: "text", text: "[mellum-worker on]" }] }, { role: "assistant", content: [{ type: "text", text: "x" }] }] });
		await mellum("off");
		assert.deepEqual(calls.setModel.at(-1), ctx.model, "previous model restored");
		assert.ok(calls.sendMessage.some((m) => m.content === "[mellum-worker off]"), "off marker sent");
		assert.ok(calls.notify.some(([m, l]) => m.includes("could not write the run record") && l === "warning"));
		assert.ok(calls.notify.some(([m]) => m.startsWith("mellum-worker off:")), "off notification still shown");
		for (let i = 0; i < 8; i++) assert.equal(handlers.tool_call({ toolName: "read", input: { path: "x" } }), undefined, "mode is off afterwards");
	} finally {
		delete process.env.MELLUM_MODE_RUNS;
	}
});
function join_(...p) { return p.join("/"); }

test("no context seen while on means nothing is written", async () => {
	const { mkdtempSync, existsSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const file = join_(mkdtempSync(join_(tmpdir(), "mellum-runs-")), "runs.jsonl");
	process.env.MELLUM_MODE_RUNS = file;
	try {
		const { mellum } = recordingPi();
		await mellum("on");
		await mellum("off");
		assert.equal(existsSync(file), false);
	} finally {
		delete process.env.MELLUM_MODE_RUNS;
	}
});

const snapshot = [
	{ role: "user", content: [{ type: "text", text: "fix the cart" }] },
	{ role: "user", content: [{ type: "text", text: "[mellum-worker on]" }] },
	{ role: "assistant", timestamp: 1000, usage: { output: 5 }, content: [{ type: "text", text: "ok" }] },
];

// Runs `body(file)` with MELLUM_MODE_RUNS on a fresh temp file, restoring every env var afterwards.
async function withRunsFile(body, { prompt, headless } = {}) {
	const { mkdtempSync, readFileSync, writeFileSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const dir = mkdtempSync(join_(tmpdir(), "mellum-runs-"));
	const file = join_(dir, "runs.jsonl");
	const saved = { RUNS: process.env.MELLUM_MODE_RUNS, PROMPT: process.env.MELLUM_MODE_PROMPT, MODE: process.env.MELLUM_MODE };
	process.env.MELLUM_MODE_RUNS = file;
	if (prompt !== undefined) {
		const pf = join_(dir, "prompt.md");
		writeFileSync(pf, prompt);
		process.env.MELLUM_MODE_PROMPT = pf;
	}
	if (headless) process.env.MELLUM_MODE = "1";
	try {
		await body();
		return JSON.parse(readFileSync(file, "utf8").trim());
	} finally {
		for (const [k, v] of Object.entries({ MELLUM_MODE_RUNS: saved.RUNS, MELLUM_MODE_PROMPT: saved.PROMPT, MELLUM_MODE: saved.MODE })) {
			if (v === undefined) delete process.env[k];
			else process.env[k] = v;
		}
	}
}

test("run record carries host, activation, prompt version, nudges and guard blocks", async () => {
	const { readFileSync } = await import("node:fs");
	const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
	const rec = await withRunsFile(async () => {
		const { handlers, mellum } = recordingPi({ mode: "tui" });
		await mellum("on");
		handlers.context({ messages: snapshot });
		for (let i = 0; i < 5; i++) assert.equal(handlers.tool_call(read), undefined);
		assert.ok(handlers.tool_call(read)?.block, "the sixth identical read is blocked");
		handlers.turn_end(emptyTurn);
		assert.ok(handlers.agent_before_settle()?.continue, "the empty turn is nudged");
		await mellum("off");
	});
	assert.equal(rec.nudges, 1);
	assert.equal(rec.guardBlocks, 1);
	assert.equal(rec.activation, "on");
	assert.equal(rec.host, "tui");
	assert.equal(rec.promptVersion, "v11");
	assert.equal(rec.version, pkg.version);
});

test("a prompt without a version marker records promptVersion unknown", async () => {
	const rec = await withRunsFile(async () => {
		const { handlers, mellum } = recordingPi({ mode: "tui" });
		await mellum("on");
		handlers.context({ messages: snapshot });
		await mellum("off");
	}, { prompt: "no marker" });
	assert.equal(rec.promptVersion, "unknown");
});

test("MELLUM_MODE=1 at session_start records activation headless and the host mode", async () => {
	const rec = await withRunsFile(async () => {
		const { handlers, ctx, mellum } = recordingPi({ mode: "json" });
		await handlers.session_start({}, ctx);
		handlers.context({ messages: snapshot });
		await mellum("off");
	}, { headless: true });
	assert.equal(rec.activation, "headless");
	assert.equal(rec.host, "json");
});

test("/mellum <task> records activation one-shot", async () => {
	const rec = await withRunsFile(async () => {
		const { handlers, ctx, mellum } = recordingPi({ mode: "tui", hasUI: true });
		await mellum("fix it");
		handlers.context({ messages: snapshot });
		await handlers.agent_settled({}, ctx);
	});
	assert.equal(rec.activation, "one-shot");
});

test("a ctx without a mode records host unknown", async () => {
	const rec = await withRunsFile(async () => {
		const { handlers, mellum } = recordingPi();
		await mellum("on");
		handlers.context({ messages: snapshot });
		await mellum("off");
	});
	assert.equal(rec.host, "unknown");
});

// A fake Pi whose sendUserMessage runs the task a tick later, as Pi's print mode does:
// agent_start, a context snapshot, one assistant turn, then (optionally) agent_settled,
// then the idle wait resolves. `waitForIdle` is a spy returning that idle promise.
function headlessPi({ hasUI = false, withWait = true, startsRun = true, settledFirst = false, startTimeoutMs } = {}) {
	const handlers = {};
	let commands = {};
	const calls = { setModel: [], sendMessage: [], notify: [], waitForIdle: 0 };
	let resolveIdle;
	const idle = new Promise((r) => { resolveIdle = r; });
	if (!startsRun) resolveIdle(); // no run: Pi is idle, so the wait returns at once
	const ctx = { mode: "print", hasUI, model: { provider: "anthropic", id: "parent" }, modelRegistry: { find: () => MODEL }, ui: { notify: (m, l) => calls.notify.push([m, l]) } };
	if (withWait) ctx.waitForIdle = () => { calls.waitForIdle += 1; return idle; };
	const pi = {
		on: (name, fn) => { handlers[name] = fn; },
		registerCommand: (name, def) => { commands[name] = def; },
		getActiveTools: () => ["read"], setActiveTools: () => {},
		setModel: async (m) => { calls.setModel.push(m); return true; },
		sendMessage: (m) => calls.sendMessage.push(m),
		sendUserMessage: (text) => {
			if (!startsRun) return;
			setImmediate(async () => {
				handlers.agent_start?.({}, ctx);
				const reply = { role: "assistant", timestamp: 1000, usage: { output: 5 }, content: [{ type: "text", text: "done" }] };
				handlers.context({ messages: [{ role: "user", content: [{ type: "text", text }] }, { role: "custom", customType: "mellum-worker", content: "[mellum-worker on]" }, reply] });
				handlers.turn_end({ message: reply });
				if (settledFirst) await handlers.agent_settled({}, ctx);
				resolveIdle();
			});
		},
	};
	if (startTimeoutMs === undefined) install(pi, { fetch: noServer });
	else install(pi, { startTimeoutMs, fetch: noServer });
	return { handlers, ctx, calls, mellum: (a) => commands.mellum.handler(a, ctx) };
}

// Runs `body()` with MELLUM_MODE_RUNS on a fresh temp file; returns the file's lines (none if absent).
async function recordLines(body) {
	const { mkdtempSync, readFileSync, existsSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const file = join_(mkdtempSync(join_(tmpdir(), "mellum-runs-")), "runs.jsonl");
	const saved = process.env.MELLUM_MODE_RUNS;
	process.env.MELLUM_MODE_RUNS = file;
	try {
		await body();
		return existsSync(file) ? readFileSync(file, "utf8").trim().split("\n") : [];
	} finally {
		if (saved === undefined) delete process.env.MELLUM_MODE_RUNS;
		else process.env.MELLUM_MODE_RUNS = saved;
	}
}

const offMarkers = (calls) => calls.sendMessage.filter((m) => m.content === "[mellum-worker off]").length;
const modeIsOff = (handlers) => { for (let i = 0; i < 8; i++) assert.equal(handlers.tool_call(read), undefined, "guard hooks inert: mode is off"); };

test("headless one shot: the handler waits for the run, then restores the model and writes the record", async () => {
	let h;
	const lines = await recordLines(async () => {
		h = headlessPi();
		await h.mellum("fix it");
	});
	assert.equal(h.calls.waitForIdle, 1, "waitForIdle called once");
	assert.deepEqual(h.calls.setModel.at(-1), h.ctx.model, "the parent model is restored");
	assert.equal(offMarkers(h.calls), 1, "one off-marker");
	assert.equal(lines.length, 1, "one record line");
	const rec = JSON.parse(lines[0]);
	assert.equal(rec.activation, "one-shot");
	assert.equal(rec.host, "print");
	assert.equal(rec.task, "fix it");
	modeIsOff(h.handlers);
});

test("headless one shot where agent_settled fires before idle: still one deactivation", async () => {
	let h;
	const lines = await recordLines(async () => {
		h = headlessPi({ settledFirst: true });
		await h.mellum("fix it");
	});
	const restores = h.calls.setModel.filter((m) => m === h.ctx.model).length;
	assert.equal(restores, 1, "one restore setModel");
	assert.equal(offMarkers(h.calls), 1, "one off-marker");
	assert.equal(lines.length, 1, "one record line");
	assert.equal(h.calls.notify.filter(([m]) => m.startsWith("mellum-worker off:")).length, 1, "one off notification");
	modeIsOff(h.handlers);
});

test("one shot with a UI: the handler returns at once and agent_settled turns the mode off", async () => {
	const h = headlessPi({ hasUI: true, startsRun: false, startTimeoutMs: 20 });
	await h.mellum("fix it");
	assert.equal(h.calls.waitForIdle, 0, "waitForIdle never called");
	for (let i = 0; i < 5; i++) assert.equal(h.handlers.tool_call(read), undefined);
	assert.ok(h.handlers.tool_call(read)?.block, "mode still on after return: the sixth identical read is blocked");
	await h.handlers.agent_settled({}, h.ctx);
	modeIsOff(h.handlers);
	assert.equal(offMarkers(h.calls), 1);
});

test("headless ctx without waitForIdle: the handler returns with the mode on and does not throw", async () => {
	const h = headlessPi({ withWait: false, startsRun: false, startTimeoutMs: 20 });
	await h.mellum("fix it");
	for (let i = 0; i < 5; i++) assert.equal(h.handlers.tool_call(read), undefined);
	assert.ok(h.handlers.tool_call(read)?.block, "mode still on after return");
	assert.equal(offMarkers(h.calls), 0);
});

test("headless one shot whose run never starts gives up after the start timeout, warns on stderr and turns the mode off", async () => {
	let h;
	let elapsed;
	let lines;
	const stderr = await captureStderr(async () => {
		lines = await recordLines(async () => {
			h = headlessPi({ startsRun: false, startTimeoutMs: 20 });
			const t0 = Date.now();
			await h.mellum("fix it");
			elapsed = Date.now() - t0;
		});
	});
	assert.ok(elapsed < 1000, `returned within a second (took ${elapsed} ms)`);
	assert.equal(stderr.length, 1, `one stderr line (got ${JSON.stringify(stderr)})`);
	assert.match(stderr[0], /did not start within/);
	assert.deepEqual(h.calls.setModel.at(-1), h.ctx.model, "the parent model is restored");
	assert.equal(offMarkers(h.calls), 1);
	assert.equal(lines.length, 0, "no record line");
	modeIsOff(h.handlers);
});

// Runs `body()` with console.error captured; returns the captured lines. Always restores console.error.
async function captureStderr(body) {
	const lines = [];
	const original = console.error;
	console.error = (...args) => lines.push(args.join(" "));
	try {
		await body();
	} finally {
		console.error = original;
	}
	return lines;
}

test("without a UI, a missing Mellum model is reported on stderr and the mode stays off", async () => {
	const h = recordingPi({ mode: "print", hasUI: false });
	h.ctx.modelRegistry.find = () => undefined;
	const lines = await captureStderr(() => h.mellum("fix it"));
	assert.equal(lines.length, 1, "one stderr line");
	assert.match(lines[0], /omlx\/Mellum2\.1-12B-A2\.5B-Thinking-6bit not found/);
	modeIsOff(h.handlers);
});

test("with a UI, a missing Mellum model is a notify error and nothing goes to stderr", async () => {
	const h = recordingPi({ mode: "tui", hasUI: true });
	h.ctx.modelRegistry.find = () => undefined;
	const lines = await captureStderr(() => h.mellum("fix it"));
	assert.deepEqual(lines, [], "nothing on stderr");
	assert.ok(h.calls.notify.some(([m, l]) => m.includes("not found") && l === "error"), "notify called with level error");
	modeIsOff(h.handlers);
});

// Runs `body(dir)` with the process in a fresh project directory holding `files`, restoring cwd and env.
async function inProject(files, body, { env = {} } = {}) {
	const { mkdtempSync, writeFileSync, realpathSync } = await import("node:fs");
	const { tmpdir } = await import("node:os");
	const dir = realpathSync(mkdtempSync(join_(tmpdir(), "mellum-proj-")));
	for (const [name, content] of Object.entries(files)) writeFileSync(join_(dir, name), content);
	const cwd = process.cwd();
	const saved = Object.fromEntries(Object.keys(env).map((k) => [k, process.env[k]]));
	Object.assign(process.env, env);
	process.chdir(dir);
	try {
		return await body(dir);
	} finally {
		process.chdir(cwd);
		for (const [k, v] of Object.entries(saved)) {
			if (v === undefined) delete process.env[k];
			else process.env[k] = v;
		}
	}
}

const FACTS_MD = "# P\n\n## Mellum\n\n- Test command: make test\n- Do not: add dependencies\n";
const userMsg = (text) => ({ role: "user", content: [{ type: "text", text }] });

test("/mellum on reads the project's facts, marks the source, and forwards the block on every request", async () => {
	await inProject({ "AGENTS.md": FACTS_MD }, async () => {
		const { handlers, ctx, calls, mellum } = recordingPi({ mode: "tui" });
		await mellum("on");
		const on = calls.sendMessage.find((m) => String(m.content).includes("[mellum-worker on]"));
		assert.equal(on.content, "[mellum-worker on] facts: agents-md");
		const payload = { messages: [userMsg("[mellum-worker on] facts: agents-md"), userMsg("task one")] };
		for (let i = 0; i < 2; i++) {
			const out = handlers.before_provider_request({ payload }, ctx);
			assert.equal(out.messages[1].content[0].text, "task one\n\nProject facts:\n- Test command: make test\n- Do not: add dependencies");
		}
		assert.equal(payload.messages[1].content[0].text, "task one", "the session's message is unchanged");
	});
});

test("headless activation (MELLUM_MODE=1, no marker) forwards the facts to the task message", async () => {
	await inProject({ "AGENTS.md": FACTS_MD }, async () => {
		const { handlers, ctx, calls } = recordingPi({ mode: "json" });
		const saved = process.env.MELLUM_MODE;
		process.env.MELLUM_MODE = "1";
		try {
			await handlers.session_start({}, ctx);
		} finally {
			if (saved === undefined) delete process.env.MELLUM_MODE;
			else process.env.MELLUM_MODE = saved;
		}
		assert.equal(calls.sendMessage.length, 0, "headless sends no marker");
		const out = handlers.before_provider_request({ payload: { messages: [{ role: "system", content: "pi" }, userMsg("Implement specs/phase-1.md")] } }, ctx);
		assert.deepEqual(out.messages.map((m) => m.role), ["system", "user"]);
		assert.match(out.messages[1].content[0].text, /^Implement specs\/phase-1\.md\n\nProject facts:\n- Test command: make test\n/);
	});
});

test("the run record carries facts: source, test command, chars", async () => {
	const rec = await inProject({ "AGENTS.md": FACTS_MD }, () => withRunsFile(async () => {
		const { handlers, mellum } = recordingPi({ mode: "tui" });
		await mellum("on");
		handlers.context({ messages: snapshot });
		await mellum("off");
	}));
	assert.deepEqual(rec.facts, { source: "agents-md", testCommand: "make test", chars: "Test command: make test".length + "Do not: add dependencies".length });
});

test("the fallback is detected from a pytest pyproject and recorded", async () => {
	const rec = await inProject({ "pyproject.toml": '[dependency-groups]\ndev = ["pytest"]\n' }, () => withRunsFile(async () => {
		const { handlers, mellum } = recordingPi({ mode: "tui" });
		await mellum("on");
		handlers.context({ messages: snapshot });
		await mellum("off");
	}));
	assert.deepEqual(rec.facts, { source: "detected", testCommand: "uv run --offline python -m pytest -q", chars: "Test command: uv run --offline python -m pytest -q".length });
});

test("MELLUM_MODE_FACTS=0 records off, marks off, and forwards nothing", async () => {
	await inProject({ "AGENTS.md": FACTS_MD }, async () => {
		const rec = await withRunsFile(async () => {
			const { handlers, ctx, calls, mellum } = recordingPi({ mode: "tui" });
			await mellum("on");
			assert.equal(calls.sendMessage.find((m) => String(m.content).includes("[mellum-worker on]")).content, "[mellum-worker on] facts: off");
			const out = handlers.before_provider_request({ payload: { messages: [userMsg("[mellum-worker on]"), userMsg("t")] } }, ctx);
			assert.equal(out.messages[1].content[0].text, "t");
			handlers.context({ messages: snapshot });
			await mellum("off");
		});
		assert.deepEqual(rec.facts, { source: "off", testCommand: null, chars: 0 });
	}, { env: { MELLUM_MODE_FACTS: "0" } });
});

test("a section over the cap warns on activation and falls back", async () => {
	await inProject({ "AGENTS.md": `## Mellum\n- Do not: ${"x".repeat(700)}\n` }, async () => {
		const { calls, mellum } = recordingPi({ mode: "tui" });
		await mellum("on");
		assert.ok(calls.notify.some(([m, l]) => /600/.test(m) && l === "warning"), JSON.stringify(calls.notify));
		assert.equal(calls.sendMessage.find((m) => String(m.content).includes("[mellum-worker on]")).content, "[mellum-worker on] facts: none");
	});
});

test("without a UI the over-cap warning goes to stderr", async () => {
	await inProject({ "AGENTS.md": `## Mellum\n- Do not: ${"x".repeat(700)}\n` }, async () => {
		const { calls, mellum } = recordingPi({ mode: "print", hasUI: false });
		const errs = [];
		const orig = console.error;
		console.error = (...a) => errs.push(a.join(" "));
		try {
			await mellum("on");
		} finally {
			console.error = orig;
		}
		assert.ok(errs.some((m) => /600/.test(m)), JSON.stringify(errs));
		assert.ok(!calls.notify.some(([, l]) => l === "warning"), "no UI notification for the warning");
	});
});

test("the parent's handoff summary line names the facts source from the span's on-marker", async () => {
	const { handlers } = recordingPi();
	const out = handlers.context({ messages: [userMsg("task"), { role: "custom", customType: "mellum-worker", content: "[mellum-worker on] facts: detected" }, { role: "assistant", content: [{ type: "text", text: "done" }] }, { role: "custom", customType: "mellum-worker", content: "[mellum-worker off]" }, userMsg("next")] });
	const handoff = out.messages.find((m) => JSON.stringify(m).includes("handoff"));
	assert.match(JSON.stringify(handoff), /, facts: detected/);
});

// ---- the server settings check: on activation, in the run record, and /mellum check ----

const FIX = new URL("./fixtures/check/", import.meta.url);
const fixtureJson = (name) => JSON.parse(readFileSync(new URL(name, FIX), "utf8"));
const response = (body, status = 200) => ({ ok: status < 300, status, json: async () => body });
const DRIFT_WARNING =
	"Mellum server settings differ: max_context_window 32768 (expected 56000), turboquant_kv_enabled true (expected false). Run /mellum check.";

// A fake oMLX that answers the three GETs from the fixtures and records every call.
function fakeServer(adminModels = "admin-models-drift.json") {
	const calls = [];
	const fetch = async (url, init) => {
		const u = String(url);
		calls.push({ url: u, method: init?.method ?? "GET" });
		if (u.endsWith("/admin/api/models")) return response(fixtureJson(adminModels));
		if (u.endsWith("/admin/api/global-settings")) return response(fixtureJson("global-settings.json"));
		if (u.endsWith("/v1/models")) return response(fixtureJson("v1-models.json"));
		return response({}, 404);
	};
	return { fetch, calls };
}

// Runs `body()` with HOME at a fresh temp dir holding `models` as ~/.pi/agent/models.json (none if undefined).
async function withHome(models, body) {
	const saved = process.env.HOME;
	const home = mkdtempSync(`${tmpdir()}/mellum-home-`);
	if (models !== undefined) {
		mkdirSync(`${home}/.pi/agent`, { recursive: true });
		writeFileSync(`${home}/.pi/agent/models.json`, JSON.stringify(models));
	}
	process.env.HOME = home;
	try {
		return await body(home);
	} finally {
		process.env.HOME = saved;
	}
}

const warnings = (calls) => calls.notify.filter(([, l]) => l === "warning");

test("activation with drifted server settings warns once with the exact message, and Mode still turns on", async () => {
	const server = fakeServer("admin-models-drift.json");
	const { handlers, calls, mellum } = recordingPi({ mode: "tui", fetch: server.fetch });
	await mellum("on");
	assert.deepEqual(calls.notify.filter(([m]) => m.startsWith("Mellum server settings differ")), [[DRIFT_WARNING, "warning"]]);
	assert.deepEqual(server.calls, [{ url: "http://127.0.0.1:8001/admin/api/models", method: "GET" }], "one admin GET, nothing else");
	for (let i = 0; i < 5; i++) assert.equal(handlers.tool_call(read), undefined);
	assert.ok(handlers.tool_call(read)?.block, "mode is on: the sixth identical read is blocked");
});

test("activation with matching server settings warns nothing", async () => {
	const server = fakeServer("admin-models-match.json");
	const { calls, mellum } = recordingPi({ mode: "tui", fetch: server.fetch });
	await mellum("on");
	assert.deepEqual(warnings(calls), []);
	assert.equal(server.calls.length, 1);
});

test("activation ignores server values the client's request overrides (max_tokens, thinking, penalties)", async () => {
	const admin = fixtureJson("admin-models-match.json");
	Object.assign(admin.models[0].settings, { max_tokens: 16384, forced_ct_kwargs: null, enable_thinking: false, presence_penalty: 0.5 });
	const { calls, mellum } = recordingPi({ mode: "tui", fetch: async () => response(admin) });
	await mellum("on");
	assert.deepEqual(warnings(calls), []);
	const rec = await withRunsFile(async () => {
		const { handlers, mellum: m } = recordingPi({ mode: "tui", fetch: async () => response(admin) });
		await m("on");
		handlers.context({ messages: snapshot });
		await m("off");
	});
	assert.deepEqual(rec.server, { match: true, diffs: [] });
});

test("the three server rules warn on activation and mark the record; their near-misses do not", async () => {
	const withSettings = (over) => {
		const admin = fixtureJson("admin-models-match.json");
		Object.assign(admin.models[0].settings, over);
		return admin;
	};
	const activate = async (over) => {
		const { calls, mellum } = recordingPi({ mode: "tui", fetch: async () => response(withSettings(over)) });
		await mellum("on");
		return warnings(calls).map(([m]) => m);
	};
	assert.deepEqual(await activate({ forced_ct_kwargs: ["enable_thinking"], enable_thinking: false }), [
		"Mellum server settings differ: enable_thinking false (expected true). Run /mellum check.",
	]);
	assert.deepEqual(await activate({ force_sampling: true, temperature: 0.6 }), ["Mellum server settings differ: temperature 0.6 (expected 1). Run /mellum check."]);
	assert.deepEqual(await activate({ thinking_budget_enabled: true }), ["Mellum server settings differ: thinking_budget_enabled true (expected false). Run /mellum check."]);
	assert.deepEqual(await activate({ enable_thinking: false }), [], "not forced: the request wins");
	assert.deepEqual(await activate({ force_sampling: false, temperature: 0.6 }), [], "sampling not forced");
	const rec = await withRunsFile(async () => {
		const { handlers, mellum } = recordingPi({ mode: "tui", fetch: async () => response(withSettings({ max_tool_result_tokens: 4000 })) });
		await mellum("on");
		handlers.context({ messages: snapshot });
		await mellum("off");
	});
	assert.deepEqual(rec.server, { match: false, diffs: [{ key: "max_tool_result_tokens", expected: null, actual: 4000 }] });
});

test("the activation check uses the baseUrl of the Pi omlx provider", async () => {
	const models = fixtureJson("pi-models.json");
	models.providers.omlx.baseUrl = "http://127.0.0.1:9999/v1";
	await withHome(models, async () => {
		const server = fakeServer();
		const { mellum } = recordingPi({ mode: "tui", fetch: server.fetch });
		await mellum("on");
		assert.deepEqual(server.calls.map((c) => c.url), ["http://127.0.0.1:9999/admin/api/models"]);
	});
});

test("an activation check whose fetch never resolves and ignores the signal returns within 1,500 ms and warns nothing", async () => {
	const { handlers, calls, mellum } = recordingPi({ mode: "tui", fetch: () => new Promise(() => {}) });
	const t0 = Date.now();
	await mellum("on");
	const elapsed = Date.now() - t0;
	assert.ok(elapsed < 1500, `activation took ${elapsed} ms`);
	assert.deepEqual(warnings(calls), []);
	for (let i = 0; i < 5; i++) assert.equal(handlers.tool_call(read), undefined);
	assert.ok(handlers.tool_call(read)?.block, "mode is on");
});

test("an unreachable server is silent on activation, with or without a UI", async () => {
	const ui = recordingPi({ mode: "tui", hasUI: true });
	await ui.mellum("on");
	assert.deepEqual(warnings(ui.calls), []);
	const headless = recordingPi({ mode: "print", hasUI: false });
	const lines = await captureStderr(() => headless.mellum("on"));
	assert.deepEqual(lines, []);
});

test("the one-shot and headless activations run the check too; without a UI the warning goes to stderr", async () => {
	const oneShot = fakeServer();
	const a = recordingPi({ mode: "tui", hasUI: true, fetch: oneShot.fetch });
	await a.mellum("fix it");
	assert.deepEqual(a.calls.notify.filter(([m]) => m === DRIFT_WARNING), [[DRIFT_WARNING, "warning"]]);
	const headless = fakeServer();
	const b = recordingPi({ mode: "json", hasUI: false, fetch: headless.fetch });
	const saved = process.env.MELLUM_MODE;
	process.env.MELLUM_MODE = "1";
	let lines;
	try {
		lines = await captureStderr(() => b.handlers.session_start({}, b.ctx));
	} finally {
		if (saved === undefined) delete process.env.MELLUM_MODE;
		else process.env.MELLUM_MODE = saved;
	}
	assert.deepEqual(lines, [DRIFT_WARNING]);
	assert.equal(headless.calls.length, 1);
});

test("the run record carries server: match false with the diffs, true when they match, null when unreadable", async () => {
	const span = async (fetch) =>
		withRunsFile(async () => {
			const { handlers, mellum } = recordingPi({ mode: "tui", fetch });
			await mellum("on");
			handlers.context({ messages: snapshot });
			await mellum("off");
		});
	const drift = await span(fakeServer("admin-models-drift.json").fetch);
	assert.deepEqual(drift.server, {
		match: false,
		diffs: [
			{ key: "max_context_window", expected: 56000, actual: 32768 },
			{ key: "turboquant_kv_enabled", expected: false, actual: true },
		],
	});
	assert.deepEqual((await span(fakeServer("admin-models-match.json").fetch)).server, { match: true, diffs: [] });
	assert.deepEqual((await span(noServer)).server, { match: null, diffs: [] });
	assert.deepEqual((await span(async () => response({}, 401))).server, { match: null, diffs: [] });
});

// The text /mellum check should print for the drift fixture with HOME holding pi-models.json.
function expectedCheckText(adminModels) {
	const ok = (value) => ({ ok: true, value });
	const template = providerEntry("pi", JSON.parse(readFileSync(new URL("../templates/pi/models.omlx.json", import.meta.url), "utf8")));
	return formatFindings(
		checkSetup(
			{
				baseUrl: "http://127.0.0.1:8001/v1",
				models: ok(fixtureJson("v1-models.json")),
				adminModels: ok(fixtureJson(adminModels)),
				global: ok(fixtureJson("global-settings.json")),
				provider: { host: "pi", entry: providerEntry("pi", fixtureJson("pi-models.json")) },
				template,
			},
			loadExpected(),
		),
	);
}

test("/mellum check notifies the findings, GETs only, and never turns Mode on", async () => {
	await withHome(fixtureJson("pi-models.json"), async () => {
		const server = fakeServer("admin-models-drift.json");
		const { handlers, calls, mellum } = recordingPi({ mode: "tui", hasUI: true, fetch: server.fetch });
		await mellum("check");
		const text = expectedCheckText("admin-models-drift.json");
		assert.match(text, /^FAIL settings/);
		assert.deepEqual(calls.notify, [[text, "error"]]);
		assert.deepEqual(server.calls.map((c) => c.method), ["GET", "GET", "GET"]);
		assert.deepEqual(calls.setModel, [], "no model switch");
		assert.deepEqual(calls.sendMessage, [], "no marker");
		modeIsOff(handlers);
	});
});

test("/mellum check without a UI prints the findings to stdout", async () => {
	await withHome(fixtureJson("pi-models.json"), async () => {
		const server = fakeServer("admin-models-match.json");
		const { handlers, calls, mellum } = recordingPi({ mode: "print", hasUI: false, fetch: server.fetch });
		const out = [];
		const original = console.log;
		console.log = (...a) => out.push(a.join(" "));
		try {
			await mellum("check");
		} finally {
			console.log = original;
		}
		assert.deepEqual(out, [expectedCheckText("admin-models-match.json")]);
		assert.deepEqual(calls.notify, []);
		assert.deepEqual(calls.setModel, []);
		modeIsOff(handlers);
	});
});

// ---- /mellum learn: the report, the suggestion, and AGENTS.md written only on yes ----

const LEARN_FIX = new URL("./fixtures/learn/patterns/", import.meta.url);

// A temp project dir (real path, as process.cwd() would give) and a runs file whose records
// are the given pattern fixture moved into that dir. HOME is a temp dir; MELLUM_MODE_RUNS names the file.
async function withLearn(pattern, body, { workerPattern } = {}) {
	const { realpathSync } = await import("node:fs");
	const cwd = realpathSync(mkdtempSync(`${tmpdir()}/mellum-learn-cwd-`));
	const runs = `${mkdtempSync(`${tmpdir()}/mellum-learn-runs-`)}/runs.jsonl`;
	const moved = (name) => readFileSync(new URL(`${name}.jsonl`, LEARN_FIX), "utf8").replaceAll("/home/user/proj", cwd);
	writeFileSync(runs, pattern ? moved(pattern) : "");
	const saved = { HOME: process.env.HOME, RUNS: process.env.MELLUM_MODE_RUNS };
	process.env.HOME = mkdtempSync(`${tmpdir()}/mellum-home-`);
	process.env.MELLUM_MODE_RUNS = runs;
	if (workerPattern) {
		mkdirSync(`${process.env.HOME}/.pi/agent`, { recursive: true });
		writeFileSync(`${process.env.HOME}/.pi/agent/mellum-worker-runs.jsonl`, moved(workerPattern));
	}
	try {
		return await body(cwd);
	} finally {
		process.env.HOME = saved.HOME;
		if (saved.RUNS === undefined) delete process.env.MELLUM_MODE_RUNS;
		else process.env.MELLUM_MODE_RUNS = saved.RUNS;
	}
}

// recordingPi with ctx.cwd set and a confirm that records its calls and answers `answer`.
function learnPi(cwd, { hasUI = true, answer = true } = {}) {
	const h = recordingPi({ mode: hasUI ? "tui" : "print", hasUI });
	h.ctx.cwd = cwd;
	h.calls.confirm = [];
	h.ctx.ui.confirm = async (title, message) => {
		h.calls.confirm.push([title, message]);
		return answer;
	};
	return h;
}

test("/mellum learn with a UI: notifies the report, asks, and on yes writes AGENTS.md; Mode stays off", async () => {
	await withLearn("servers", async (cwd) => {
		const { handlers, calls, mellum } = learnPi(cwd, { answer: true });
		await mellum("learn");
		const report = calls.notify.find(([m]) => m.startsWith("mellum learn: "));
		assert.ok(report, JSON.stringify(calls.notify));
		assert.match(report[0], /Mellum started a server in \d+ runs\./);
		assert.match(report[0], /Suggested for AGENTS\.md:/);
		assert.deepEqual(calls.confirm, [["Add these lines to AGENTS.md?", "- Do not: start servers"]]);
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), "# Project\n\n## Mellum\n\n- Do not: start servers\n");
		assert.deepEqual(calls.setModel, []);
		modeIsOff(handlers);
	});
});

test("/mellum learn: confirm false writes nothing", async () => {
	await withLearn("servers", async (cwd) => {
		const { calls, mellum } = learnPi(cwd, { answer: false });
		await mellum("learn 5");
		assert.equal(calls.confirm.length, 1);
		assert.equal(existsSync(`${cwd}/AGENTS.md`), false);
	});
});

test("/mellum learn on an existing AGENTS.md adds only the missing bullets inside its section", async () => {
	await withLearn("servers", async (cwd) => {
		const before = "# P\n\n## Mellum\n\n- Write only: src/\n\n## Notes\n\nx\n";
		writeFileSync(`${cwd}/AGENTS.md`, before);
		const { mellum } = learnPi(cwd, { answer: true });
		await mellum("learn");
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), "# P\n\n## Mellum\n\n- Write only: src/\n- Do not: start servers\n\n## Notes\n\nx\n");
	});
});

test("/mellum learn without a UI prints to stdout, never asks, and writes nothing", async () => {
	await withLearn("servers", async (cwd) => {
		const { calls, mellum } = learnPi(cwd, { hasUI: false, answer: true });
		const out = [];
		const original = console.log;
		console.log = (...a) => out.push(a.join(" "));
		try {
			await mellum("learn");
		} finally {
			console.log = original;
		}
		assert.equal(out.length, 1);
		assert.match(out[0], /^mellum learn: \d+ runs in /);
		assert.match(out[0], /- Do not: start servers/);
		assert.deepEqual(calls.confirm, []);
		assert.deepEqual(calls.notify, []);
		assert.equal(existsSync(`${cwd}/AGENTS.md`), false);
	});
});

test("/mellum learn with no suggestion (or nothing missing, or a conflict) never asks", async () => {
	await withLearn("long-run", async (cwd) => {
		const { calls, mellum } = learnPi(cwd);
		await mellum("learn");
		assert.match(calls.notify[0][0], /took more than 30 requests/);
		assert.deepEqual(calls.confirm, []);
		assert.equal(existsSync(`${cwd}/AGENTS.md`), false);
	});
	await withLearn("test-thrash", async (cwd) => {
		const before = "## Mellum\n\n- Test command: npm test\n";
		writeFileSync(`${cwd}/AGENTS.md`, before);
		const { calls, mellum } = learnPi(cwd);
		await mellum("learn");
		assert.match(calls.notify[0][0], /your Test command: npm test; runs passed with: uv run python -m pytest tests/);
		assert.deepEqual(calls.confirm, []);
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), before);
	});
	await withLearn(undefined, async (cwd) => {
		const { calls, mellum } = learnPi(cwd);
		await mellum("learn");
		assert.equal(calls.notify[0][0], `mellum learn: 0 runs in ${cwd}\nnothing to fix`);
		assert.deepEqual(calls.confirm, []);
	});
});

test("/mellum learn near the 600-character facts cap says so and never asks", async () => {
	await withLearn("servers", async (cwd) => {
		const before = `## Mellum\n\n- Note: ${"x".repeat(584)}\n`;
		writeFileSync(`${cwd}/AGENTS.md`, before);
		const { calls, mellum } = learnPi(cwd, { answer: true });
		await mellum("learn");
		assert.match(calls.notify[0][0], /Adding these would take the section past 600 characters; Mode would ignore it\./);
		assert.deepEqual(calls.confirm, []);
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), before);
	});
});

test("/mellum learn 0 warns and reads nothing; a failed write warns and does not throw", async () => {
	await withLearn("servers", async (cwd) => {
		const { calls, mellum } = learnPi(cwd);
		await mellum("learn 0");
		assert.deepEqual(calls.notify, [["mellum learn: n must be a whole number above 0", "warning"]]);
		assert.deepEqual(calls.confirm, []);
	});
	await withLearn("servers", async (cwd) => {
		const records = readFileSync(process.env.MELLUM_MODE_RUNS, "utf8");
		const gone = `${cwd}/missing-dir`;
		writeFileSync(process.env.MELLUM_MODE_RUNS, records.replaceAll(cwd, gone));
		const { calls, mellum } = learnPi(gone, { answer: true });
		await mellum("learn");
		assert.equal(calls.confirm.length, 1);
		assert.ok(calls.notify.some(([m, l]) => l === "error" && m.startsWith("mellum learn: could not write AGENTS.md")), JSON.stringify(calls.notify));
	});
});

test("/mellum learn: no Suggested block when AGENTS.md already has every line; a missing Do not value is added as its own bullet", async () => {
	await withLearn("servers", async (cwd) => {
		const before = "## Mellum\n\n- Do not: start servers\n";
		writeFileSync(`${cwd}/AGENTS.md`, before);
		const { calls, mellum } = learnPi(cwd, { answer: true });
		await mellum("learn");
		const out = calls.notify[0][0];
		assert.doesNotMatch(out, /Suggested for AGENTS\.md/);
		assert.doesNotMatch(out, /Kept as written/);
		assert.match(out, /\nAGENTS\.md already has these lines\.$/);
		assert.deepEqual(calls.confirm, []);
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), before);
	});
	await withLearn("servers", async (cwd) => {
		const before = "## Mellum\n\n- Do not: install packages or add dependencies\n";
		writeFileSync(`${cwd}/AGENTS.md`, before);
		const { calls, mellum } = learnPi(cwd, { answer: true });
		await mellum("learn");
		assert.match(calls.notify[0][0], /Suggested for AGENTS\.md:\n\n## Mellum\n- Do not: start servers$/);
		assert.deepEqual(calls.confirm, [["Add these lines to AGENTS.md?", "- Do not: start servers"]]);
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), `${before}- Do not: start servers\n`);
	});
});

test("/mellum learn re-reads AGENTS.md after yes: an edit that changes the lines to add (or the cap) writes nothing; any other edit is kept", async () => {
	const answerAfter = (h, edit) => {
		h.ctx.ui.confirm = async (title, message) => {
			h.calls.confirm.push([title, message]);
			edit();
			return true;
		};
	};
	await withLearn("servers", async (cwd) => {
		const edited = "## Mellum\n\n- Do not: start servers\n";
		const h = learnPi(cwd);
		answerAfter(h, () => writeFileSync(`${cwd}/AGENTS.md`, edited));
		await h.mellum("learn");
		assert.equal(h.calls.confirm.length, 1);
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), edited);
		assert.ok(h.calls.notify.some(([m]) => m === "mellum learn: AGENTS.md changed while asking; run /mellum learn again"), JSON.stringify(h.calls.notify));
	});
	await withLearn("servers", async (cwd) => {
		const edited = `## Mellum\n\n- Note: ${"x".repeat(584)}\n`;
		const h = learnPi(cwd);
		answerAfter(h, () => writeFileSync(`${cwd}/AGENTS.md`, edited));
		await h.mellum("learn");
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), edited, "past the cap after the edit: nothing written");
		assert.ok(h.calls.notify.some(([m]) => m === "mellum learn: AGENTS.md changed while asking; run /mellum learn again"), JSON.stringify(h.calls.notify));
	});
	await withLearn("servers", async (cwd) => {
		const h = learnPi(cwd);
		answerAfter(h, () => writeFileSync(`${cwd}/AGENTS.md`, "# Edited\n"));
		await h.mellum("learn");
		assert.equal(readFileSync(`${cwd}/AGENTS.md`, "utf8"), "# Edited\n\n## Mellum\n\n- Do not: start servers\n");
	});
});

test("/mellum check <words> is a one-shot task, not the check", async () => {
	const server = fakeServer("admin-models-match.json");
	const { calls, mellum } = recordingPi({ mode: "tui", hasUI: true, fetch: server.fetch });
	await mellum("check the export totals");
	assert.equal(calls.setModel.length, 1, "Mode switched to Mellum");
	assert.deepEqual(server.calls.map((c) => c.url), ["http://127.0.0.1:8001/admin/api/models"], "only the activation GET");
});

// ---- /mellum last: the newest run as a Markdown table ----

test("parseSubcommand: last is a command; a longer prompt starting with last is a task", async () => {
	const { parseSubcommand } = await import("../extensions/mellum-worker.ts");
	assert.deepEqual(parseSubcommand("last"), { cmd: "last" });
	assert.deepEqual(parseSubcommand(" last "), { cmd: "last" });
	assert.deepEqual(parseSubcommand("last week's bug"), { cmd: "task", task: "last week's bug" });
});

test("/mellum last with a UI and Mode off: one mellum-last message, displayed, that never starts a turn", async () => {
	await withLearn("servers", async (cwd) => {
		const { handlers, calls, mellum } = learnPi(cwd);
		await mellum("last");
		const sent = calls.sendMessage.filter((m) => m.customType === "mellum-last");
		assert.equal(sent.length, 1, JSON.stringify(calls.sendMessage));
		assert.equal(sent[0].display, true);
		assert.match(sent[0].content, /^\*\*mellum last\*\*: Mellum Worker/);
		assert.match(sent[0].content, /\| Metric \| Value \|/);
		assert.deepEqual(calls.lastOptions, [{ triggerTurn: false }]);
		assert.deepEqual(calls.notify, []);
		assert.deepEqual(calls.setModel, []);
		modeIsOff(handlers);
	});
});

test("/mellum last while Mode is on notifies instead, so the table stays out of Mellum's context", async () => {
	await withLearn("servers", async (cwd) => {
		const { calls, mellum } = learnPi(cwd);
		await mellum("on");
		const before = calls.sendMessage.length;
		await mellum("last");
		assert.equal(calls.sendMessage.length, before);
		assert.ok(calls.notify.some(([m, l]) => m.startsWith("**mellum last**: Mellum Worker") && l === "info"), JSON.stringify(calls.notify));
	});
});

test("/mellum last without a UI prints the table to stdout", async () => {
	await withLearn("servers", async (cwd) => {
		const { calls, mellum } = learnPi(cwd, { hasUI: false });
		const out = [];
		const original = console.log;
		console.log = (...a) => out.push(a.join(" "));
		try {
			await mellum("last");
		} finally {
			console.log = original;
		}
		assert.equal(out.length, 1);
		assert.match(out[0], /^\*\*mellum last\*\*/);
		assert.equal(calls.sendMessage.filter((m) => m.customType === "mellum-last").length, 0);
	});
});

test("/mellum last with no runs under the directory says so and names the files it read", async () => {
	await withLearn(undefined, async (cwd) => {
		const { calls, mellum } = learnPi(cwd);
		await mellum("last");
		const note = calls.notify.find(([m]) => m.startsWith("mellum last: "));
		assert.ok(note, JSON.stringify(calls.notify));
		assert.ok(note[0].includes(`no Mellum runs recorded under ${cwd}`), note[0]);
		assert.ok(note[0].includes(process.env.MELLUM_MODE_RUNS), note[0]);
	});
});

test("/mellum last with recording off says recording is off", async () => {
	await withLearn(undefined, async (cwd) => {
		process.env.MELLUM_MODE_RUNS = "0";
		const { calls, mellum } = learnPi(cwd);
		await mellum("last");
		assert.ok(calls.notify.some(([m]) => m.includes("run records are off (MELLUM_MODE_RUNS=0)")), JSON.stringify(calls.notify));
	});
});
