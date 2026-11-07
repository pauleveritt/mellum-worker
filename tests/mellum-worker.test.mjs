import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { filterForMellum, withFacts, MARK_ON, MARK_OFF, BOOTSTRAP_MARKER } from "../extensions/mellum-worker.ts";

const text = (role, t) => ({ role, content: [{ type: "text", text: t }] });

test("after the on-marker: system replaced, earlier history and the bootstrap dropped, reasoning kept", () => {
	const payload = {
		model: "x",
		messages: [
			{ role: "system", content: "pi base prompt + skills catalog" },
			text("user", `${BOOTSTRAP_MARKER} ... superpowers`),
			text("user", "parent task"),
			{ role: "assistant", content: "parent answer", reasoning_content: "parent thoughts" },
			text("user", MARK_ON),
			text("user", "fix the cart total"),
			{ role: "assistant", content: "", reasoning_content: "mine", tool_calls: [{ id: "1" }] },
			{ role: "tool", tool_call_id: "1", content: "r" },
		],
	};
	const out = filterForMellum(payload, "v5 prompt");
	assert.equal(out.messages[0].role, "system");
	assert.equal(out.messages[0].content, "v5 prompt");
	assert.deepEqual(out.messages.slice(1).map(m => m.role), ["user", "assistant", "tool"]);
	assert.equal(out.messages[1].content[0].text, "fix the cart total");
	assert.equal(out.messages[2].reasoning_content, "mine", "own thinking stays (A12)");
	assert.equal(payload.messages.length, 8, "input not mutated");
});

test("stripThinking removes earlier reasoning and nothing else", () => {
	const payload = {
		model: "x",
		messages: [
			{ role: "system", content: "pi base prompt" },
			text("user", MARK_ON),
			text("user", "fix the cart total"),
			{ role: "assistant", content: "", reasoning_content: "mine", tool_calls: [{ id: "1" }] },
			{ role: "tool", tool_call_id: "1", content: "r" },
			{ role: "assistant", content: "done", reasoning: "provider-style thinking" },
		],
	};
	const kept = filterForMellum(payload, "v5");
	const stripped = filterForMellum(payload, "v5", { stripThinking: true });
	assert.equal(kept.messages[2].reasoning_content, "mine", "off by default (A12)");
	assert.equal(stripped.messages[2].reasoning_content, undefined, "reasoning_content dropped");
	assert.equal(stripped.messages[2].content, "", "content untouched");
	assert.deepEqual(stripped.messages[2].tool_calls, [{ id: "1" }], "tool calls untouched");
	assert.equal(stripped.messages[3].content, "r", "tool messages untouched");
	assert.equal(stripped.messages[4].reasoning, undefined, "a reasoning field is dropped too");
	assert.equal(stripped.messages[4].content, "done");
	assert.equal(stripped.messages[1].content[0].text, "fix the cart total");
	assert.equal(payload.messages[3].reasoning_content, "mine", "input not mutated");
});

test("keepSystem leaves Pi's system message in place, and the thin worker leaves the tools alone", () => {
	const payload = {
		messages: [{ role: "system", content: "pi base prompt" }, text("user", "task")],
		tools: [{ type: "function", function: { name: "read" } }, { type: "function", function: { name: "subagent" } }],
	};
	const out = filterForMellum(payload, "v5", { keepSystem: true });
	assert.equal(out.messages[0].role, "system");
	assert.equal(out.messages[0].content, "pi base prompt");
	// Tool-narrowing is context/narrow-tools now; filterForMellum passes the tools through.
	assert.deepEqual(out.tools.map((t) => t.function.name), ["read", "subagent"]);
});

test("without an on-marker (headless activation) only the bootstrap is dropped", () => {
	const payload = { messages: [{ role: "system", content: "base" }, text("user", `${BOOTSTRAP_MARKER} x`), text("user", "task")] };
	const out = filterForMellum(payload, "v5");
	assert.deepEqual(out.messages.map(m => m.role), ["system", "user"]);
	assert.equal(out.messages[1].content[0].text, "task");
});

