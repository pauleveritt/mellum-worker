import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
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
