import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import unit, { install, moduleName } from "../remedies/check/compile-import.ts";

/** A fake Pi: handlers by event, a tool_result fired with the session's cwd, and a settle merged
 * the way Pi 1.4.0's emitBoundary merges it. Real uv and python run underneath. */
function fakePi(cwd) {
	const handlers = {};
	const tools = [];
	const ctx = { cwd };
	return {
		handlers,
		tools,
		on(event, handler) { (handlers[event] ??= []).push(handler); },
		registerTool(tool) { tools.push(tool); },
		toolResult(toolName, path, isError = false) {
			const event = { toolName, input: { path }, content: [{ type: "text", text: "ok" }], isError };
			return handlers.tool_result?.map((h) => h(event, ctx)).find((r) => r !== undefined);
		},
		settle(prior = []) {
			let entries = prior;
			let cont = false;
			for (const h of handlers.agent_before_settle ?? []) {
				const r = h({ type: "agent_before_settle", entries, continue: cont }, ctx);
				if (r?.entries !== undefined) entries = r.entries;
				if (r?.continue !== undefined) cont = r.continue;
			}
			return { entries, continue: cont };
		},
	};
}

function workspace(files) {
	const dir = mkdtempSync(join(tmpdir(), "compile-import-"));
	for (const [rel, source] of Object.entries(files)) {
		mkdirSync(join(dir, rel, ".."), { recursive: true });
		writeFileSync(join(dir, rel), source);
	}
	return dir;
}

test("moduleName maps a workspace .py path to its dotted module, and nothing else", () => {
	assert.equal(moduleName("app.py"), "app");
	assert.equal(moduleName("pkg/mod.py"), "pkg.mod");
	assert.equal(moduleName("pkg/__init__.py"), "pkg");
	assert.equal(moduleName("notes.md"), null);
	assert.equal(moduleName("../outside.py"), null);
	assert.equal(moduleName("/abs/elsewhere.py"), null);
});

test("check/compile-import installs a tool_result and a settle hook and registers no tool", () => {
	const pi = fakePi(tmpdir());
	unit(pi);
	assert.deepEqual(Object.keys(pi.handlers).sort(), ["agent_before_settle", "tool_result"]);
	assert.equal(pi.tools.length, 0);
});

test("a write that leaves a SyntaxError comes back as a failed write with the compiler's message", () => {
	const dir = workspace({ "bad.py": "def f(:\n    pass\n" });
	const pi = fakePi(dir);
	install(pi);
	const result = pi.toolResult("write", "bad.py");
	assert.equal(result.isError, true);
	assert.equal(result.content[0].text, "ok");
	assert.match(result.content.map((c) => c.text).join("\n"), /SyntaxError/);
	assert.match(result.content.map((c) => c.text).join("\n"), /bad\.py/);
});

test("an edit that leaves a SyntaxError is caught the same way", () => {
	const dir = workspace({ "pkg/mod.py": "x = (1,\n" });
	const pi = fakePi(dir);
	install(pi);
	assert.equal(pi.toolResult("edit", "pkg/mod.py").isError, true);
});

test("a valid .py write, a non-.py write, a write outside the workspace and a failed write pass untouched", () => {
	const outside = workspace({ "elsewhere.py": "def f(:\n" });
	const dir = workspace({ "ok.py": "x = 1\n", "notes.md": "def f(:\n" });
	const pi = fakePi(dir);
	install(pi);
	assert.equal(pi.toolResult("write", "ok.py"), undefined);
	assert.equal(pi.toolResult("write", "notes.md"), undefined);
	assert.equal(pi.toolResult("write", join(outside, "elsewhere.py")), undefined);
	assert.equal(pi.toolResult("write", "ok.py", true), undefined);
	assert.equal(pi.toolResult("read", "ok.py"), undefined);
});

test("at settle a module the session wrote that fails to import sends the model back, keeping earlier entries", () => {
	const dir = workspace({ "app.py": "import no_such_module_r1\n" });
	const pi = fakePi(dir);
	install(pi);
	pi.toolResult("write", "app.py");
	const earlier = { type: "custom_message", customType: "earlier", content: "x", display: true };
	const { entries, continue: cont } = pi.settle([earlier]);
	assert.deepEqual(entries.map((e) => e.customType), ["earlier", "compile-import"]);
	assert.equal(cont, true);
	assert.match(entries[1].content, /app/);
	assert.match(entries[1].content, /ModuleNotFoundError/);
});

test("the import gate sends the model back at most 3 times", () => {
	const dir = workspace({ "app.py": "import no_such_module_r1\n" });
	const pi = fakePi(dir);
	install(pi);
	pi.toolResult("write", "app.py");
	for (let i = 0; i < 3; i++) assert.equal(pi.settle().continue, true);
	assert.deepEqual(pi.settle(), { entries: [], continue: false });
});

test("modules that import cleanly let the session settle", () => {
	const dir = workspace({ "app.py": "x = 1\n", "pkg/__init__.py": "", "pkg/mod.py": "from app import x\n" });
	const pi = fakePi(dir);
	install(pi);
	for (const rel of ["app.py", "pkg/__init__.py", "pkg/mod.py"]) pi.toolResult("write", rel);
	assert.deepEqual(pi.settle(), { entries: [], continue: false });
});

test("an import that hangs is stopped at the timeout and reads red", () => {
	const dir = workspace({ "app.py": "import time\ntime.sleep(30)\n" });
	const pi = fakePi(dir);
	install(pi, { importTimeoutMs: 1500 });
	pi.toolResult("write", "app.py");
	const t0 = Date.now();
	const { entries } = pi.settle();
	assert.ok(Date.now() - t0 < 6000, `took ${Date.now() - t0} ms`);
	assert.match(entries[0].content, /timed out/);
});

test("when uv cannot start, neither hook blocks", () => {
	const dir = workspace({ "bad.py": "def f(:\n", "app.py": "import no_such_module_r1\n" });
	const pi = fakePi(dir);
	install(pi, { uv: "no-such-uv-r1" });
	assert.equal(pi.toolResult("write", "bad.py"), undefined);
	pi.toolResult("write", "app.py");
	assert.deepEqual(pi.settle(), { entries: [], continue: false });
});
