import assert from "node:assert/strict";
import test from "node:test";

import { PLAN_REASON, createPlanGate, isTodoPath, resolvePlanMax } from "../extensions/mellum-plan.ts";

test("isTodoPath recognises the plan file anywhere, not source files", () => {
	assert.equal(isTodoPath("TODO.md"), true);
	assert.equal(isTodoPath("./TODO.md"), true);
	assert.equal(isTodoPath("sub/dir/TODO.md"), true);
	assert.equal(isTodoPath("todo.md"), true);
	assert.equal(isTodoPath("app.py"), false);
	assert.equal(isTodoPath("models.py"), false);
});

test("read/grep/ls/bash/find are never gated — exploration is fine", () => {
	const gate = createPlanGate(2, () => false);
	for (const toolName of ["read", "grep", "ls", "find", "bash"]) {
		assert.equal(gate.toolCall({ toolName, input: { path: "app.py" } }), undefined, toolName);
	}
});

test("a source edit/write is blocked until a TODO.md exists", () => {
	const gate = createPlanGate(2, () => false); // no TODO.md yet
	const decision = gate.toolCall({ toolName: "write", input: { path: "app.py", content: "x" } });
	assert.ok(decision?.block, "source write with no plan is blocked");
	assert.match(decision.reason, /TODO\.md/);
});

test("writing the TODO.md itself is always allowed (that is how the plan gets made)", () => {
	const gate = createPlanGate(2, () => false);
	assert.equal(gate.toolCall({ toolName: "write", input: { path: "TODO.md", content: "- [ ] step" } }), undefined);
	assert.equal(gate.toolCall({ toolName: "edit", input: { path: "TODO.md" } }), undefined);
});

test("once a TODO.md exists, source edits are allowed (follow the plan)", () => {
	let has = false;
	const gate = createPlanGate(2, () => has);
	assert.ok(gate.toolCall({ toolName: "write", input: { path: "app.py", content: "x" } })?.block, "blocked before plan");
	has = true; // the worker wrote TODO.md
	assert.equal(gate.toolCall({ toolName: "write", input: { path: "app.py", content: "x" } }), undefined, "allowed after plan");
});

test("the gate fails open after max blocks — it never deadlocks", () => {
	const gate = createPlanGate(2, () => false);
	assert.ok(gate.toolCall({ toolName: "write", input: { path: "a.py" } })?.block, "1st blocked");
	assert.ok(gate.toolCall({ toolName: "write", input: { path: "b.py" } })?.block, "2nd blocked");
	assert.equal(gate.toolCall({ toolName: "write", input: { path: "c.py" } }), undefined, "3rd allowed — fail open");
});

test("PLAN_REASON encodes the loop: gather -> plan -> follow+check off -> test -> on fail re-plan -> until pass", () => {
	assert.match(PLAN_REASON, /gather|read the spec/i);
	assert.match(PLAN_REASON, /TODO\.md/);
	assert.match(PLAN_REASON, /follow/i);
	assert.match(PLAN_REASON, /every requirement|checklist|each route/i);
	assert.match(PLAN_REASON, /check(ed)? (it )?off/i);
	assert.match(PLAN_REASON, /fail|still failing/i);
	assert.match(PLAN_REASON, /until .*(pass|done|checked)/i);
});

test("resolvePlanMax reads MELLUM_PLAN, defaults, tolerates junk", () => {
	assert.equal(resolvePlanMax(undefined), 2);
	assert.equal(resolvePlanMax('{"max":1}'), 1);
	assert.equal(resolvePlanMax("nope"), 2);
});

test("the default export wires tool_call and gates on a TODO.md in cwd", async () => {
	const { default: install } = await import("../extensions/mellum-plan.ts");
	const handlers = {};
	install({ on: (name, fn) => { handlers[name] = fn; } }, { hasTodo: () => false });
	assert.ok(handlers.tool_call, "registers tool_call");
	assert.ok(handlers.tool_call({ toolName: "write", input: { path: "app.py" } })?.block);
	assert.equal(handlers.tool_call({ toolName: "write", input: { path: "TODO.md" } }), undefined);
});
