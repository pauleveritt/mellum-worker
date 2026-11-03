import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const load = () => import("../extensions/mellum-worker.ts");

// Run `body()` with the cwd on a fresh temp dir, restoring it afterwards (doTask reads cwd).
async function inTempCwd(body) {
	const dir = mkdtempSync(join(tmpdir(), "mellum-dotask-"));
	const cwd = process.cwd();
	process.chdir(dir);
	try { return await body(dir); } finally { process.chdir(cwd); }
}

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

test("doTask authors the handover, runs the worker, and reports the acceptance verdict", async () => {
	const { doTask, ACCEPTANCE_TEST, ACCEPTANCE_CMD } = await load();
	await inTempCwd(async () => {
		let authoredTask = "", workerBrief = "", ranCmd = "";
		const author = async (task) => {
			authoredTask = task;
			mkdirSync("tests", { recursive: true });
			writeFileSync(ACCEPTANCE_TEST, "def test_x():\n    assert False\n");
			return `wrote ${ACCEPTANCE_TEST} + BRIEF.md`;
		};
		const worker = async (b) => { workerBrief = b; return "worker: implemented, 1 passed"; };
		const acceptance = async (cmd) => { ranCmd = cmd; return { passed: true, output: "1 passed" }; };
		const r = await doTask("build a slugify utility", { author, worker, acceptance });
		assert.equal(authoredTask, "build a slugify utility");
		assert.match(workerBrief, /test_acceptance\.py/, "worker told to pass the authored test");
		assert.match(workerBrief, /do not edit/i, "worker told not to touch the oracle");
		assert.equal(ranCmd, ACCEPTANCE_CMD);
		assert.match(r, /handover:/);
		assert.match(r, /PASS/);
	});
});

test("doTask refuses when the architect writes no acceptance test", async () => {
	const { doTask } = await load();
	await inTempCwd(async () => {
		let workerCalled = false;
		const r = await doTask("x", {
			author: async () => "I refuse to write it",
			worker: async () => { workerCalled = true; return "w"; },
			acceptance: async () => ({ passed: true, output: "" }),
		});
		assert.match(r, /did not write/i);
		assert.equal(workerCalled, false, "no worker runs without a handover");
	});
});

test("in the primary, /mellum <task> authors a handover then runs the worker, no model switch", async () => {
	delete process.env.MELLUM_WORKER_CHILD;
	await inTempCwd(async () => {
		const pi = fakePi();
		let setModelCalled = false;
		pi.setModel = async () => { setModelCalled = true; return true; };
		pi.getActiveTools = () => [];
		let authoredTask = "", workerBrief = "";
		const author = async (t) => { authoredTask = t; mkdirSync("tests", { recursive: true }); writeFileSync("tests/test_acceptance.py", "def t():\n    assert False\n"); return "wrote handover"; };
		const worker = async (b) => { workerBrief = b; return "done"; };
		const acceptance = async () => ({ passed: true, output: "1 passed" });
		(await load()).default(pi, { author, spawnWorker: worker, acceptance });
		const cmd = pi.commands.find((c) => c.name === "mellum");
		const notes = [];
		await cmd.def.handler("build calc.py", { hasUI: true, ui: { notify: (m) => notes.push(m) } });
		assert.equal(authoredTask, "build calc.py", "the architect got the task");
		assert.ok(workerBrief.length > 0, "the worker ran with the brief");
		assert.equal(setModelCalled, false, "the primary does not switch model");
		assert.ok(notes.some((n) => /PASS/.test(n)), "the acceptance verdict is shown");
	});
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
