import { test } from "node:test";
import assert from "node:assert/strict";

const load = () => import("../extensions/mellum-worker.ts");

function fakePi() {
	const tools = [];
	const commands = [];
	const handlers = {};
	return {
		tools,
		commands,
		handlers,
		registerTool: (t) => tools.push(t),
		registerCommand: (name, def) => commands.push({ name, def }),
		on: (event, fn) => { (handlers[event] ??= []).push(fn); },
	};
}

test("loading the worker gives the primary one delegate tool", async () => {
	delete process.env.MELLUM_WORKER_CHILD;
	const pi = fakePi();
	(await load()).default(pi);
	const delegate = pi.tools.filter((t) => t.name === "delegate");
	assert.equal(delegate.length, 1);
	const t = delegate[0];
	assert.match(t.description, /worker/i);
	assert.match(t.description, /do not use it for exploration/i);
	assert.deepEqual(t.parameters.required, ["brief"]);
	assert.equal(t.parameters.properties.brief.type, "string");
});

test("a spawned worker child gets no delegate tool (no recursion)", async () => {
	process.env.MELLUM_WORKER_CHILD = "1";
	const pi = fakePi();
	(await load()).default(pi);
	assert.equal(pi.tools.filter((t) => t.name === "delegate").length, 0);
	delete process.env.MELLUM_WORKER_CHILD;
});

test("delegate with an empty brief refuses without spawning the worker", async () => {
	const { registerDelegate } = await load();
	const pi = fakePi();
	let spawned = false;
	registerDelegate(pi, async () => { spawned = true; return "ran"; });
	const r = await pi.tools[0].execute("id1", { brief: "   " });
	assert.match(r.content[0].text, /empty/i);
	assert.equal(spawned, false);
});

test("delegate with a brief runs the worker and returns its report", async () => {
	const { registerDelegate } = await load();
	const pi = fakePi();
	let seen = "";
	registerDelegate(pi, async (brief) => { seen = brief; return "worker report: 1 passed"; });
	const r = await pi.tools[0].execute("id1", { brief: "build app.py so pytest passes" });
	assert.equal(seen, "build app.py so pytest passes");
	assert.match(r.content[0].text, /1 passed/);
});

test("in the primary, /mellum <task> runs the tool: delegates to a worker, no model switch", async () => {
	delete process.env.MELLUM_WORKER_CHILD;
	const pi = fakePi();
	let setModelCalled = false;
	pi.setModel = async () => { setModelCalled = true; return true; };
	pi.getActiveTools = () => [];
	let briefSeen = "";
	(await load()).default(pi, { spawnWorker: async (b) => { briefSeen = b; return "report: 1 passed"; } });
	const cmd = pi.commands.find((c) => c.name === "mellum");
	const notes = [];
	await cmd.def.handler("build calc.py so pytest passes", { hasUI: true, ui: { notify: (m) => notes.push(m) } });
	assert.equal(briefSeen, "build calc.py so pytest passes");
	assert.equal(setModelCalled, false);
	assert.ok(notes.some((n) => /1 passed/.test(n)), "the worker report is shown");
});

test("a spawned child does NOT re-delegate on /mellum <task>", async () => {
	process.env.MELLUM_WORKER_CHILD = "1";
	const pi = fakePi();
	pi.getActiveTools = () => [];
	let delegated = false;
	(await load()).default(pi, { spawnWorker: async () => { delegated = true; return "x"; } });
	const cmd = pi.commands.find((c) => c.name === "mellum");
	// No Mellum model available, so activate bails out — enough to prove the child takes the
	// in-session path (activate) rather than spawning another worker.
	await cmd.def.handler("do the work here", { hasUI: false, model: { id: "other" }, modelRegistry: { find: () => undefined } });
	assert.equal(delegated, false);
	delete process.env.MELLUM_WORKER_CHILD;
});

test("withDelegateNudge appends the nudge to user messages only", async () => {
	const { withDelegateNudge } = await load();
	const out = withDelegateNudge({
		messages: [
			{ role: "system", content: "sys" },
			{ role: "user", content: "add a /health route" },
			{ role: "assistant", content: "ok" },
		],
	});
	assert.equal(out.messages[0].content, "sys");
	assert.match(out.messages[1].content, /add a \/health route/);
	assert.match(out.messages[1].content, /delegate/i);
	assert.equal(out.messages[2].content, "ok");
});