test("a prompt queued just before the on-marker is kept, and marker messages never reach the model", () => {
	const payload = {
		messages: [
			{ role: "system", content: "base" },
			text("user", "fix the cart total"),
			text("user", MARK_ON),
		],
		tools: [{ type: "function", function: { name: "read" } }, { type: "function", function: { name: "subagent" } }],
	};
	const out = filterForMellum(payload, "v5");
	assert.deepEqual(out.messages.map(m => m.role), ["system", "user"]);
	assert.equal(out.messages[1].content[0].text, "fix the cart total");
	assert.ok(!JSON.stringify(out.messages).includes(MARK_ON));
	assert.deepEqual(out.tools.map(t => t.function.name), ["read", "subagent"], "the thin worker leaves tool-narrowing to context/narrow-tools");
});

test("a developer-role instruction message is replaced too, and the thin worker leaves tools and tool_choice to the unit", () => {
	const payload = {
		messages: [{ role: "developer", content: "pi base" }, text("user", "task")],
		tools: [{ type: "function", function: { name: "subagent" } }],
		tool_choice: { type: "function", function: { name: "subagent" } },
	};
	const out = filterForMellum(payload, "v5");
	assert.deepEqual(out.messages.map(m => m.role), ["system", "user"]);
	// filterForMellum no longer touches tools/tool_choice; context/narrow-tools does.
	assert.deepEqual(out.tools.map(t => t.function.name), ["subagent"]);
	assert.deepEqual(out.tool_choice, { type: "function", function: { name: "subagent" } });
});

test("markers between the prompt and the on-marker are skipped: [prompt, OFF, ON] keeps the prompt", () => {
	const payload = { messages: [{ role: "system", content: "base" }, text("user", "task"), text("user", MARK_OFF), text("user", MARK_ON)] };
	const out = filterForMellum(payload, "v5");
	assert.deepEqual(out.messages.map(m => m.role), ["system", "user"]);
	assert.equal(out.messages[1].content[0].text, "task");
});

test("a missing marker while interactively active is reported, not silently widened", () => {
	const payload = { messages: [{ role: "system", content: "base" }, text("user", "old parent turn"), text("user", "task")] };
	const out = filterForMellum(payload, "v5", { expectMarker: true });
	assert.equal(out.messages.length, 2, "only the system prompt and the last user message survive");
	assert.equal(out.messages[1].content[0].text, "task");
	assert.equal(out.mellumModeMarkerMissing, true);
});

test("after /mellum off, the parent sees one handoff block in place of the mode's turns", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const msgs = [
		text("user", "earlier parent turn"),
		{ role: "assistant", content: [{ type: "text", text: "parent reply" }] },
		text("user", "fix the cart total"),
		text("user", MARK_ON),
		{ role: "assistant", content: [{ type: "thinking", thinking: "..." }, { type: "toolCall", id: "1", name: "read", arguments: { path: "calculator.js" } }] },
		{ role: "toolResult", toolCallId: "1", toolName: "read", content: [{ type: "text", text: "export function total() {}" }] },
		{ role: "assistant", content: [{ type: "toolCall", id: "2", name: "edit", arguments: { path: "calculator.js", edits: [] } }] },
		{ role: "toolResult", toolCallId: "2", toolName: "edit", content: [{ type: "text", text: "Successfully replaced 1 block(s)" }] },
		{ role: "assistant", content: [{ type: "toolCall", id: "3", name: "bash", arguments: { command: "node --test calculator.test.js" } }] },
		{ role: "toolResult", toolCallId: "3", toolName: "bash", content: [{ type: "text", text: "ℹ pass 3\nℹ fail 0" }] },
		{ role: "assistant", content: [{ type: "text", text: "Files changed: calculator.js. Tests pass." }] },
		text("user", MARK_OFF),
		text("user", "thanks, now the docs"),
	];
	const out = collapseHandoffs(msgs);
	assert.deepEqual(out.map(m => m.role), ["user", "assistant", "user", "user"]);
	const handoff = out[2].content[0].text;
	assert.match(handoff, /\[mellum-worker handoff\]/);
	assert.match(handoff, /fix the cart total/);
	assert.match(handoff, /calculator\.js/);
	assert.match(handoff, /pass 3/);
	assert.match(handoff, /Tests pass\./);
	assert.ok(!handoff.includes("export function total"), "tool results are summarised, not replayed");
	assert.equal(out[3].content[0].text, "thanks, now the docs");
	assert.equal(msgs.length, 13, "input not mutated");
});

test("an open span (mode still on) is left alone by the collapse", async () => {
	const { collapseHandoffs } = await import("../extensions/mellum-worker.ts");
	const msgs = [text("user", "task"), text("user", MARK_ON), { role: "assistant", content: [{ type: "text", text: "working" }] }];
	assert.deepEqual(collapseHandoffs(msgs), msgs);
});

