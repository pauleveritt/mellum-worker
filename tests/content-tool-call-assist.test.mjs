import assert from "node:assert/strict";
import test from "node:test";

import { coerceToolCall, parseXmlToolCall, parseContentToolCall } from "../extensions/content-tool-call-assist/parse.ts";

// The tools a small model is driving, as a name -> ordered parameter-name map (declaration order).
// This is what lets us normalise a POSITIONAL list of args onto named arguments.
const TOOLS = new Map([
	["write", ["path", "content"]],
	["bash", ["command"]],
	["read", ["path"]],
]);

test("coerceToolCall keeps a well-formed named-args object", () => {
	const call = coerceToolCall({ tool: "write", args: { path: "a.py", content: "x" } }, TOOLS);
	assert.deepEqual(call, { name: "write", arguments: { path: "a.py", content: "x" } });
});

test("coerceToolCall maps a POSITIONAL list onto the tool's parameter order", () => {
	// the live 1.5B failure: it emits {"tool":"write","args":["a.py","hi"]} — a list, which oMLX
	// then rejects with 422 'arguments must be a JSON object, got list'. Map it to named args.
	const call = coerceToolCall({ tool: "write", args: ["a.py", "print(1)"] }, TOOLS);
	assert.deepEqual(call, { name: "write", arguments: { path: "a.py", content: "print(1)" } });
	// a single-parameter tool from a one-element list
	assert.deepEqual(coerceToolCall({ name: "bash", arguments: ["ls -la"] }, TOOLS),
		{ name: "bash", arguments: { command: "ls -la" } });
});

test("coerceToolCall rejects a list it cannot safely map (more args than parameters)", () => {
	// too many positional values for the tool's parameters -> don't guess, force a retry
	assert.equal(coerceToolCall({ tool: "bash", args: ["ls", "extra", "more"] }, TOOLS), undefined);
});

test("coerceToolCall needs a list when param names are unknown", () => {
	// without a tool map we cannot name positional args, so a list is not promotable
	assert.equal(coerceToolCall({ tool: "write", args: ["a.py", "x"] }), undefined);
});

test("coerceToolCall rejects data and scalars", () => {
	assert.equal(coerceToolCall({ name: "Widget A", priceCents: 500 }, TOOLS), undefined); // no args key -> data
	assert.equal(coerceToolCall({ tool: "write", args: "a.py" }, TOOLS), undefined);        // bare scalar
	assert.equal(coerceToolCall({ tool: "nope", args: {} }, TOOLS), undefined);             // unknown tool
});

test("parseXmlToolCall converts Hermes/Qwen XML into a named-args JSON object", () => {
	const xml = "<tool_call><function=write>\n<parameter=path>a.py</parameter>\n<parameter=content>print(1)</parameter>\n</function></tool_call>";
	assert.deepEqual(parseXmlToolCall(xml, TOOLS), { name: "write", arguments: { path: "a.py", content: "print(1)" } });
});

test("parseContentToolCall promotes a fenced-JSON list-args call (end to end)", () => {
	const content = "Sure.\n```json\n{\"tool\":\"write\",\"args\":[\"a.py\",\"print(1)\"]}\n```";
	assert.deepEqual(parseContentToolCall(content, TOOLS),
		{ name: "write", arguments: { path: "a.py", content: "print(1)" } });
});

test("parseContentToolCall promotes a Hermes-XML call from content", () => {
	const content = "<tool_call><function=bash><parameter=command>pytest -q</parameter></function></tool_call>";
	assert.deepEqual(parseContentToolCall(content, TOOLS), { name: "bash", arguments: { command: "pytest -q" } });
});

test("parseContentToolCall ignores a call restated inside <think> and takes the real one", () => {
	const content = "<think>maybe {\"tool\":\"read\",\"args\":[\"wrong.py\"]}</think>\n```json\n{\"tool\":\"write\",\"args\":[\"a.py\",\"x\"]}\n```";
	assert.deepEqual(parseContentToolCall(content, TOOLS),
		{ name: "write", arguments: { path: "a.py", content: "x" } });
});
