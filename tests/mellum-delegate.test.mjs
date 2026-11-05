import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
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

test("authorPhasesPrompt tells the architect to split into ordered phases and pin named contracts", async () => {
	const { authorPhasesPrompt } = await load();
	const p = authorPhasesPrompt("build a board");
	assert.match(p, /ORDERED PHASES/i);
	assert.match(p, /test_phaseN_<slug>\.py/);
	assert.match(p, /contiguous/i);
	assert.match(p, /NAMED CONTRACTS/i);
	assert.match(p, /stay green once later\s+phases are built/i, "phase tests are cumulative-safe");
	assert.match(p, /SINGLE-quoted/i, "warns against nested double-quotes");
});

test("listPhaseTests returns the phase files ordered by phase number", async () => {
	const { listPhaseTests } = await load();
	await inTempCwd(async (dir) => {
		mkdirSync(join(dir, "tests"), { recursive: true });
		for (const f of ["test_phase2_board.py", "test_phase10_last.py", "test_phase1_home.py", "test_helpers.py"]) writeFileSync(join(dir, "tests", f), "x = 1\n");
		assert.deepEqual(listPhaseTests(dir), ["tests/test_phase1_home.py", "tests/test_phase2_board.py", "tests/test_phase10_last.py"]);
	});
});

test("phaseCmd is cumulative and phaseWorkerBrief freezes the oracle and warns from phase 2", async () => {
	const { phaseCmd, phaseWorkerBrief } = await load();
	const paths = ["tests/test_phase1_a.py", "tests/test_phase2_b.py"];
	assert.equal(phaseCmd(paths, 0), "uv run --with pytest python -m pytest tests/test_phase1_a.py -q");
	assert.equal(phaseCmd(paths, 1), "uv run --with pytest python -m pytest tests/test_phase1_a.py tests/test_phase2_b.py -q");
	const b0 = phaseWorkerBrief(paths, 0);
	assert.match(b0, /phase 1 of 2/);
	assert.match(b0, /do NOT edit any tests\/test_phase\*\.py/i);
	assert.doesNotMatch(b0, /do NOT break/i, "phase 1 has no earlier phase to break");
	assert.match(b0, /only inside this directory/i, "the worker is scoped to its own directory");
	const b1 = phaseWorkerBrief(paths, 1);
	assert.match(b1, /phase 2 of 2/);
	assert.match(b1, /do NOT break them/i);
});

test("doTaskPhased runs one fresh worker per phase against the cumulative test and reports a full pass", async () => {
	const { doTaskPhased } = await load();
	await inTempCwd(async () => {
		const workerBriefs = [], ran = [];
		const authorPhases = async () => { mkdirSync("tests", { recursive: true }); writeFileSync("tests/test_phase1_a.py", "def t():\n    assert True\n"); writeFileSync("tests/test_phase2_b.py", "def t():\n    assert True\n"); return "wrote 2 phases"; };
		const worker = async (b) => { workerBriefs.push(b); return "impl"; };
		const acceptance = async (cmd) => { ran.push(cmd); return { passed: true, output: "ok" }; };
		const compile = async () => undefined;
		const shell = async () => ({ passed: false, output: "" }); // report no git, so no checkpoint side effects
		const r = await doTaskPhased("build it", { authorPhases, worker, acceptance, compile, shell });
		assert.equal(workerBriefs.length, 2, "one worker per phase");
		assert.match(ran[0], /test_phase1_a\.py -q$/);
		assert.match(ran[1], /test_phase1_a\.py tests\/test_phase2_b\.py -q$/, "phase 2 runs the cumulative command");
		assert.match(r, /phases passed: 2\/2/);
		assert.match(r, /full pass/);
	});
});