test("a new prompt queued before the off-marker is kept after the handoff", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const msgs = [
		text("user", "fix it"),
		text("user", MARK_ON),
		{ role: "assistant", content: [{ type: "text", text: "done" }] },
		text("user", "now the docs"),
		text("user", MARK_OFF),
	];
	const out = collapseHandoffs(msgs);
	assert.deepEqual(out.map(m => m.role), ["user", "user"]);
	assert.match(out[0].content[0].text, /handoff/);
	assert.equal(out[1].content[0].text, "now the docs");
});

test("markers arrive at the context event as custom messages, not user messages", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const custom = (t) => ({ role: "custom", customType: "mellum-worker", content: [{ type: "text", text: t }] });
	const msgs = [
		text("user", "fix it"),
		custom(MARK_ON),
		{ role: "assistant", content: [{ type: "text", text: "done" }] },
		text("user", "now the docs"),
		custom(MARK_OFF),
	];
	const out = collapseHandoffs(msgs);
	assert.deepEqual(out.map(m => m.role), ["user", "user"]);
	assert.match(out[0].content[0].text, /handoff/);
});

test("handoff lists the bash commands run and flags written files that no longer exist", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const ts = (s) => Date.parse(`2026-10-09T19:${s}Z`);
	const msgs = [
		text("user", "Write a hello world python file with a unit test"),
		text("user", MARK_ON),
		{ role: "assistant", timestamp: ts("28:52.217"), usage: { input: 547, output: 651 }, content: [{ type: "toolCall", id: "1", name: "write", arguments: { path: "hello.py", content: "x" } }] },
		{ role: "toolResult", toolCallId: "1", toolName: "write", content: [{ type: "text", text: "Successfully wrote to hello.py" }] },
		{ role: "assistant", timestamp: ts("28:58.265"), usage: { input: 994, output: 102 }, content: [{ type: "toolCall", id: "2", name: "write", arguments: { path: "tests/test_hello.py", content: "y" } }] },
		{ role: "toolResult", toolCallId: "2", toolName: "write", content: [{ type: "text", text: "Successfully wrote to tests/test_hello.py" }] },
		{ role: "assistant", timestamp: ts("28:58.930"), usage: { input: 96, output: 77 }, content: [{ type: "toolCall", id: "3", name: "bash", arguments: { command: "uv run --offline pytest -q" } }] },
		{ role: "toolResult", toolCallId: "3", toolName: "bash", isError: true, content: [{ type: "text", text: "E   ModuleNotFoundError: No module named 'hello'\n\nCommand exited with code 2" }] },
		{ role: "assistant", timestamp: ts("29:04.814"), usage: { input: 180, output: 55 }, content: [{ type: "toolCall", id: "4", name: "bash", arguments: { command: "mv hello.py tests/hello.py" } }] },
		{ role: "toolResult", toolCallId: "4", toolName: "bash", content: [{ type: "text", text: "(no output)" }] },
		{ role: "assistant", timestamp: ts("29:09.304"), usage: { input: 839, output: 40 }, content: [{ type: "toolCall", id: "5", name: "bash", arguments: { command: "uv run --offline pytest -q" } }] },
		{ role: "toolResult", toolCallId: "5", toolName: "bash", content: [{ type: "text", text: "1 passed in 0.00s" }] },
		{ role: "assistant", timestamp: ts("29:13.636"), usage: { input: 143, output: 355 }, content: [{ type: "text", text: "Hello world Python file with unit test created and tests passed successfully." }] },
		text("user", MARK_OFF),
	];
	const exists = (p) => p === "tests/test_hello.py"; // hello.py was moved away by bash
	const out = collapseHandoffs(msgs, { exists });
	const h = out[0].content[0].text;
	assert.match(h, /Files edited or written: hello\.py \(missing at handoff\), tests\/test_hello\.py/);
	assert.match(h, /Commands run:\n- uv run --offline pytest -q \(failed\)\n- mv hello\.py tests\/hello\.py\n- uv run --offline pytest -q/);
	assert.match(h, /Mellum: 6 requests, 1,280 output tokens, 21 s, last command ok/);
	assert.ok(h.indexOf("Mellum: 6 requests") < h.indexOf("Task:"), "the summary line comes right after the header");
});

