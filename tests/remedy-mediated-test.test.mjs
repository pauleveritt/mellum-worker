import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join } from "node:path";

function fakePi() {
	const handlers = {};
	return {
		handlers,
		on(event, handler) { (handlers[event] ??= []).push(handler); },
		names() { return Object.keys(handlers).sort(); },
	};
}

async function withEnv(vars, fn) {
	const saved = Object.fromEntries(Object.keys(vars).map((k) => [k, process.env[k]]));
	for (const [k, v] of Object.entries(vars)) v === undefined ? delete process.env[k] : (process.env[k] = v);
	try { return await fn(); } finally {
		for (const [k, v] of Object.entries(saved)) v === undefined ? delete process.env[k] : (process.env[k] = v);
	}
}

function acceptanceFiles() {
	const dir = mkdtempSync(join(tmpdir(), "mediated-src-"));
	const one = join(dir, "test_01_home.py"), two = join(dir, "test_02_board.py");
	writeFileSync(one, "def test_home():\n    assert ORIGINAL_ONE\n");
	writeFileSync(two, "def test_board():\n    assert ORIGINAL_TWO\n");
	return { dir, one, two, env: `${one}${delimiter}${two}` };
}

/** A pytest stand-in (a VERIFY_PYTEST command) speaking the gate's report protocol. By default it
 * fails test_board with a message naming where it ran and every test file it was handed. With
 * `greenWhen`, it passes every test once that file exists in the project. `count` gets a line per call;
 * `infraFirst` answers with no report on that many calls first; `say` is printed like server output. */
function standIn({ greenWhen, count, infraFirst = 0, say = "", message } = {}) {
	const dir = mkdtempSync(join(tmpdir(), "mediated-standin-"));
	const script = join(dir, "pytest.mjs");
	writeFileSync(script, `
import { appendFileSync, existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
const dir = process.argv[2];
const counter = ${JSON.stringify(count ?? null)};
let calls = 0;
if (counter) { appendFileSync(counter, "x\\n"); calls = readFileSync(counter, "utf8").split("\\n").filter(Boolean).length; }
process.stdout.write(${JSON.stringify(say)});
if (calls && calls <= ${infraFirst}) process.exit(0);
const emit = (line) => appendFileSync(process.env.MELLUM_GATE_REPORT, JSON.stringify(line) + "\\n");
const tests = readdirSync(dir).filter((n) => /^test_.*\\.py$/.test(n));
const green = ${JSON.stringify(greenWhen ?? null)} && existsSync(join(process.cwd(), ${JSON.stringify(greenWhen ?? "")}));
if (green) {
	for (const n of tests) for (const m of readFileSync(join(dir, n), "utf8").matchAll(/def (test\\w*)/g)) emit({ event: "outcome", test: n + "::" + m[1], when: "call", outcome: "passed" });
	emit({ event: "finished", exit: 0 });
	process.exit(0);
}
const seen = tests.map((n) => n + ": " + readFileSync(join(dir, n), "utf8")).join(" | ");
emit({ event: "outcome", test: dir + "/test_02_board.py::test_board", when: "call", outcome: "failed", message: String(${JSON.stringify(message ?? null)} ?? ("AssertionError: cwd=" + process.cwd() + " saw " + seen)).replaceAll("MEDIATED_DIR", dir) });
emit({ event: "finished", exit: 1 });
process.exit(1);
`);
	return `"${process.execPath}" ${script}`;
}

const RED = standIn();

test("check/mediated-test installs nothing when no acceptance test is named", async () => {
	const unit = await import("../remedies/check/mediated-test.ts");
	await withEnv({ MELLUM_MEDIATED_TEST: undefined }, async () => {
		const pi = fakePi();
		unit.default(pi);
		assert.deepEqual(pi.names(), []);
	});
});

test("check/mediated-test shows the request's acceptance test once at the start of the task", async () => {
	const unit = await import("../remedies/check/mediated-test.ts");
	const files = acceptanceFiles();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const shown = pi.handlers.before_agent_start[0]({ messageType: "user" });
		assert.match(shown.message.content, /ORIGINAL_ONE/);
		assert.match(shown.message.content, /ORIGINAL_TWO/);
		assert.match(shown.message.content, /cannot change/);
		// A settle re-dispatch continues the same task: the test is not shown again.
		assert.equal(pi.handlers.before_agent_start[0]({ messageType: "custom" }), undefined);
	});
});