test("doTaskPhased stops at the first failing phase and does not run later phases", async () => {
	const { doTaskPhased, MAX_PHASE_RETRIES } = await load();
	await inTempCwd(async () => {
		let workerCalls = 0;
		const authorPhases = async () => { mkdirSync("tests", { recursive: true }); for (const n of [1, 2, 3]) writeFileSync(`tests/test_phase${n}_x.py`, "def t():\n    assert True\n"); return "wrote 3 phases"; };
		const worker = async () => { workerCalls++; return "impl"; };
		const acceptance = async (cmd) => ({ passed: !cmd.includes("test_phase2"), output: "boom" }); // phase 2 never passes
		const r = await doTaskPhased("x", { authorPhases, worker, acceptance, compile: async () => undefined, shell: async () => ({ passed: false, output: "" }) });
		assert.equal(workerCalls, 1 + (MAX_PHASE_RETRIES + 1), "phase 1 once, phase 2 retried then given up, phase 3 never");
		assert.match(r, /phases passed: 1\/3/);
		assert.match(r, /stopped at the first failing phase/);
	});
});

test("doTaskPhased repairs a phase test that does not parse before running the worker", async () => {
	const { doTaskPhased } = await load();
	await inTempCwd(async () => {
		let repairedPath = "", parses = false, workerRan = false;
		const authorPhases = async () => { mkdirSync("tests", { recursive: true }); writeFileSync("tests/test_phase1_a.py", "broken\n"); return "wrote 1 phase"; };
		const compile = async (p) => (parses ? undefined : (p.includes("test_phase1_a.py") ? "SyntaxError: invalid syntax" : undefined));
		const repair = async (err, p) => { repairedPath = p; parses = true; writeFileSync("tests/test_phase1_a.py", "def t():\n    assert True\n"); return "fixed"; };
		const worker = async () => { workerRan = true; return "impl"; };
		const r = await doTaskPhased("x", { authorPhases, worker, compile, repair, acceptance: async () => ({ passed: true, output: "ok" }), shell: async () => ({ passed: false, output: "" }) });
		assert.match(repairedPath, /tests\/test_phase1_a\.py/, "repair was called with the phase test path");
		assert.equal(workerRan, true, "the worker ran after the phase test was made to parse");
		assert.match(r, /phases passed: 1\/1/);
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
	assert.match(p, /SINGLE-quoted/i, "warns against nested double-quotes");
});

test("repairPrompt names a path, forbids weakening, and tells the architect to rewrite via write", async () => {
	const { repairPrompt } = await load();
	const p = repairPrompt("SyntaxError: x", "tests/test_phase1_home.py");
	assert.match(p, /tests\/test_phase1_home\.py/, "names the broken file");
	assert.match(p, /do NOT.*weaken|weaken.*meaning/i, "keeps the assertions");
	assert.match(p, /always true/i, "forbids turning a check into a tautology");
	assert.match(p, /WRITE tool to replace the ENTIRE file/i, "rewrite, not piecemeal edits");
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

// ── Step-file delegation (MELLUM_DELEGATE_STEPS=1) ──────────────────────────────

test("authorStepsPrompt splits the spec into small ordered steps with a doc + self-contained test each + a todo.md", async () => {
	const { authorStepsPrompt } = await load();
	const p = authorStepsPrompt("build a board");
	assert.match(p, /SMALL ORDERED STEPS/i);
	assert.match(p, /stepNN\.md/, "each step gets its own instruction doc");
	assert.match(p, /test_stepN_<slug>\.py/, "each step gets its own test");
	assert.match(p, /SELF-CONTAINED/i, "each step test stands on that step alone");
	assert.match(p, /todo\.md/i, "a todo.md ledger is written");
	assert.match(p, /- \[ \] step01/, "the ledger starts unchecked");
	assert.match(p, /NAMED CONTRACTS/i);
	assert.match(p, /contiguous/i);
	assert.match(p, /SINGLE-quoted/i, "warns against nested double-quotes");
});

test("listSteps pairs each stepNN.md with its numbered test, ordered, and skips an unpaired doc", async () => {
	const { listSteps } = await load();
	await inTempCwd(async (dir) => {
		mkdirSync(join(dir, "tests"), { recursive: true });
		for (const f of ["step02.md", "step10.md", "step01.md", "step03.md"]) writeFileSync(join(dir, f), "do this\n");
		for (const f of ["test_step2_board.py", "test_step10_last.py", "test_step1_home.py", "test_helpers.py"]) writeFileSync(join(dir, "tests", f), "x = 1\n");
		// step03 has a doc but no test → it cannot be gated, so it is not listed.
		assert.deepEqual(listSteps(dir), [
			{ n: 1, doc: "step01.md", test: "tests/test_step1_home.py" },
			{ n: 2, doc: "step02.md", test: "tests/test_step2_board.py" },
			{ n: 10, doc: "step10.md", test: "tests/test_step10_last.py" },
		]);
	});
});

test("stepTestCmd is self-contained (that step only) and stepWorkerBrief points at the step doc, freezes the oracle, warns from step 2", async () => {
	const { stepTestCmd, allStepsCmd, stepWorkerBrief } = await load();
	const steps = [
		{ n: 1, doc: "step01.md", test: "tests/test_step1_a.py" },
		{ n: 2, doc: "step02.md", test: "tests/test_step2_b.py" },
	];
	assert.equal(stepTestCmd(steps[0]), "uv run --with pytest python -m pytest tests/test_step1_a.py -q");
	assert.equal(stepTestCmd(steps[1]), "uv run --with pytest python -m pytest tests/test_step2_b.py -q", "each step runs its own test alone, not the cumulative set");
	assert.equal(allStepsCmd(steps), "uv run --with pytest python -m pytest tests/test_step1_a.py tests/test_step2_b.py -q");
	const b0 = stepWorkerBrief(steps, 0);
	assert.match(b0, /step 1 of 2/);
	assert.match(b0, /Read step01\.md/, "the worker reads its own step doc");
	assert.match(b0, /do NOT edit any tests\/test_step\*\.py/i);
	assert.doesNotMatch(b0, /do NOT break/i, "step 1 has no earlier step to break");
	assert.match(b0, /only inside this directory/i);
	assert.match(b0, /original spec|specs\/|roadmap/i, "the worker may still consult the original spec plan");
	const b1 = stepWorkerBrief(steps, 1);
	assert.match(b1, /step 2 of 2/);
	assert.match(b1, /Read step02\.md/);
	assert.match(b1, /do NOT break them/i);
});

test("renderTodo ticks only the verified steps and counts them in the header", async () => {
	const { renderTodo } = await load();
	const steps = [
		{ n: 1, doc: "step01.md", test: "tests/test_step1_a.py" },
		{ n: 2, doc: "step02.md", test: "tests/test_step2_b.py" },
	];
	const t = renderTodo(steps, new Set([1]));
	assert.match(t, /1\/2 steps done and tested/);
	assert.match(t, /- \[x\] step01 — step01\.md — tests\/test_step1_a\.py/);
	assert.match(t, /- \[ \] step02 — step02\.md — tests\/test_step2_b\.py/);
});

test("doTaskSteps runs one fresh worker per step against its own test, ticks todo.md as the harness verifies, and reports 100%", async () => {
	const { doTaskSteps } = await load();
	await inTempCwd(async (dir) => {
		const briefs = [], ran = [];
		const authorSteps = async () => {
			mkdirSync("tests", { recursive: true });
			writeFileSync("step01.md", "build home\n"); writeFileSync("step02.md", "build board\n");
			writeFileSync("tests/test_step1_home.py", "def t():\n    assert True\n");
			writeFileSync("tests/test_step2_board.py", "def t():\n    assert True\n");
			return "wrote 2 steps";
		};
		const worker = async (b) => { briefs.push(b); return "impl"; };
		const acceptance = async (cmd) => { ran.push(cmd); return { passed: true, output: "ok" }; };
		const compile = async () => undefined;
		const shell = async () => ({ passed: false, output: "" }); // report no git
		const r = await doTaskSteps("build it", { authorSteps, authorVerify: async () => "", worker, acceptance, compile, shell });
		assert.equal(briefs.length, 2, "one worker per step");
		assert.match(ran[0], /test_step1_home\.py -q$/, "step 1 runs its own test only");
		assert.match(ran[1], /test_step2_board\.py -q$/, "step 2 runs its own test only (self-contained)");
		assert.match(r, /steps done and tested: 2\/2/);
		assert.match(r, /100%/);
		const todo = readFileSync(join(dir, "todo.md"), "utf8");
		assert.match(todo, /2\/2 steps done/);
		assert.doesNotMatch(todo, /\[ \]/, "every step is ticked");
	});
});

test("doTaskSteps stops at the first failing step and leaves its todo.md line unchecked", async () => {
	const { doTaskSteps, MAX_STEP_RETRIES } = await load();
	await inTempCwd(async (dir) => {
		let workerCalls = 0;
		const authorSteps = async () => {
			mkdirSync("tests", { recursive: true });
			for (const n of [1, 2, 3]) { writeFileSync(`step0${n}.md`, "x\n"); writeFileSync(`tests/test_step${n}_x.py`, "def t():\n    assert True\n"); }
			return "wrote 3 steps";
		};
		const worker = async () => { workerCalls++; return "impl"; };
		const acceptance = async (cmd) => ({ passed: !cmd.includes("test_step2"), output: "boom" }); // step 2 never passes
		const r = await doTaskSteps("x", { authorSteps, authorVerify: async () => "", worker, acceptance, compile: async () => undefined, shell: async () => ({ passed: false, output: "" }) });
		assert.equal(workerCalls, 1 + (MAX_STEP_RETRIES + 1), "step 1 once, step 2 retried then given up, step 3 never");
		assert.match(r, /steps done and tested: 1\/3/);
		assert.match(r, /stopped at the first failing step/);
		const todo = readFileSync(join(dir, "todo.md"), "utf8");
		assert.match(todo, /- \[x\] step01/);
		assert.match(todo, /- \[ \] step02/);
		assert.match(todo, /- \[ \] step03/);
	});
});

test("doTaskSteps declares done only when the final full-suite run is green, even if every step was ticked", async () => {
	const { doTaskSteps } = await load();
	await inTempCwd(async () => {
		const authorSteps = async () => {
			mkdirSync("tests", { recursive: true });
			for (const n of [1, 2]) { writeFileSync(`step0${n}.md`, "x\n"); writeFileSync(`tests/test_step${n}_x.py`, "def t():\n    assert True\n"); }
			return "wrote 2 steps";
		};
		const worker = async () => "impl";
		// Each single-step run passes; the final full-suite run (both tests together) fails → not done.
		const acceptance = async (cmd) => ({ passed: !(cmd.includes("test_step1_x.py") && cmd.includes("test_step2_x.py")), output: "regression" });
		const r = await doTaskSteps("x", { authorSteps, authorVerify: async () => "", worker, acceptance, compile: async () => undefined, shell: async () => ({ passed: false, output: "" }) });
		assert.match(r, /steps done and tested: 2\/2/);
		assert.match(r, /all ticked but the full suite did not pass/i);
		assert.doesNotMatch(r, /100%/);
	});
});

test("doTaskSteps refuses when the architect writes no paired step doc + test", async () => {
	const { doTaskSteps } = await load();
	await inTempCwd(async () => {
		const authorSteps = async () => { writeFileSync("step01.md", "x\n"); return "no test written"; }; // doc but no test
		const r = await doTaskSteps("x", { authorSteps, worker: async () => "impl", acceptance: async () => ({ passed: true, output: "" }), compile: async () => undefined, shell: async () => ({ passed: false, output: "" }) });
		assert.match(r, /no paired stepNN\.md/i);
	});
});

test("authorStepsPrompt makes the requirements the contract, not the spec's suggested tests, and asserts through the rendered surface", async () => {
	const { authorStepsPrompt } = await load();
	const p = authorStepsPrompt("build a board");
	assert.match(p, /FLOOR, not the ceiling/i, "the spec's own 'write tests' line is a floor, not the ceiling");
	assert.match(p, /EVERY requirement the step states/i);
	assert.match(p, /RESPONSE BODY|rendered page/i, "a rendered requirement is asserted through the response body");
	assert.match(p, /real end-to-end path|through the route/i, "exercise the real path, not seed mutation");
	assert.match(p, /FAIL on the obvious wrong build/i, "red-on-the-miss");
});

test("authorStepsPrompt tells the architect to copy the verbatim spec text into each step as its north star", async () => {
	const { authorStepsPrompt } = await load();
	const p = authorStepsPrompt("build a board");
	assert.match(p, /north star/i);
	assert.match(p, /COPY the exact spec text|copy[^.]*verbatim/i, "the exact spec requirement lines are copied in");
	assert.match(p, /Spec \(verbatim\)/, "under a verbatim-spec heading in the step doc");
	assert.match(p, /original spec plan|point back/i, "each step stays linked to the original spec plan");
});

test("authorVerifyPrompt tells the architect to check each spec requirement is asserted, edit only tests, and never weaken", async () => {
	const { authorVerifyPrompt } = await load();
	const p = authorVerifyPrompt("build a board");
	assert.match(p, /FINAL SPEC-COVERAGE PASS/i);
	assert.match(p, /requirements are the contract/i);
	assert.match(p, /FLOOR, not the ceiling/i);
	assert.match(p, /ADD the missing assertion/i);
	assert.match(p, /Edit ONLY the step docs and test files/i);
	assert.match(p, /do NOT.*weaken/i, "existing assertions must not be weakened");
	assert.match(p, /north star|verbatim/i, "checks the step quotes the spec verbatim as its north star");
	assert.match(p, /SINGLE-quoted/i, "carries the quoting rule");
});

test("stepWorkerBrief feeds the actual failure back as bugs only on a retry", async () => {
	const { stepWorkerBrief } = await load();
	const steps = [{ n: 1, doc: "step01.md", test: "tests/test_step1_a.py" }];
	const first = stepWorkerBrief(steps, 0);
	assert.doesNotMatch(first, /bugs/i, "the first attempt carries no bug feedback");
	const retry = stepWorkerBrief(steps, 0, "E   AssertionError: badge 'Resolved' not rendered");
	assert.match(retry, /did NOT pass/i);
	assert.match(retry, /bugs/i);
	assert.match(retry, /badge 'Resolved' not rendered/, "the real failure is handed back verbatim");
});

test("doTaskSteps runs a final spec-coverage pass before freezing and feeds the failure back on retry", async () => {
	const { doTaskSteps } = await load();
	await inTempCwd(async () => {
		let verifyCalled = 0;
		const briefs = [];
		const authorSteps = async () => {
			mkdirSync("tests", { recursive: true });
			writeFileSync("step01.md", "build home\n");
			writeFileSync("tests/test_step1_home.py", "def t():\n    assert True\n");
			return "wrote 1 step";
		};
		const authorVerify = async () => { verifyCalled++; return "coverage pass done"; };
		const worker = async (b) => { briefs.push(b); return "impl"; };
		let n = 0;
		// First attempt fails (hands back the bug), retry passes; then the final full-suite run passes.
		const acceptance = async () => ({ passed: ++n > 1, output: "E   AssertionError: badge not rendered" });
		const r = await doTaskSteps("x", { authorSteps, authorVerify, worker, acceptance, compile: async () => undefined, shell: async () => ({ passed: false, output: "" }) });
		assert.equal(verifyCalled, 1, "the final spec-coverage pass ran once, before the worker loop");
		assert.equal(briefs.length, 2, "the worker retried after the first failure");
		assert.doesNotMatch(briefs[0], /bugs/i, "first attempt: no bug feedback");
		assert.match(briefs[1], /badge not rendered/, "retry: the actual failure is fed back as bugs");
		assert.match(r, /steps done and tested: 1\/1/);
	});
});

// ── Code-eval remedies wired into the delegation workers ────────────────────────

test("resolveRemedyFiles turns a preset into existing remedy unit files and skips unknown names", async () => {
	const { resolveRemedyFiles } = await load();
	const files = resolveRemedyFiles("preset:medium");
	assert.ok(files.length >= 1, "the medium preset resolves to at least one unit file");
	assert.ok(files.every((f) => f.endsWith(".ts")), "each resolved unit is a .ts file");
	assert.ok(files.some((f) => /prompt\/python-developer\.ts$/.test(f)), "the medium preset includes prompt/python-developer");
	assert.deepEqual(resolveRemedyFiles("guard/does-not-exist"), [], "an unknown unit is skipped, not fatal");
	assert.deepEqual(resolveRemedyFiles(""), [], "no spec means no remedies");
	assert.deepEqual(resolveRemedyFiles(undefined), []);
});

test("remedyArgs renders the resolved units as -e file arguments for the spawned worker", async () => {
	const { remedyArgs } = await load();
	const args = remedyArgs("prompt/python-developer");
	assert.equal(args.length, 2);
	assert.equal(args[0], "-e");
	assert.match(args[1], /remedies\/prompt\/python-developer\.ts$/);
	assert.deepEqual(remedyArgs(""), [], "no remedies when the spec is empty (bare worker, the measured default)");
});

// ── Plan delegation, no per-step tests (MELLUM_DELEGATE_PLAN=1) ──────────────────

test("authorPlanPrompt splits the spec into step docs with the verbatim spec and writes NO tests", async () => {
	const { authorPlanPrompt } = await load();
	const p = authorPlanPrompt("build a board");
	assert.match(p, /SMALL ORDERED STEPS/i);
	assert.match(p, /stepNN\.md/);
	assert.match(p, /Spec \(verbatim\)/, "the exact spec text is copied into each step doc");
	assert.match(p, /todo\.md/i);
	assert.match(p, /do NOT write (any )?tests|no test files/i, "the plan mode writes no tests");
	assert.doesNotMatch(p, /test_step/i, "no per-step test files are requested");
	assert.match(p, /run out/i, "it nudges the architect to write files first and keep reasoning short so it does not run out of output (truncation guard)");
});

test("listStepDocs returns the step docs by number, no paired test required", async () => {
	const { listStepDocs } = await load();
	await inTempCwd(async (dir) => {
		for (const f of ["step02.md", "step01.md", "step10.md", "notes.md"]) writeFileSync(join(dir, f), "x\n");
		assert.deepEqual(listStepDocs(dir), [
			{ n: 1, doc: "step01.md" },
			{ n: 2, doc: "step02.md" },
			{ n: 10, doc: "step10.md" },
		]);
	});
});

test("planWorkerBrief tells the worker to build its step from the doc and consult the spec, with no test gate", async () => {
	const { planWorkerBrief } = await load();
	const steps = [{ n: 1, doc: "step01.md" }, { n: 2, doc: "step02.md" }];
	const b0 = planWorkerBrief(steps, 0);
	assert.match(b0, /step 1 of 2/);
	assert.match(b0, /Read step01\.md/);
	assert.match(b0, /original spec|specs\//i, "the worker may consult the original spec plan");
	assert.match(b0, /only inside this directory/i);
	assert.doesNotMatch(b0, /pytest|test passes/i, "there is no per-step test to run");
	assert.doesNotMatch(planWorkerBrief(steps, 0), /do NOT break/i);
	assert.match(planWorkerBrief(steps, 1), /do NOT break/i, "a later step must not break earlier ones");
});

test("doTaskPlan runs one worker per step doc, ticks todo and checkpoints, with no acceptance gate", async () => {
	const { doTaskPlan } = await load();
	await inTempCwd(async (dir) => {
		const briefs = [];
		const authorPlan = async () => { writeFileSync("step01.md", "home\n"); writeFileSync("step02.md", "board\n"); return "wrote 2 step docs"; };
		const worker = async (b) => { briefs.push(b); return "built"; };
		const shell = async () => ({ passed: false, output: "" }); // git off
		const r = await doTaskPlan("build it", { authorPlan, worker, shell });
		assert.equal(briefs.length, 2, "one worker per step doc");
		assert.match(r, /steps built: 2\/2/);
		const todo = readFileSync(join(dir, "todo.md"), "utf8");
		assert.match(todo, /2\/2 steps built/);
		assert.doesNotMatch(todo, /\[ \]/, "every step is ticked");
	});
});

test("doTaskPlan retries the architect when it writes no step docs, then runs the recovered plan", async () => {
	const { doTaskPlan } = await load();
	await inTempCwd(async () => {
		const tasks = [];
		// Attempt 1 writes nothing (the output-token truncation); attempt 2 writes the docs.
		const authorPlan = async (t) => {
			tasks.push(t);
			if (tasks.length >= 2) { writeFileSync("step01.md", "home\n"); writeFileSync("step02.md", "board\n"); return "wrote 2"; }
			return "truncated — nothing written";
		};
		const r = await doTaskPlan("build it", { authorPlan, worker: async () => "built", shell: async () => ({ passed: false, output: "" }) });
		assert.equal(tasks.length, 2, "the architect is re-dispatched after writing no docs");
		assert.match(tasks[1], /RETRY|wrote no|write .*first|run out/i, "the retry carries feedback about the miss");
		assert.match(r, /steps built: 2\/2/, "the recovered plan runs");
	});
});

test("doTaskPlan refuses only after the retries are exhausted", async () => {
	const { doTaskPlan, MAX_AUTHOR_RETRIES } = await load();
	await inTempCwd(async () => {
		let calls = 0;
		const authorPlan = async () => { calls++; return "nothing written"; };
		const r = await doTaskPlan("x", { authorPlan, worker: async () => "built", shell: async () => ({ passed: false, output: "" }) });
		assert.equal(calls, MAX_AUTHOR_RETRIES + 1, "one initial attempt plus the retry budget");
		assert.match(r, /no step(NN)?\.?md|no step docs/i);
	});
});

test("planMinSteps scales a step floor with the spec's requirement bullets, and is 0 for prose", async () => {
	const { planMinSteps } = await load();
	assert.equal(planMinSteps("just build the thing, no bullets here"), 0, "a prose spec imposes no floor");
	const spec = Array.from({ length: 10 }, (_, i) => `- requirement number ${i + 1} that must hold`).join("\n");
	assert.ok(planMinSteps(spec) >= 2, "ten requirement bullets floor the plan above one step");
	assert.ok(planMinSteps(spec) <= 10, "the floor never exceeds the requirement count");
});

test("doTaskPlan re-dispatches for a finer split when the plan is too coarse for the spec", async () => {
	const { doTaskPlan } = await load();
	await inTempCwd(async () => {
		const spec = Array.from({ length: 10 }, (_, i) => `- requirement ${i + 1}`).join("\n"); // floor >= 2
		const tasks = [];
		const authorPlan = async (t) => {
			tasks.push(t);
			if (tasks.length >= 2) { writeFileSync("step01.md", "a\n"); writeFileSync("step02.md", "b\n"); writeFileSync("step03.md", "c\n"); return "3"; }
			writeFileSync("step01.md", "everything in one coarse step\n"); return "1"; // too coarse
		};
		const r = await doTaskPlan(spec, { authorPlan, worker: async () => "built", shell: async () => ({ passed: false, output: "" }) });
		assert.equal(tasks.length, 2, "a coarse plan is re-dispatched");
		assert.match(tasks[1], /split|finer|smaller|at most|requirement/i, "the retry asks for a finer split");
		assert.match(r, /steps built: 3\/3/, "the finer plan runs");
	});
});

test("doTaskPlan runs a coarse plan as best effort once the split retries are spent, and says so", async () => {
	const { doTaskPlan, MAX_AUTHOR_RETRIES } = await load();
	await inTempCwd(async () => {
		const spec = Array.from({ length: 10 }, (_, i) => `- requirement ${i + 1}`).join("\n"); // floor >= 2
		let calls = 0;
		const authorPlan = async () => { calls++; writeFileSync("step01.md", "one coarse step\n"); return "1"; };
		const r = await doTaskPlan(spec, { authorPlan, worker: async () => "built", shell: async () => ({ passed: false, output: "" }) });
		assert.equal(calls, MAX_AUTHOR_RETRIES + 1, "it retried for a finer split before giving up");
		assert.match(r, /steps built: 1\/1/, "the coarse plan still runs rather than being thrown away");
		assert.match(r, /coarse|below .*floor|fewer steps/i, "the report flags that the plan stayed coarse");
	});
});