test("handoff summary reports a failed last command and tolerates missing usage and timestamps", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const msgs = [
		text("user", "fix it"),
		text("user", MARK_ON),
		{ role: "assistant", content: [{ type: "toolCall", id: "1", name: "bash", arguments: { command: "node --test" } }] },
		{ role: "toolResult", toolCallId: "1", toolName: "bash", isError: true, content: [{ type: "text", text: "fail 1" }] },
		{ role: "assistant", content: [{ type: "text", text: "could not" }] },
		text("user", MARK_OFF),
	];
	const h = collapseHandoffs(msgs, { exists: () => true })[0].content[0].text;
	assert.match(h, /Mellum: 2 requests, 0 output tokens, wall unknown, last command failed/);
	assert.match(h, /Commands run:\n- node --test \(failed\)/);
});

test("collapseHandoffs without an exists option never flags files", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const msgs = [text("user", "t"), text("user", MARK_ON), { role: "assistant", content: [{ type: "toolCall", id: "1", name: "write", arguments: { path: "nope/zzz.py" } }] }, text("user", MARK_OFF)];
	assert.match(collapseHandoffs(msgs)[0].content[0].text, /Files edited or written: nope\/zzz\.py\n/);
});

test("a bash call with no result is reported as unfinished, not ok, and does not steal the last output", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const msgs = [
		text("user", "t"),
		text("user", MARK_ON),
		{ role: "assistant", content: [{ type: "toolCall", id: "1", name: "bash", arguments: { command: "node --test" } }] },
		{ role: "toolResult", toolCallId: "1", toolName: "bash", content: [{ type: "text", text: "pass 3" }] },
		{ role: "assistant", content: [{ type: "toolCall", id: "2", name: "bash", arguments: { command: "sleep 999" } }] },
		text("user", MARK_OFF),
	];
	const h = collapseHandoffs(msgs)[0].content[0].text;
	assert.match(h, /Mellum: 2 requests, /);
	assert.match(h, /last command did not finish/);
	assert.match(h, /- sleep 999 \(no result\)/);
	assert.match(h, /Last command output:\npass 3/);
});

test("the commands list is capped and multi-line commands are collapsed to one line", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const calls = [];
	for (let i = 1; i <= 18; i++) {
		calls.push({ role: "assistant", content: [{ type: "toolCall", id: String(i), name: "bash", arguments: { command: i === 18 ? "cat <<'X'\nline one\nline two\nX" : `echo ${i}` } }] });
		calls.push({ role: "toolResult", toolCallId: String(i), toolName: "bash", content: [{ type: "text", text: "ok" }] });
	}
	const h = collapseHandoffs([text("user", "t"), text("user", MARK_ON), ...calls, text("user", MARK_OFF)])[0].content[0].text;
	assert.match(h, /Commands run \(3 earlier not shown\):\n- echo 4\n/);
	assert.ok(!h.includes("- echo 1\n"), "the earliest commands are dropped");
	assert.match(h, /- cat <<'X' line one line two X\n/);
	assert.match(h, /Mellum: 18 requests/);
});