test("check/mediated-test sends the model back with the failures, run from a frozen copy outside the project", async () => {
	const unit = await import("../remedies/check/mediated-test.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED }, async () => {
		const pi = fakePi();
		unit.default(pi);
		// The model edits or deletes the test it was shown: the gate still runs the original.
		writeFileSync(files.one, "def test_home():\n    assert True  # weakened\n");
		rmSync(files.two);
		const out = pi.handlers.agent_before_settle[0]({}, { cwd });
		assert.equal(out?.continue, true);
		const text = out.entries[0].content;
		assert.match(text, /test_board/);
		assert.match(text, /ORIGINAL_ONE/);
		assert.match(text, /ORIGINAL_TWO/);
		assert.doesNotMatch(text, /weakened/);
		assert.ok(!text.includes(files.dir), "runs a copy, not the files the model can reach");
		assert.ok(text.includes(cwd), "runs with the project as the working directory");
	});
});

test("check/mediated-test lets a green project settle", async () => {
	const unit = await import("../remedies/check/mediated-test.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: standIn({ greenWhen: "." }) }, async () => {
		const pi = fakePi();
		unit.default(pi);
		assert.equal(pi.handlers.agent_before_settle[0]({}, { cwd }), undefined);
	});
});

test("check/mediated-test sends the model back at most MELLUM_MEDIATED_MAX times", async () => {
	const unit = await import("../remedies/check/mediated-test.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED, MELLUM_MEDIATED_MAX: "2" }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const settle = pi.handlers.agent_before_settle[0];
		assert.equal(settle({}, { cwd })?.continue, true);
		assert.equal(settle({}, { cwd })?.continue, true);
		assert.equal(settle({}, { cwd }), undefined);
	});
});

test("check/mediated-test refuses a named acceptance test that does not exist", async () => {
	const unit = await import("../remedies/check/mediated-test.ts");
	await withEnv({ MELLUM_MEDIATED_TEST: join(tmpdir(), "no-such-acceptance-test.py") }, async () => {
		assert.throws(() => unit.default(fakePi()), /acceptance test/);
	});
});

test("check/mediated-test carries the metadata the remedies list is generated from", async () => {
	const { meta } = await import("../remedies/check/mediated-test.ts");
	for (const key of ["pathology", "does", "lesson", "evidence"]) assert.equal(typeof meta[key], "string");
	for (const key of ["pathology", "does", "evidence"]) assert.ok(meta[key].length > 0, key);
});

test("check/mediated-test-show shows the test and never reruns it at settle", async () => {
	const unit = await import("../remedies/check/mediated-test-show.ts");
	const files = acceptanceFiles();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const shown = pi.handlers.before_agent_start[0]({ messageType: "user" });
		assert.match(shown.message.content, /ORIGINAL_ONE/);
		assert.equal(pi.handlers.agent_before_settle, undefined);
	});
});

test("check/mediated-test-settle never shows the test but sends failures back at settle", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED }, async () => {
		const pi = fakePi();
		unit.default(pi);
		assert.equal(pi.handlers.before_agent_start, undefined);
		const out = pi.handlers.agent_before_settle[0]({}, { cwd });
		assert.equal(out?.continue, true);
		assert.equal(out.entries[0].customType, "mediated-test");
		assert.match(out.entries[0].content, /test_board/);
	});
});

test("check/mediated-test-settle reads the test when it loads, so later edits change nothing", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED }, async () => {
		const pi = fakePi();
		unit.default(pi);
		writeFileSync(files.one, "def test_home():\n    assert True  # weakened\n");
		const text = pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content;
		assert.match(text, /ORIGINAL_ONE/);
		assert.doesNotMatch(text, /weakened/);
	});
});

// Names the copy's location the way pytest does: absolute, relative to the project, and in a node id.
const RED_WITH_PATHS = standIn({ message: "AssertionError at MEDIATED_DIR/test_01_home.py:3 and ../../..MEDIATED_DIR/test_01_home.py:3" });

function alive(pid) {
	try { process.kill(pid, 0); return true; } catch { return false; }
}

async function until(condition, ms = 3000) {
	const end = Date.now() + ms;
	while (Date.now() < end) {
		if (condition()) return true;
		await new Promise((r) => setTimeout(r, 25));
	}
	return condition();
}

function background(env) {
	// Node, not sleep: macOS hides the environment of its own system binaries from `ps`.
	const r = spawnSync("sh", ["-c", `"${process.execPath}" -e 'setTimeout(() => {}, 60000)' >/dev/null 2>&1 & echo $!`], { env, encoding: "utf8" });
	return Number(r.stdout.trim());
}

test("check/mediated-test-settle never tells the model where the copy is, and says it is out of reach", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED_WITH_PATHS }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const text = pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content;
		assert.match(text, /test_board/, "the failing test is still named");
		assert.match(text, /AssertionError/, "the failure is still shown");
		assert.doesNotMatch(text, /mediated-[A-Za-z0-9]{6}\b/);
		assert.match(text, /not in the project/);
	});
});

