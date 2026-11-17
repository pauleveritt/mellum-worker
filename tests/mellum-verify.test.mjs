import { test } from "node:test";
import assert from "node:assert/strict";

import { parsePytest, gateMessage, verifyCommand, verifyEnv, gateConfig } from "../extensions/mellum-verify.ts";

test("parsePytest: exit 0 is passed, no unmet concepts", () => {
	const v = parsePytest(0, "2 passed in 0.12s");
	assert.equal(v.passed, true);
	assert.deepEqual(v.failures, []);
});

test("parsePytest: failing test functions are the unmet concepts", () => {
	const out = [
		"FAILED tests/test_phase4.py::test_new_complaints_get_distinct_ids - AssertionError",
		"FAILED tests/test_phase4.py::test_resolve_and_reopen_redirect_303 - assert 404 == 303",
		"1 passed, 2 failed in 0.3s",
	].join("\n");
	const v = parsePytest(1, out);
	assert.equal(v.passed, false);
	assert.deepEqual(v.failures, [
		"test_new_complaints_get_distinct_ids",
		"test_resolve_and_reopen_redirect_303",
	]);
});

test("gateMessage: names the unmet concepts, says not done, carries the tail", () => {
	const msg = gateMessage({ passed: false, failures: ["test_a", "test_b"], output: "TRACEBACK boom" });
	assert.match(msg, /not done/i);
	assert.match(msg, /test_a, test_b/);
	assert.match(msg, /boom/);
});

test("gateMessage: says the test is held out, so the worker fixes behaviour instead of hunting the file", () => {
	// The gated one-pass run (2026-11-08): handed two failing acceptance-test NAMES, the worker
	// went looking for the test file (`find / -name test_medium.py`) because the file is external
	// and not in its workspace — and crawled to the stall. The message must say: do not search for
	// it; each name is a behaviour to satisfy; check with your own in-workspace tests.
	const msg = gateMessage({ passed: false, failures: ["test_a"], output: "boom" });
	assert.match(msg, /held out|not .*in your workspace/i);
	assert.match(msg, /do not (search|look) for/i);
	assert.match(msg, /your own tests/i);
});

test("verifyCommand: a named test runs just that file; empty runs the whole suite", () => {
	const named = verifyCommand("tests/test_phase4.py", "uv run pytest");
	assert.match(named, /uv run pytest/);
	assert.match(named, /tests\/test_phase4\.py/);
	const all = verifyCommand("", "uv run pytest");
	assert.match(all, /uv run pytest/);
	assert.doesNotMatch(all, /test_phase4/);
	// the whole-suite command carries no file-path token between pytest and its flags
	assert.ok(!/pytest\s+\S*\.py/.test(all), "no file path in the whole-suite command");
});

test("gateConfig reads VERIFY_TEST at call time, so acceptance's late session_start set is seen (not inert)", () => {
	// The inert-gate pathology: the gate read VERIFY_TEST once at load, before acceptance's
	// session_start set it, so the gate never fired. gateConfig must read it per call.
	const prev = process.env.VERIFY_TEST;
	delete process.env.VERIFY_TEST;
	assert.equal(gateConfig().test, "", "empty at load, before acceptance runs");
	process.env.VERIFY_TEST = "/w/contract/test_contract.py"; // acceptance sets it at session_start
	assert.equal(gateConfig().test, "/w/contract/test_contract.py", "seen at settle time");
	if (prev === undefined) delete process.env.VERIFY_TEST;
	else process.env.VERIFY_TEST = prev;
});

test("verifyEnv: worker cwd on PYTHONPATH, VIRTUAL_ENV stripped (so a held-out contract can import the app)", () => {
	// Without this the gate hits ModuleNotFoundError: app, errors at collection,
	// and never redispatches — the inert-gate pathology. Mirrors harness grade_env.
	const prev = process.env.VIRTUAL_ENV;
	process.env.VIRTUAL_ENV = "/some/venv";
	try {
		const env = verifyEnv("/work/space");
		assert.equal(env.PYTHONPATH, "/work/space");
		assert.ok(!("VIRTUAL_ENV" in env), "VIRTUAL_ENV must be stripped");
	} finally {
		if (prev === undefined) delete process.env.VIRTUAL_ENV;
		else process.env.VIRTUAL_ENV = prev;
	}
});