test("summary uses the singular for one request", async () => {
	const { collapseHandoffs, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const h = collapseHandoffs([text("user", "t"), text("user", MARK_ON), { role: "assistant", content: [{ type: "text", text: "hi" }] }, text("user", MARK_OFF)])[0].content[0].text;
	assert.match(h, /Mellum: 1 request, 0 output tokens, wall unknown, no commands/);
});

test("runRecord builds the JSONL line for a span from the same fields as the handoff", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const { MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const ts = (s) => Date.parse(`2026-10-09T19:${s}Z`);
	const span = [
		{ role: "assistant", timestamp: ts("28:52.217"), usage: { input: 547, cacheRead: 1024, output: 651 }, content: [{ type: "toolCall", id: "1", name: "write", arguments: { path: "hello.py" } }] },
		{ role: "toolResult", toolCallId: "1", toolName: "write", content: [{ type: "text", text: "ok" }] },
		{ role: "assistant", timestamp: ts("28:58.930"), usage: { input: 96, cacheRead: 3072, output: 77 }, content: [{ type: "toolCall", id: "2", name: "bash", arguments: { command: "uv run --offline pytest -q" } }] },
		{ role: "toolResult", toolCallId: "2", toolName: "bash", isError: true, content: [{ type: "text", text: "Command exited with code 2" }] },
		{ role: "assistant", timestamp: ts("29:13.636"), usage: { input: 143, cacheRead: 5120, output: 355 }, content: [{ type: "text", text: "done" }] },
	];
	const rec = runRecord("Write a hello world python file with a unit test", span, { endedAt: ts("29:27.031"), cwd: "/p/ac-demo", model: "omlx/Mellum" });
	assert.equal(rec.task, "Write a hello world python file with a unit test");
	assert.equal(rec.model, "omlx/Mellum");
	assert.equal(rec.cwd, "/p/ac-demo");
	assert.equal(rec.startedAt, "2026-10-09T19:28:52.217Z");
	assert.equal(rec.endedAt, "2026-10-09T19:29:27.031Z");
	assert.equal(rec.requests, 3);
	assert.deepEqual(rec.usage, { input: 786, cacheRead: 9216, output: 1083 });
	assert.deepEqual(rec.files, ["hello.py"]);
	assert.deepEqual(rec.commands, [{ command: "uv run --offline pytest -q", failed: true, mutates: false }]);
	assert.equal(rec.lastCommand, "failed");
	assert.equal(rec.wallSeconds, 21);
	assert.equal(rec.finalReply, "done");
	assert.equal(JSON.stringify(rec).includes("\n"), false);
});

// Helpers for the schema-2 record tests: an assistant turn with tool calls, and its results.
const asst = (blocks, extra = {}) => ({ role: "assistant", content: blocks, ...extra });
const call = (id, name, args) => ({ type: "toolCall", id, name, arguments: args });
const res = (id, name, isError = false) => ({ role: "toolResult", toolCallId: id, toolName: name, isError, content: [{ type: "text", text: isError ? "Command exited with code 2" : "ok" }] });
const metaBase = { endedAt: Date.parse("2026-10-09T20:42:00Z"), cwd: "/p/ac-demo", model: "omlx/Mellum" };

function span2042() {
	const bash = (id, command, failed) => [asst([call(id, "bash", { command })]), res(id, "bash", failed)];
	return [
		asst([call("w1", "write", { path: "hello.py" })]), res("w1", "write"),
		asst([call("w2", "write", { path: "tests/test_hello.py" })]), res("w2", "write"),
		asst([call("w3", "write", { path: "test_hello.py" })]), res("w3", "write"),
		...bash("b1", "uv run --offline pytest -q", true),
		...bash("b2", 'python -c "import hello; print(hello.hello())"', true),
		...bash("b3", "uv python --version", true),
		...bash("b4", "uv run python --version", false),
		...bash("b5", 'uv run python -c "import hello; print(hello.hello())"', false),
		...bash("b6", "rm tests/test_hello.py", false),
		...bash("b7", "uv run --offline pytest -q", false),
		asst([{ type: "text", text: "All tests pass." }], { stopReason: "stop" }),
	];
}

test("runRecord schema 2 on the recorded 20:42 shape: missing files, mutating commands, edits, final turn", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const rec = runRecord("Write a hello world python file with a unit test", span2042(), { ...metaBase, exists: (p) => p !== "tests/test_hello.py" });
	assert.equal(rec.schema, 2);
	assert.deepEqual(rec.files, ["hello.py", "tests/test_hello.py", "test_hello.py"]);
	assert.deepEqual(rec.filesMissingAtEnd, ["tests/test_hello.py"]);
	assert.equal(rec.commands.length, 7);
	assert.equal(rec.commands[5].command, "rm tests/test_hello.py");
	assert.equal(rec.commands[5].mutates, true);
	assert.equal(rec.commands[0].mutates, false);
	assert.equal(rec.edits, 3);
	assert.equal(rec.taskNamesTestCommand, false);
	assert.deepEqual(rec.finalTurn, { stopReason: "stop", hadText: true, hadToolCall: false });
});

test("runRecord schema 2 marks an announce-and-stop span: failed last command, text-only final turn", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const span = [
		asst([call("1", "bash", { command: "node --test" })]), res("1", "bash", true),
		asst([{ type: "text", text: "The test failed; I will fix it." }], { stopReason: "stop" }),
	];
	const rec = runRecord("fix", span, metaBase);
	assert.equal(rec.finalTurn.hadToolCall, false);
	assert.equal(rec.finalTurn.hadText, true);
	assert.equal(rec.lastCommand, "failed");
});