for (const [label, pytest] of [["red", RED_WITH_PATHS], ["green", standIn({ greenWhen: "." })]]) {
	test(`check/mediated-test-settle leaves no copy behind after a ${label} run`, async () => {
		const unit = await import("../remedies/check/mediated-test-settle.ts");
		const files = acceptanceFiles();
		const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
		const scratch = mkdtempSync(join(tmpdir(), "mediated-scratch-"));
		await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: pytest, TMPDIR: scratch }, async () => {
			const pi = fakePi();
			unit.default(pi);
			pi.handlers.agent_before_settle[0]({}, { cwd });
			assert.deepEqual(readdirSync(scratch), []);
		});
	});
}

test("check/mediated-test-settle stops what this session left running, and only that, before the run", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED, MELLUM_SESSION_PROCESS: undefined }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const session = background(process.env);
		const notSession = { ...process.env };
		delete notSession.MELLUM_SESSION_PROCESS;
		const other = background(notSession);
		try {
			assert.ok(alive(session) && alive(other));
			const text = pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content;
			assert.ok(await until(() => !alive(session)), "the session's background process is gone");
			assert.ok(alive(other), "a process the session did not start is left alone");
			assert.match(text, /stopped/);
		} finally {
			for (const pid of [session, other]) if (alive(pid)) process.kill(pid, "SIGKILL");
		}
	});
});

test("check/mediated-test-settle says nothing about stopping when nothing was running", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED, MELLUM_SESSION_PROCESS: undefined }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const text = pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content;
		assert.doesNotMatch(text, /stopped/);
	});
});

for (const name of ["mediated-test-show", "mediated-test-settle"]) {
	test(`check/${name} installs nothing without a test and carries its metadata`, async () => {
		const unit = await import(`../remedies/check/${name}.ts`);
		await withEnv({ MELLUM_MEDIATED_TEST: undefined }, async () => {
			const pi = fakePi();
			unit.default(pi);
			assert.deepEqual(pi.names(), []);
		});
		for (const key of ["pathology", "does", "evidence"]) assert.ok(unit.meta[key].length > 0, key);
	});
}

// --- F.8: explicit verdicts at settle -----------------------------------------------------------

function gateLog() {
	const path = join(mkdtempSync(join(tmpdir(), "mediated-log-")), "gate.jsonl");
	return { path, read: () => (existsSync(path) ? readFileSync(path, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)) : []) };
}

test("check/mediated-test still checks the last repair after the cap, and it can be green", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	const log = gateLog();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: standIn({ greenWhen: "fixed" }), MELLUM_MEDIATED_MAX: "1", MELLUM_GATE_LOG: log.path }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const settle = pi.handlers.agent_before_settle[0];
		assert.equal(settle({}, { cwd })?.continue, true);
		writeFileSync(join(cwd, "fixed"), "");
		assert.equal(settle({}, { cwd }), undefined);
		assert.deepEqual(log.read().map((r) => r.status), ["red", "green"]);
	});
});

test("check/mediated-test records exhausted when the check is still red at the cap", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	const log = gateLog();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED, MELLUM_MEDIATED_MAX: "1", MELLUM_GATE_LOG: log.path }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const settle = pi.handlers.agent_before_settle[0];
		assert.equal(settle({}, { cwd })?.continue, true);
		assert.equal(settle({}, { cwd }), undefined);
		const records = log.read();
		assert.deepEqual(records.map((r) => r.status), ["red", "exhausted"]);
		assert.deepEqual(records[1].failures, ["test_board"]);
	});
});

test("check/mediated-test retries an infrastructure failure once, silently, without spending a send-back", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	const log = gateLog();
	const count = join(mkdtempSync(join(tmpdir(), "mediated-count-")), "calls");
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: standIn({ count, infraFirst: 2 }), MELLUM_MEDIATED_MAX: "1", MELLUM_GATE_LOG: log.path }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const settle = pi.handlers.agent_before_settle[0];
		assert.equal(settle({}, { cwd }), undefined, "never sent to the model");
		assert.equal(readFileSync(count, "utf8").split("\n").filter(Boolean).length, 2, "one retry");
		assert.equal(settle({}, { cwd })?.continue, true, "the send-back was not spent");
		assert.deepEqual(log.read().map((r) => r.status), ["infrastructure", "red"]);
	});
});

test("check/mediated-test records infrastructure when the check cannot even be prepared", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	const log = gateLog();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: RED, MELLUM_GATE_LOG: log.path }, async () => {
		const pi = fakePi();
		unit.default(pi);
		await withEnv({ TMPDIR: join(tmpdir(), "no-such-dir-for-mediated") }, async () => {
			assert.equal(pi.handlers.agent_before_settle[0]({}, { cwd }), undefined);
		});
		assert.deepEqual(log.read().map((r) => r.status), ["infrastructure"]);
	});
});

