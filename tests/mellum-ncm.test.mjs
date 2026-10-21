import { test } from "node:test";
import assert from "node:assert/strict";

import { parsePytest, gateMessage } from "../extensions/mellum-ncm.ts";

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
