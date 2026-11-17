import assert from "node:assert/strict";
import test from "node:test";

import { WORKFLOWS, nextStep, workflowExtensions } from "../extensions/mellum-loop.ts";

test("happy path: plan -> plan_review -> code -> code_review -> test -> done", () => {
	let s = nextStep({ workflow: "start", round: 0 });
	assert.deepEqual(s, { workflow: "planning", round: 0 });
	s = nextStep(s);
	assert.deepEqual(s, { workflow: "plan_review", round: 0 });
	s = nextStep({ workflow: "plan_review", round: 0, passed: true });
	assert.deepEqual(s, { workflow: "coding", round: 0 });
	s = nextStep(s);
	assert.deepEqual(s, { workflow: "code_review", round: 0 });
	s = nextStep({ workflow: "code_review", round: 0, passed: true });
	assert.deepEqual(s, { workflow: "testing", round: 0 });
	s = nextStep({ workflow: "testing", round: 0, passed: true }, { maxRounds: 5 });
	assert.deepEqual(s, { workflow: "done", round: 0 });
});

test("a complicated plan goes back to planning", () => {
	assert.deepEqual(nextStep({ workflow: "plan_review", round: 0, passed: false }, { maxRounds: 5 }), { workflow: "planning", round: 1 });
});

test("code review failing goes back to coding (not planning)", () => {
	assert.deepEqual(nextStep({ workflow: "code_review", round: 0, passed: false }, { maxRounds: 5 }), { workflow: "coding", round: 1 });
});

test("a broken test goes back to CODING, not planning", () => {
	assert.deepEqual(nextStep({ workflow: "testing", round: 0, passed: false }, { maxRounds: 5 }), { workflow: "coding", round: 1 });
});

test("a REPEATED broken test rubber-ducks first, then back to coding", () => {
	assert.deepEqual(nextStep({ workflow: "testing", round: 1, passed: false }, { maxRounds: 5 }), { workflow: "rubberduck", round: 2 });
	assert.deepEqual(nextStep({ workflow: "rubberduck", round: 2 }), { workflow: "coding", round: 2 });
});

test("every gate respects the round budget", () => {
	for (const wf of ["plan_review", "code_review", "testing"]) {
		assert.deepEqual(nextStep({ workflow: wf, round: 5, passed: false }, { maxRounds: 5 }), { workflow: "done", round: 5 });
	}
});

test("extensions: only coding carries the guards", () => {
	assert.deepEqual(workflowExtensions("planning"), []);
	assert.deepEqual(workflowExtensions("plan_review"), []);
	const coding = workflowExtensions("coding");
	assert.ok(coding.includes("mellum-guards") && coding.includes("mellum-surgical"), coding);
	assert.deepEqual(workflowExtensions("code_review"), []);
	assert.deepEqual(workflowExtensions("testing"), []);
});

test("WORKFLOWS lists the five main nodes in order", () => {
	assert.deepEqual(WORKFLOWS, ["planning", "plan_review", "coding", "code_review", "testing"]);
});