test("runRecord schema 2 on the 20:10 shape: no edits, no files, nothing missing", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const span = [
		asst([call("1", "read", { path: "README.md" })]), res("1", "read"),
		asst([call("2", "bash", { command: "ls" })]), res("2", "bash"),
		asst([{ type: "text", text: "Two files." }], { stopReason: "stop" }),
	];
	const rec = runRecord("list files", span, { ...metaBase, exists: () => true });
	assert.equal(rec.edits, 0);
	assert.deepEqual(rec.files, []);
	assert.deepEqual(rec.filesMissingAtEnd, []);
});

test("runRecord schema 2 with no assistant turn reports an empty final turn", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const rec = runRecord("t", [{ role: "user", content: [{ type: "text", text: "hi" }] }], metaBase);
	assert.deepEqual(rec.finalTurn, { hadText: false, hadToolCall: false });
	assert.equal(rec.edits, 0);
});

test("runRecord schema 2 detects a task that names a test command", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	assert.equal(runRecord("fix it. Test command: node --test x", [], metaBase).taskNamesTestCommand, true);
	assert.equal(runRecord("fix it", [], metaBase).taskNamesTestCommand, false);
});

test("runRecord schema 2 passes meta through and defaults what is omitted", async () => {
	const { runRecord, PACKAGE_VERSION } = await import("../extensions/mellum-record.ts");
	const given = runRecord("t", [], { ...metaBase, host: "print", activation: "one-shot", promptVersion: "v5", nudges: 1, guardBlocks: 2 });
	assert.equal(given.host, "print");
	assert.equal(given.activation, "one-shot");
	assert.equal(given.promptVersion, "v5");
	assert.equal(given.nudges, 1);
	assert.equal(given.guardBlocks, 2);
	const bare = runRecord("t", [], metaBase);
	assert.equal(bare.host, "unknown");
	assert.equal(bare.activation, "unknown");
	assert.equal(bare.promptVersion, "unknown");
	assert.equal(bare.nudges, 0);
	assert.equal(bare.guardBlocks, 0);
	assert.deepEqual(bare.filesMissingAtEnd, []);
	const pkg = JSON.parse(readFileSync("package.json", "utf8"));
	assert.equal(bare.version, pkg.version);
	assert.equal(PACKAGE_VERSION, pkg.version);
});

const FACTS = "\n\nProject facts:\n- Test command: make test";

// Project-facts injection is the context/add-project-facts remedy unit now, and reading the
// facts (AGENTS.md, the pytest fallback, the cap, MELLUM_MODE_FACTS) is tested in
// mellum-facts.test.mjs. What stays the worker's export is the withFacts placement primitive
// the unit builds on, so its mechanics — append point, multimodal, idempotency — are tested
// here directly rather than through the removed filterForMellum facts path.
test("withFacts appends to a string message and to the last text part of array content, after an image too", () => {
	const img = { type: "image_url", image_url: { url: "data:image/png;base64,AAAA" } };
	assert.equal(withFacts({ role: "user", content: "t" }, FACTS).content, "t" + FACTS);
	const arr = { role: "user", content: [{ type: "text", text: "look" }, img, { type: "text", text: "and fix" }, img] };
	const out = withFacts(arr, FACTS);
	assert.equal(out.content[2].text, "and fix" + FACTS);
	assert.deepEqual(out.content[3], img, "the trailing image is untouched");
	assert.equal(arr.content[2].text, "and fix", "input not mutated");
	const onlyImage = withFacts({ role: "user", content: [img] }, FACTS);
	assert.deepEqual(onlyImage.content[0], img);
	assert.equal(onlyImage.content[1].type, "text", "a new text part carries the facts after an image-only message");
	assert.match(onlyImage.content[1].text, /Project facts:/);
});

test("withFacts is idempotent: a message already ending with the block gets no second one", () => {
	const once = withFacts({ role: "user", content: "t" }, FACTS);
	assert.equal(withFacts(once, FACTS), once, "a string already ending with the block is returned unchanged");
	const arrOnce = withFacts({ role: "user", content: [{ type: "text", text: "t" }] }, FACTS);
	const arrTwice = withFacts(arrOnce, FACTS);
	const text = arrTwice.content.filter((p) => p.type === "text").map((p) => p.text).join("");
	assert.equal(text.split("Project facts:").length, 2, "exactly one facts block after re-applying");
});

