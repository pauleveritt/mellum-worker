import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, realpathSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { killTargets, createForeignProcessGuard, processCwd } from "../extensions/mellum-guards.ts";

// The recorded pathology (2026-11-11 on-policy sampling, rung 7 r2): the worker wanted port 8001
// for its own uvicorn, found the harness's llama-server listening there, and ran `kill 92231`.
// The model server died mid-run, and 15 later runs in the batch got only connection errors.
// The worker may stop what it started (its cwd is in the workspace), never anything else.

const WS = "/work/space";
const cwdOf = (table) => (pid) => table[pid];
const guardWith = (table) => createForeignProcessGuard(WS, cwdOf(table), new Set([1, 2]));
const bash = (command) => ({ toolName: "bash", input: { command } });

test("killTargets: literal pids from kill in any command position, signals skipped", () => {
	assert.deepEqual(killTargets("kill 92231"), { pids: [92231], indirect: false });
	assert.deepEqual(killTargets("kill -9 12 34"), { pids: [12, 34], indirect: false });
	assert.deepEqual(killTargets("kill -s TERM 55"), { pids: [55], indirect: false });
	assert.deepEqual(killTargets("sleep 1; kill 7 && echo ok"), { pids: [7], indirect: false });
	assert.deepEqual(killTargets("cat app.py"), { pids: [], indirect: false });
	assert.deepEqual(killTargets(undefined), { pids: [], indirect: false });
});

test("killTargets: a kill whose target the guard cannot see is indirect", () => {
	for (const c of [
		"pkill -f llama-server",
		"killall uvicorn",
		"lsof -ti:8001 | xargs kill",
		"kill $(lsof -t -i:8001)",
		"kill `cat server.pid`",
		"kill $PID",
		"fuser -k 8001/tcp",
	]) {
		assert.equal(killTargets(c).indirect, true, c);
	}
});

test("killTargets: naming kill in a read or a word is not a kill", () => {
	assert.equal(killTargets("grep -n kill app.py").indirect, false);
	assert.deepEqual(killTargets("echo 'kill 5'").pids, []);
	assert.deepEqual(killTargets("uv run python skill.py 3").pids, []);
});

test("guard: blocks killing a process that lives outside the workspace (the llama-server case)", () => {
	const blocked = guardWith({ 92231: "/Users/mac/scratch" })(bash("kill 92231"));
	assert.equal(blocked?.block, true);
	assert.match(blocked.reason, /not one you started/);
	assert.match(blocked.reason, /different port/);
});

test("guard: blocks killing the harness itself (own pid or parent), even though its cwd is the workspace", () => {
	assert.equal(guardWith({ 1: WS, 2: WS })(bash("kill 2"))?.block, true);
});

test("guard: blocks name-based and indirect kills, pointing at the explicit pid", () => {
	const blocked = guardWith({})(bash("lsof -ti:8001 | xargs kill -9"));
	assert.equal(blocked?.block, true);
	assert.match(blocked.reason, /\$!/);
});

test("guard: allows killing a server the worker started in its workspace", () => {
	const g = guardWith({ 500: WS, 501: `${WS}/app` });
	assert.equal(g(bash("kill 500")), undefined);
	assert.equal(g(bash("kill -9 501")), undefined);
});

test("guard: allows a pid that is already gone, plain commands, and non-bash tools", () => {
	const g = guardWith({});
	assert.equal(g(bash("kill 4242")), undefined); // no such process: the kill fails harmlessly
	assert.equal(g(bash("uv run python -m pytest -q")), undefined);
	assert.equal(g({ toolName: "edit", input: { path: "kill.py" } }), undefined);
});

test("processCwd: reads a real process's working directory, undefined for a dead pid", async () => {
	const dir = realpathSync(mkdtempSync(join(tmpdir(), "fpg-")));
	const child = spawn("sleep", ["30"], { cwd: dir });
	try {
		await new Promise((r) => setTimeout(r, 200));
		assert.equal(processCwd(child.pid), dir);
	} finally {
		child.kill();
	}
	assert.equal(processCwd(999999), undefined);
});
