import { test } from "node:test";
import assert from "node:assert/strict";

import { feedLine, turnFields } from "../extensions/mellum-feed.ts";

test("feedLine: NDJSON with t, kind, and the extra fields", () => {
	const line = feedLine("tool", { name: "edit" });
	assert.ok(line.endsWith("\n"));
	const o = JSON.parse(line);
	assert.equal(o.kind, "tool");
	assert.equal(o.name, "edit");
	assert.equal(typeof o.t, "number");
});

test("turnFields: pulls the thinking text and the tool call from an assistant turn", () => {
	const message = {
		role: "assistant",
		content: [
			{ type: "text", text: "We need to add the id field." },
			{ type: "toolCall", name: "edit", arguments: { path: "models.py" } },
		],
	};
	const { think, call } = turnFields(message);
	assert.match(think, /add the id field/);
	assert.match(call, /^edit\(/);
});

test("turnFields: empty turn yields empty fields", () => {
	const { think, call } = turnFields({ role: "assistant", content: [] });
	assert.equal(think, "");
	assert.equal(call, "");
});


test("promptFields: extracts the system prompt and the latest task/injected message", async () => {
	const { promptFields } = await import("../extensions/mellum-feed.ts");
	const messages = [
		{ role: "system", content: "You make one failing test pass." },
		{ role: "user", content: "Make tests/test_phase4.py pass." },
		{ role: "custom", content: [{ type: "text", text: "[mellum-ncm] unmet concepts: test_ids" }] },
	];
	const { system, task } = promptFields(messages);
	assert.match(system, /failing test pass/);
	assert.match(task, /unmet concepts: test_ids/);
});
