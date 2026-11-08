import { test } from "node:test";
import assert from "node:assert/strict";

// Ported from lc40-thin-worker (c9ee0b04, 81f659ce); the fake Pi is remedy-units.test.mjs's.
function fakePi() {
	const handlers = {};
	const tools = [];
	return {
		handlers,
		tools,
		on(event, handler) { (handlers[event] ??= []).push(handler); },
		registerTool(tool) { tools.push(tool); },
		events() { return Object.keys(handlers).sort(); },
		fire(event, payload) { return handlers[event]?.map((h) => h(payload)).find((r) => r !== undefined); },
	};
}

test("guard/foreground-log-follow installs one tool_call hook and nothing else", async () => {
	const pi = fakePi();
	(await import("../remedies/guard/foreground-log-follow.ts")).default(pi);
	assert.deepEqual(pi.events(), ["tool_call"]);
	assert.equal(pi.handlers.tool_call.length, 1);
	assert.equal(pi.tools.length, 0);
});

test("guard/foreground-log-follow blocks compound foreground follows and preserves finite reads", async () => {
 const pi = fakePi();
 (await import("../remedies/guard/foreground-log-follow.ts")).default(pi);
 for (const command of [
  "uvicorn service:app & echo ready && tail -f /tmp/service.log",
  "tail -F worker.log", "tail --follow=name worker.log", "tail -vf worker.log",
  "tail -n 20 -f worker.log", "env RUN=1 /usr/bin/tail --follow worker.log",
  "timeout 5 tail -f worker.log", "uv run --offline tail -F worker.log",
  "(tail -f worker.log) | cat",
 ]) assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command } })?.block, true, command);
 for (const command of [
  "tail -n 50 worker.log", "tail -c 100 worker.log", "tail --lines 50 worker.log",
  "tail -- --follow", "tail -n -f worker.log", "tail --bytes -f worker.log",
  "tail --help", "tail -f --help", "tail --version", "tail -F --version",
  "printf '%s' 'tail -f worker.log'", "rg 'tail -f' .", "tail -f worker.log &",
  "(tail -f worker.log | cat) & echo ready",
 ]) assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command } }), undefined, command);
 assert.equal(pi.fire("tool_call", { toolName: "read", input: { path: "tail -f" } }), undefined);
});

test("log-follow guard distinguishes nohup from detachment and redirection targets from options", async () => {
 const pi = fakePi();
 (await import("../remedies/guard/foreground-log-follow.ts")).default(pi);
 for (const command of [
  "nohup tail -f worker.log", "env RUN=1 nohup timeout 5 tail -F worker.log",
  "tail -f worker.log > --help", "tail -f worker.log 2> --version",
  "> out.log tail -f worker.log", "2> --help tail -f worker.log",
  'tail -f worker.log > "--help"', 'tail -n "2"> out.log -f worker.log',
  "tail -f worker.log &> --version", "tail -f worker.log 2>&1",
 ]) assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command } })?.block, true, command);
 for (const command of [
  "nohup tail -f worker.log &", "tail -n 50 worker.log > -f",
  "tail -n 50 worker.log 2> --follow", "tail -n 50 worker.log >'-F'",
  '> out.log tail -n 50 worker.log', 'printf "%s" "tail -f > --help"',
 ]) assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command } }), undefined, command);
});

test("log-follow guard ignores redirection operands in executable and option classification", async () => {
 const pi = fakePi();
 (await import("../remedies/guard/foreground-log-follow.ts")).default(pi);
 assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command: "tail -f worker.log > --help" } })?.block, true);
 assert.equal(pi.fire("tool_call", { toolName: "bash", input: { command: "tail -n 50 worker.log > -f" } }), undefined);
});