test("runRecord carries facts from the meta, and omits the field when there is none", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const meta = { endedAt: 1, cwd: "/p", model: "omlx/M" };
	const rec = runRecord("t", [], { ...meta, facts: { source: "detected", testCommand: "uv run --offline python -m pytest -q", chars: 50 } });
	assert.deepEqual(rec.facts, { source: "detected", testCommand: "uv run --offline python -m pytest -q", chars: 50 });
	assert.equal("facts" in JSON.parse(JSON.stringify(runRecord("t", [], meta))), false);
});

test("the handoff summary line carries facts: <source> when the on-marker does", async () => {
	const { collapseHandoffs } = await import("../extensions/mellum-worker.ts");
	const build = (on) => collapseHandoffs([text("user", "task"), text("user", on), { role: "assistant", content: [{ type: "text", text: "done" }] }, text("user", MARK_OFF), text("user", "next")]);
	const withFacts = build(`${MARK_ON} facts: agents-md+detected`).map((m) => textOf(m)).join("\n");
	assert.match(withFacts, /, facts: agents-md\+detected\n/);
	const without = build(MARK_ON).map((m) => textOf(m)).join("\n");
	assert.doesNotMatch(without, /facts:/);
});
function textOf(m) {
	return typeof m.content === "string" ? m.content : m.content.map((p) => p.text ?? "").join("\n");
}

test("parseSubcommand: on, off, check and learn [n] are commands; anything longer is a task", async () => {
	const { parseSubcommand } = await import("../extensions/mellum-worker.ts");
	assert.deepEqual(parseSubcommand(""), { cmd: "on" });
	assert.deepEqual(parseSubcommand("  "), { cmd: "on" });
	assert.deepEqual(parseSubcommand("on"), { cmd: "on" });
	assert.deepEqual(parseSubcommand(" off "), { cmd: "off" });
	assert.deepEqual(parseSubcommand("check"), { cmd: "check" });
	assert.deepEqual(parseSubcommand("learn"), { cmd: "learn", n: 10 });
	assert.deepEqual(parseSubcommand("learn 25"), { cmd: "learn", n: 25 });
	assert.deepEqual(parseSubcommand("check the export totals"), { cmd: "task", task: "check the export totals" });
	assert.deepEqual(parseSubcommand("learn how the cache works"), { cmd: "task", task: "learn how the cache works" });
	assert.deepEqual(parseSubcommand(" fix the cart "), { cmd: "task", task: "fix the cart" });
});

test("runRecord carries the server settings check from the meta, and omits the field when there is none", async () => {
	const { runRecord } = await import("../extensions/mellum-record.ts");
	const meta = { endedAt: 1, cwd: "/p", model: "omlx/M" };
	const diffs = [{ key: "max_context_window", expected: 56000, actual: 32768 }];
	assert.deepEqual(runRecord("t", [], { ...meta, server: { match: false, diffs } }).server, { match: false, diffs });
	assert.deepEqual(runRecord("t", [], { ...meta, server: { match: null, diffs: [] } }).server, { match: null, diffs: [] });
	assert.equal("server" in JSON.parse(JSON.stringify(runRecord("t", [], meta))), false);
});

test("openSpan takes the task from the prompt before an off-marker, as back-to-back one-shots deliver it", async () => {
	const { openSpan, MARK_ON, MARK_OFF } = await import("../extensions/mellum-worker.ts");
	const user = (text) => ({ role: "user", content: [{ type: "text", text }] });
	const marker = (text) => ({ role: "custom", customType: "mellum-worker", content: text });
	const reply = { role: "assistant", content: [{ type: "text", text: "done" }] };
	// Seen in ac-demo, 2026-10-12: the first one-shot's off-marker is queued for the next turn,
	// so it lands after the second prompt, between that prompt and the second on-marker.
	const messages = [
		user("Implement Phase 1 of specs/roadmap.md"), marker(`${MARK_ON} facts: agents-md`), reply,
		user("Implement Phase 2 of specs/roadmap.md"), marker(MARK_OFF), marker(`${MARK_ON} facts: agents-md`), reply,
	];
	assert.equal(openSpan(messages).task, "Implement Phase 2 of specs/roadmap.md");
	assert.deepEqual(openSpan(messages).span, [reply]);
	// Still the plain case: prompt, then on-marker.
	assert.equal(openSpan(messages.slice(0, 3)).task, "Implement Phase 1 of specs/roadmap.md");
	// An off-marker with no prompt before it gives no task from before the span.
	assert.equal(openSpan([marker(MARK_OFF), marker(MARK_ON), user("from inside"), reply]).task, "from inside");
});
