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

test("doTask asks the architect to repair an oracle that does not parse, then runs the worker", async () => {
	const { doTask, ACCEPTANCE_TEST } = await load();
	await inTempCwd(async () => {
		let repairs = 0, workerRan = false, parses = false;
		const author = async () => { mkdirSync("tests", { recursive: true }); writeFileSync(ACCEPTANCE_TEST, "broken\n"); return "wrote a broken test"; };
		const compile = async () => (parses ? undefined : 'SyntaxError: invalid syntax');
		const repair = async (err) => { repairs++; assert.match(err, /SyntaxError/); parses = true; writeFileSync(ACCEPTANCE_TEST, "def t():\n    assert False\n"); return "fixed the syntax"; };
		const worker = async () => { workerRan = true; return "worker: 1 passed"; };
		const acceptance = async () => ({ passed: true, output: "1 passed" });
		const r = await doTask("build it", { author, compile, repair, worker, acceptance });
		assert.equal(repairs, 1, "the architect was asked to repair once");
		assert.equal(workerRan, true, "the worker ran after the oracle was made to parse");
		assert.match(r, /PASS/);
	});
});

test("doTask refuses (no worker) when the oracle still does not parse after repairs", async () => {
	const { doTask, ACCEPTANCE_TEST, MAX_ORACLE_REPAIRS } = await load();
	await inTempCwd(async () => {
		let repairs = 0, workerRan = false;
		const author = async () => { mkdirSync("tests", { recursive: true }); writeFileSync(ACCEPTANCE_TEST, "broken\n"); return "wrote a broken test"; };
		const compile = async () => 'SyntaxError: invalid syntax';
		const repair = async () => { repairs++; return "tried"; };
		const worker = async () => { workerRan = true; return "w"; };
		const r = await doTask("x", { author, compile, repair, worker, acceptance: async () => ({ passed: true, output: "" }) });
		assert.equal(repairs, MAX_ORACLE_REPAIRS, "it gives up after the cap");
		assert.equal(workerRan, false, "no worker runs behind an unparseable oracle");
		assert.match(r, /does not parse/i);
	});
});

test("compileTest resolves undefined on valid Python and an error string on a syntax error", async () => {
	const { compileTest } = await load();
	await inTempCwd(async (dir) => {
		const ok = join(dir, "ok.py");
		writeFileSync(ok, "x = 1\n");
		assert.equal(await compileTest(ok), undefined, "valid file compiles");
		const bad = join(dir, "bad.py");
		writeFileSync(bad, 'assert "a "b"" in c\n');
		const err = await compileTest(bad);
		assert.match(String(err), /SyntaxError|py_compile/, "broken file reports the error");
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

test("streamTurn renders tool calls and text from content blocks when verbose", async () => {
	const { streamTurn } = await load();
	const orig = process.stdout.write.bind(process.stdout);
	let buf = "";
	process.stdout.write = (s) => { buf += s; return true; };
	process.env.MELLUM_DELEGATE_VERBOSE = "1";
	try {
		streamTurn({ role: "assistant", content: [
			{ type: "thinking", text: "I will create app.py" },
			{ type: "toolCall", name: "write", arguments: { path: "app.py" } },
			{ type: "toolCall", name: "bash", arguments: { command: "uv run pytest -q" } },
			{ type: "text", text: "done" },
		] });
	} finally {
		process.stdout.write = orig;
		delete process.env.MELLUM_DELEGATE_VERBOSE;
	}
	assert.match(buf, /💭 I will create app\.py/);
	assert.match(buf, /→ write app\.py/);
	assert.match(buf, /→ bash uv run pytest -q/);
	assert.match(buf, /done/);
	assert.doesNotMatch(buf, /· \(turn\)/, "has real content, so no bare-turn fallback");
});

test("streamTurn is silent when not verbose", async () => {
	const { streamTurn } = await load();
	const orig = process.stdout.write.bind(process.stdout);
	let buf = "";
	process.stdout.write = (s) => { buf += s; return true; };
	delete process.env.MELLUM_DELEGATE_VERBOSE;
	try { streamTurn({ role: "assistant", content: [{ type: "text", text: "x" }] }); }
	finally { process.stdout.write = orig; }
	assert.equal(buf, "");
});

test("authorPrompt tells the architect to pin exact named contracts, not just behaviour", async () => {
	const { authorPrompt } = await load();
	const p = authorPrompt("build a complaints board");
	assert.match(p, /named contracts/i, "names the contract discipline");
	assert.match(p, /module-level variable or attribute/i, "pins module-level names");
	assert.match(p, /exact count/i, "pins counts");
	assert.match(p, /verbatim seed string/i, "pins verbatim seed values");
	assert.match(p, /import the module and check the attribute/i, "asserts the named thing directly, not only via a route");
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
