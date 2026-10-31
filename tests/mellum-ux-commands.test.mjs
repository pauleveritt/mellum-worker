/**
 * The UX surface of the opt-in extensions: the slash commands and model tools
 * they register, and that dispatching them does the right thing. A fake `pi`
 * captures registrations and hooks; handlers run against temp files so nothing
 * touches a real home directory or model.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import mellumContext from "../extensions/mellum-context.ts";
import mellumFiles from "../extensions/mellum-files.ts";
import mellumVision from "../extensions/mellum-vision.ts";
import mellumReplay from "../extensions/mellum-replay.ts";
import mellumControl from "../extensions/mellum-control.ts";
import mellumRethink from "../extensions/mellum-rethink.ts";

function fakePi() {
	const commands = {};
	const tools = {};
	const hooks = {};
	const notes = [];
	const pi = {
		registerCommand: (name, def) => { commands[name] = def; },
		registerTool: (name, def) => { tools[name] = def; },
		on: (ev, fn) => { (hooks[ev] ??= []).push(fn); },
		sendUserMessage: (m) => { notes.push(["send", m]); },
	};
	const ctx = { ui: { notify: (msg, level) => notes.push([level ?? "info", String(msg)]) } };
	return { pi, commands, tools, hooks, notes, ctx };
}

const tmp = () => mkdtempSync(join(tmpdir(), "mellum-ux-"));

test("mellum-context: registers /index, /context and the context_search tool", () => {
	const { pi, commands, tools } = fakePi();
	mellumContext(pi);
	assert.ok(commands.index && typeof commands.index.handler === "function");
	assert.ok(commands.context && typeof commands.context.handler === "function");
	assert.ok(tools.context_search && typeof tools.context_search.handler === "function");
});

test("mellum-context: /index then /context finds the indexed passage", async () => {
	const dir = tmp();
	process.env.MELLUM_CONTEXT_DB = join(dir, "ctx.db");
	const file = join(dir, "app.py");
	writeFileSync(file, "def home():\n    return 'board'\n\ndef sum_columns():\n    return totals\n");
	const { pi, commands, tools, notes } = fakePi();
	mellumContext(pi);
	await commands.index.handler(file, { ui: { notify: (m, l) => notes.push([l, String(m)]) } });
	assert.match(notes.at(-1)[1], /indexed \d+ chunks/);
	const result = await tools.context_search.handler({ query: "sum_columns" });
	assert.match(result, /sum_columns/);
	delete process.env.MELLUM_CONTEXT_DB;
});

test("mellum-files: registers /read-file and the read_document tool; reads a text file", async () => {
	const dir = tmp();
	const file = join(dir, "notes.txt");
	writeFileSync(file, "quarterly revenue is up");
	const { pi, commands, tools } = fakePi();
	mellumFiles(pi);
	assert.ok(commands["read-file"] && typeof commands["read-file"].handler === "function");
	const text = await tools.read_document.handler({ path: file });
	assert.match(text, /quarterly revenue/);
});

test("mellum-vision: registers /see and describe_image; rejects a non-image without running a model", async () => {
	const { pi, commands, tools } = fakePi();
	mellumVision(pi);
	assert.ok(commands.see && typeof commands.see.handler === "function");
	const out = await tools.describe_image.handler({ path: "report.pdf" });
	assert.match(out, /not an image/);
});

test("mellum-replay: /replay with no captured feed warns instead of throwing", async () => {
	const dir = tmp();
	process.env.MELLUM_FEED = join(dir, "no-such-feed.ndjson");
	const { pi, commands, notes, ctx } = fakePi();
	mellumReplay(pi);
	assert.ok(commands.replay && typeof commands.replay.handler === "function");
	await commands.replay.handler("try harder", ctx);
	assert.match(notes.at(-1)[1], /no captured prompt/);
	delete process.env.MELLUM_FEED;
});

test("mellum-control: hooks the turn boundary (play/pause has no command)", () => {
	const { pi, hooks, commands } = fakePi();
	mellumControl(pi);
	assert.deepEqual(Object.keys(commands), []);
	assert.ok((hooks.before_provider_request || []).length === 1);
});

test("mellum-rethink: hooks context + agent_before_settle to push back", () => {
	const { pi, hooks } = fakePi();
	mellumRethink(pi);
	assert.ok((hooks.context || []).length === 1);
	assert.ok((hooks.agent_before_settle || []).length === 1);
});