// ---- Gate-runner fixes (2026-11-13, from Paul's handover proposals 17 and 18) ----
// Real pytest in throwaway directories, no mocks. Each test names the bug it pins.
import { mkdtempSync, writeFileSync, mkdirSync, realpathSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runTest } from "../extensions/mellum-verify.ts";
import verify from "../extensions/mellum-verify.ts";

const PYTEST = "uv run --with pytest python -m pytest";
const scratch = (files) => {
	const dir = realpathSync(mkdtempSync(join(tmpdir(), "verify-")));
	for (const [name, body] of Object.entries(files)) {
		mkdirSync(join(dir, name, ".."), { recursive: true });
		writeFileSync(join(dir, name), body);
	}
	return dir;
};

test("runTest: a held-out test that passes reads green", () => {
	const held = scratch({ "contract/test_contract.py": "def test_a():\n    assert True\n\ndef test_b():\n    assert True\n" });
	const ws = scratch({ "app.py": "x = 1\n" });
	assert.equal(runTest(join(held, "contract/test_contract.py"), PYTEST, ws).passed, true);
});

test("bug 1: a hung test is stopped at the timeout and reads red, instead of holding settle", () => {
	const held = scratch({ "test_hang.py": "import time\n\ndef test_hang():\n    time.sleep(120)\n" });
	const ws = scratch({ "app.py": "" });
	const t0 = Date.now();
	const v = runTest(join(held, "test_hang.py"), PYTEST, ws, 8000);
	assert.equal(v.passed, false);
	assert.match(v.output, /timed out/);
	assert.ok(Date.now() - t0 < 30000, "returned near the timeout, not after the sleep");
});

test("bug 3: exit 0 is not evidence - a workspace conftest that skips every test reads red", () => {
	// The ladder copies the acceptance test INTO the workspace (run_ladder.py:532-534), so the
	// workspace's own conftest is collected with it and can skip it into an exit 0.
	const ws = scratch({
		"tests/test_contract.py": "def test_a():\n    assert False\n",
		"conftest.py":
			"import pytest\n\ndef pytest_collection_modifyitems(config, items):\n    for i in items:\n        i.add_marker(pytest.mark.skip(reason='x'))\n",
	});
	const v = runTest("tests/test_contract.py", PYTEST, ws);
	assert.equal(v.passed, false, "a skipped acceptance test never passed");
	assert.deepEqual(v.failures, ["test_a"], "the test with no pass is named as unmet");
});

test("bug 3: PYTEST_ADDOPTS from the environment cannot deselect the acceptance test", () => {
	const prev = process.env.PYTEST_ADDOPTS;
	process.env.PYTEST_ADDOPTS = "-k nothing_matches";
	try {
		assert.ok(!("PYTEST_ADDOPTS" in verifyEnv("/w")));
	} finally {
		if (prev === undefined) delete process.env.PYTEST_ADDOPTS;
		else process.env.PYTEST_ADDOPTS = prev;
	}
});

test("bug 2: the gate keeps an earlier settle handler's entries (Pi keeps the last handler's)", async () => {
	const held = scratch({ "test_contract.py": "def test_a():\n    assert False\n" });
	const ws = scratch({ "app.py": "" });
	const prev = { t: process.env.VERIFY_TEST, p: process.env.VERIFY_PYTEST };
	process.env.VERIFY_TEST = join(held, "test_contract.py");
	process.env.VERIFY_PYTEST = PYTEST;
	try {
		let handler;
		verify({ on: (_e, h) => { handler = h; } });
		const earlier = { type: "custom_message", customType: "mellum-quality", content: "lint red", display: true };
		const r = await handler({ type: "agent_before_settle", entries: [earlier], continue: true }, { cwd: ws });
		assert.deepEqual(r.entries.map((e) => e.customType), ["mellum-quality", "mellum-verify"]);
	} finally {
		for (const [k, v] of [["VERIFY_TEST", prev.t], ["VERIFY_PYTEST", prev.p]]) {
			if (v === undefined) delete process.env[k];
			else process.env[k] = v;
		}
	}
});

