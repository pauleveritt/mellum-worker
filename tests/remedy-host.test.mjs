import { test } from "node:test";
import assert from "node:assert/strict";

/** A fake Pi with commands, a UI that records notifications and status, and hook dispatch. */
function fakePi() {
	const handlers = {};
	const commands = {};
	const tools = [];
	const ui = { notes: [], status: {}, picks: [] };
	const ctx = {
		hasUI: true,
		ui: {
			notify: (msg, level) => ui.notes.push([level, msg]),
			setStatus: (key, text) => { ui.status[key] = text; },
			select: async (_title, options) => ui.picks.shift()?.(options),
		},
	};
	return {
		handlers, commands, tools, ui, ctx,
		on(event, handler) { (handlers[event] ??= []).push(handler); },
		registerTool(tool) { tools.push(tool); },
		registerCommand(name, spec) { commands[name] = spec; },
		fire(event, payload) { return handlers[event]?.map((h) => h(payload, ctx)).find((r) => r !== undefined); },
		run(name, args) { return commands[name].handler(args, ctx); },
	};
}

const host = () => import("../extensions/mellum-remedies.ts");
const ls = { toolName: "ls", input: { path: "." } };

test("every remedy starts off: the session is bare Pi until the learner turns one on", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	for (let i = 0; i < 8; i++) assert.equal(pi.fire("tool_call", ls), undefined);
	assert.equal(pi.ui.status.remedies, undefined);
});

test("/remedy on guard/break-repeat-loops blocks the sixth identical call; off stops it", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	await pi.run("remedy", "on guard/break-repeat-loops");
	assert.equal(pi.ui.status.remedies, "remedies: 1 on");
	for (let i = 0; i < 5; i++) assert.equal(pi.fire("tool_call", ls), undefined);
	assert.equal(pi.fire("tool_call", ls)?.block, true);
	await pi.run("remedy", "off guard/break-repeat-loops");
	assert.equal(pi.fire("tool_call", ls), undefined);
	assert.equal(pi.ui.status.remedies, undefined);
});

test("/remedy preset:easy turns on every unit in the preset", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	await pi.run("remedy", "preset:easy");
	assert.equal(pi.ui.status.remedies, "remedies: 7 on");
	assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command: "uv run python app.py" } })?.block, true);
});

test("an unknown unit is refused with a message, nothing changes", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	await pi.run("remedy", "on guard/no-such-thing");
	assert.equal(pi.ui.notes.at(-1)[0], "error");
	assert.match(pi.ui.notes.at(-1)[1], /no remedy unit guard\/no-such-thing/);
	assert.equal(pi.ui.status.remedies, undefined);
});

test("names complete from what the learner has typed", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	const items = await pi.commands.remedy.getArgumentCompletions("on guard/br");
	assert.deepEqual(items.map((i) => i.value), ["on guard/break-repeat-loops"]);
});

test("bare /remedy opens a picker; choosing a unit toggles it", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	pi.ui.picks.push((options) => options.find((o) => o.includes("guard/break-repeat-loops")));
	await pi.run("remedy", "");
	assert.equal(pi.ui.status.remedies, "remedies: 1 on");
});
