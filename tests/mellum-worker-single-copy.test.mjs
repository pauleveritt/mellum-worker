import assert from "node:assert/strict";
import test from "node:test";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import install from "../extensions/mellum-worker.ts";

process.env.HOME = mkdtempSync(`${tmpdir()}/mellum-home-`);
const noServer = async () => {
	throw new TypeError("fetch failed: no server in tests");
};

// Pi's event bus: one per session runtime, shared by every loaded extension, emit is synchronous.
function makeBus() {
	const listeners = new Map();
	return {
		emit: (channel, data) => (listeners.get(channel) ?? []).forEach(fn => fn(data)),
		on: (channel, fn) => {
			listeners.set(channel, [...(listeners.get(channel) ?? []), fn]);
			return () => {};
		},
	};
}

function copy(bus) {
	const commands = [];
	const hooks = [];
	const pi = {
		events: bus,
		on: (name) => { hooks.push(name); },
		registerCommand: (name) => { commands.push(name); },
		getActiveTools: () => [],
		setActiveTools: () => {},
		setModel: async () => true,
		sendMessage: () => {},
		sendUserMessage: () => {},
	};
	install(pi, { fetch: noServer });
	return { commands, hooks };
}

test("a second copy on the same session registers nothing", () => {
	const bus = makeBus();
	const first = copy(bus);
	const second = copy(bus);
	assert.deepEqual(first.commands, ["mellum"], "the first copy owns /mellum");
	assert.ok(first.hooks.includes("before_provider_request"), "the first copy owns the hooks");
	assert.deepEqual(second.commands, [], "no /mellum:1 duplicate");
	assert.deepEqual(second.hooks, [], "no second set of hooks");
});

test("a fresh session (reload builds a new bus) registers again", () => {
	copy(makeBus());
	const reloaded = copy(makeBus());
	assert.deepEqual(reloaded.commands, ["mellum"]);
});

test("a lone copy on a host with no event bus still registers", () => {
	const lone = copy(undefined);
	assert.deepEqual(lone.commands, ["mellum"]);
});