test("18: the gate message never names where the held-out test lives", () => {
	const held = scratch({ "contract/test_contract.py": "def test_ids_distinct():\n    assert 1 == 2\n" });
	const ws = scratch({ "app.py": "" });
	const path = join(held, "contract/test_contract.py");
	const msg = gateMessage(runTest(path, PYTEST, ws));
	assert.match(msg, /test_ids_distinct/, "the unmet concept is still named");
	assert.ok(!msg.includes(held), "no directory of the held-out test");
	assert.ok(!msg.includes("test_contract.py"), "no file name of the held-out test");
});

test("gateMessage: carries each failing test's reason, not just the -rA summary tail", () => {
	// The gated screen with the extended test (2026-11-13): with `-rA`, the last 1,200 chars of
	// output were only PASSED/FAILED lines, so the worker got test NAMES and never WHY any failed.
	// It reran its own green tests and settled; five rounds closed nothing. Each failing test's
	// `E` lines must reach the worker, however long the summary below them is.
	const summary = Array.from({ length: 60 }, (_, i) => `PASSED t.py::test_ok_${i}`).join("\n");
	const out = [
		"FF",
		"=================================== FAILURES ===================================",
		"____________________________ test_ids_distinct ____________________________",
		"t.py:3: in test_ids_distinct",
		"    assert ids == [0, 1]",
		"E   AssertionError: one increasing id sequence: [5, 0]",
		"____________________________ test_status_open ____________________________",
		"E   assert 'resolved' == 'open'",
		"=========================== short test summary info ============================",
		summary,
		"FAILED t.py::test_ids_distinct - AssertionError",
		"FAILED t.py::test_status_open - assert",
		"2 failed, 60 passed in 0.2s",
	].join("\n");
	const msg = gateMessage({ passed: false, failures: ["test_ids_distinct", "test_status_open"], output: out });
	assert.match(msg, /test_ids_distinct[\s\S]*one increasing id sequence: \[5, 0\]/);
	assert.match(msg, /test_status_open[\s\S]*'resolved' == 'open'/);
	assert.ok(!msg.includes("PASSED t.py::test_ok_0"), "no wall of PASSED lines");
});

test("gateMessage: a failing test's reason is capped, so one huge diff can't crowd out the rest", () => {
	const big = Array.from({ length: 200 }, (_, i) => `E   line ${i} ${"x".repeat(80)}`).join("\n");
	const out = `____ test_a ____\n${big}\n____ test_b ____\nE   reason_b\n=== short test summary info ===\nFAILED t.py::test_a\nFAILED t.py::test_b`;
	const msg = gateMessage({ passed: false, failures: ["test_a", "test_b"], output: out });
	assert.match(msg, /reason_b/);
	assert.ok(msg.length < 4000, `message stays bounded (${msg.length})`);
});

test("gateMessage: real pytest output carries the assertion reason (through runTest)", () => {
	// Forty passing tests push the -rA summary past the old 1,200-char tail, as test_medium did.
	const passing = Array.from({ length: 40 }, (_, i) => `def test_ok_${i}():\n    assert True\n`).join("\n");
	const held = scratch({ "contract/test_contract.py": `${passing}\ndef test_ids_distinct():\n    assert [5, 0] == [0, 1], 'one increasing id sequence'\n` });
	const ws = scratch({ "app.py": "" });
	const msg = gateMessage(runTest(join(held, "contract/test_contract.py"), PYTEST, ws));
	assert.match(msg, /test_ids_distinct[\s\S]*one increasing id sequence/);
});

test("18: a reason never leaks the held-out module name (an object repr), and test names survive", () => {
	const held = scratch({ "contract/test_ids.py": "class Tree: pass\n\ndef test_ids_distinct():\n    assert Tree() is None\n" });
	const ws = scratch({ "app.py": "" });
	const msg = gateMessage(runTest(join(held, "contract/test_ids.py"), PYTEST, ws));
	assert.match(msg, /test_ids_distinct/, "a concept sharing the module's prefix is still named");
	assert.ok(!/test_ids\.Tree/.test(msg), "no module name in an object repr");
});