test("check/mediated-test takes the gate log path out of the environment", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const log = gateLog();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, MELLUM_GATE_LOG: log.path }, async () => {
		unit.default(fakePi());
		assert.equal(process.env.MELLUM_GATE_LOG, undefined);
	});
});

test("check/mediated-test feedback keeps assertions and drops captured server output", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	const say = "INFO:     Uvicorn running on http://127.0.0.1:8000\n".repeat(50);
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: standIn({ say, message: "AssertionError: expected the Open badge" }) }, async () => {
		const pi = fakePi();
		unit.default(pi);
		const text = pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content;
		assert.match(text, /expected the Open badge/);
		assert.doesNotMatch(text, /Uvicorn/);
	});
});

test("mediated feedback names every failure, caps each message and the whole", async () => {
	const { feedback } = await import("../remedies/mediated-test.ts");
	const failures = Array.from({ length: 10 }, (_, i) => ({ test: `test_${i}`, message: `AssertionError ${i} ` + "x".repeat(1000) }));
	const text = feedback({ status: "red", failures, missing: [], detail: "", execution: "frozen" }, "/tmp/mediated-abc123", 0);
	for (let i = 0; i < 10; i++) assert.match(text, new RegExp(`test_${i}\\b`));
	assert.ok(text.length < 2400, `${text.length} characters`);
	assert.doesNotMatch(text, /x{401}/);
});

test("mediated feedback for a hang says it was stopped, after how long, and what was running", async () => {
	const { feedback } = await import("../remedies/mediated-test.ts");
	const text = feedback({ status: "red", failures: [], missing: [], detail: "timed out", timedOutSeconds: 150, running: "test_board", execution: "frozen" }, "/tmp/mediated-abc123", 0);
	assert.match(text, /stopped after 150 s/);
	assert.match(text, /test_board/);
});

// --- F.8: the handover leaves nothing behind ------------------------------------------------------

const CACHE = Symbol.for("mellum.mediated");

test("check/mediated-test removes handed tests and their path before any tool runs", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	try {
		await withEnv({ MELLUM_MEDIATED_TEST: files.env, MELLUM_MEDIATED_HANDED: "1", VERIFY_PYTEST: RED }, async () => {
			const pi = fakePi();
			unit.default(pi);
			assert.equal(existsSync(files.one) || existsSync(files.two), false, "the copies are gone");
			assert.equal(existsSync(files.dir), false, "so is their directory");
			assert.equal(process.env.MELLUM_MEDIATED_TEST, undefined);
			assert.equal(process.env.MELLUM_MEDIATED_HANDED, undefined);
			const text = pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content;
			assert.match(text, /ORIGINAL_ONE/, "the gate still runs what was handed");
		});
	} finally {
		delete globalThis[CACHE];
	}
});

test("check/mediated-test never deletes a test the user named themselves", async () => {
	const unit = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, MELLUM_MEDIATED_HANDED: undefined }, async () => {
		unit.default(fakePi());
		assert.ok(existsSync(files.one) && existsSync(files.two));
		assert.equal(process.env.MELLUM_MEDIATED_TEST, files.env);
	});
});

test("check/mediated-test-show and -settle loaded as two units both get the handed tests", async () => {
	const show = await import("../remedies/check/mediated-test-show.ts");
	const settle = await import("../remedies/check/mediated-test-settle.ts");
	const files = acceptanceFiles();
	const cwd = mkdtempSync(join(tmpdir(), "mediated-ws-"));
	try {
		await withEnv({ MELLUM_MEDIATED_TEST: files.env, MELLUM_MEDIATED_HANDED: "1", VERIFY_PYTEST: RED }, async () => {
			const pi = fakePi();
			show.default(pi);
			settle.default(pi);
			assert.match(pi.handlers.before_agent_start[0]({ messageType: "user" }).message.content, /ORIGINAL_TWO/);
			assert.match(pi.handlers.agent_before_settle[0]({}, { cwd }).entries[0].content, /ORIGINAL_TWO/);
		});
	} finally {
		delete globalThis[CACHE];
	}
});

test("mediated feedback for a collection error keeps its final error line", async () => {
	const { feedback } = await import("../remedies/mediated-test.ts");
	const message = "ImportError while importing test module.\nTraceback:\n" + "  File \"app.py\", line 3, in <module>\n".repeat(30) + "E   ModuleNotFoundError: No module named 'models'";
	const text = feedback({ status: "red", failures: [{ test: "collection", message }], missing: [], detail: "", execution: "frozen" }, "/tmp/mediated-abc123", 0);
	assert.match(text, /No module named 'models'/);
});
