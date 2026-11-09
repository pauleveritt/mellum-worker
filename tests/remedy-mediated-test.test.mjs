import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
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

// The pytest stand-in prints the files it was handed (a directory) and where it ran, then fails.
const RED = "sh -c 'pwd; ls \"$1\"; cat \"$1\"/*.py; echo FAILED x.py::test_board - nope; exit 1' sh";

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
	await withEnv({ MELLUM_MEDIATED_TEST: files.env, VERIFY_PYTEST: "sh -c 'echo 2 passed; exit 0' sh" }, async () => {
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

// Prints the copy's location the way pytest does: absolute, relative to the project, and on a FAILED line.
const RED_WITH_PATHS = "sh -c 'mkdir \"$1/__pycache__\"; echo \"$1/test_01_home.py:3: in test_board\"; echo \"../../..$1/test_01_home.py:3: AssertionError\"; echo \"FAILED ../..$1/test_01_home.py::test_board - nope\"; exit 1' sh";

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

for (const [label, pytest] of [["red", RED_WITH_PATHS], ["green", "sh -c 'mkdir \"$1/__pycache__\"; exit 0' sh"]]) {
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
