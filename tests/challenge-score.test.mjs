import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const host = () => import("../extensions/mellum-remedies.ts");

/** A fake Pi that records notifications and runs registered commands, like remedy-host's. */
function fakePi() {
	const commands = {};
	const ui = { notes: [] };
	const ctx = { hasUI: true, ui: { notify: (msg, level) => ui.notes.push([level, msg]), setStatus() {} } };
	return {
		commands, ui, ctx,
		on() {},
		registerTool() {},
		registerCommand(name, spec) { commands[name] = spec; },
		run(name, args) { return commands[name].handler(args, ctx); },
	};
}

/** Write a run.json into its own run dir under `dir`, the way the harness lays repeats out. */
function writeRun(dir, name, record) {
	mkdirSync(join(dir, name), { recursive: true });
	writeFileSync(join(dir, name, "run.json"), JSON.stringify(record) + "\n");
}

test("scoreRuns totals passes, turns and wall across the run.json files, one row each", async () => {
	const { scoreRuns } = await host();
	const dir = mkdtempSync(join(tmpdir(), "challenge-score-"));
	writeRun(dir, "r1", { passed: true, turns: 180, wall: 402.4 });
	writeRun(dir, "r2", { passed: false, turns: 185, wall: 398.1 });
	writeRun(dir, "r3", { passed: true, turns: 175, wall: 400.0 });
	const s = scoreRuns(dir);
	assert.equal(s.total, 3);
	assert.equal(s.passed, 2);
	assert.equal(s.turns, 540);
	assert.equal(Math.round(s.wall), 1201);
	assert.deepEqual(s.rows.map((r) => r.passed), [true, false, true]);
});

test("scoreRuns falls back to requests when turns is absent, and skips dirs without a run.json", async () => {
	const { scoreRuns } = await host();
	const dir = mkdtempSync(join(tmpdir(), "challenge-score-"));
	writeRun(dir, "r1", { passed: true, requests: 42, wall: 10 });
	mkdirSync(join(dir, "not-a-run"), { recursive: true });
	const s = scoreRuns(dir);
	assert.equal(s.total, 1);
	assert.equal(s.turns, 42);
});

test("scoreRuns returns zeros for a runs dir that was never created", async () => {
	const { scoreRuns } = await host();
	const s = scoreRuns(join(tmpdir(), "challenge-score-does-not-exist-xyz"));
	assert.deepEqual(s, { passed: 0, total: 0, turns: 0, wall: 0, rows: [] });
});

test("/challenge with no tier shows usage and runs nothing", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	await pi.run("challenge", "");
	assert.equal(pi.ui.notes.at(-1)[0], "info");
	assert.match(pi.ui.notes.at(-1)[1], /easy\|medium\|hard/);
	assert.match(pi.ui.notes.at(-1)[1], /default 1/);
});

test("/challenge bronze is refused as an unknown tier", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	await pi.run("challenge", "bronze");
	assert.match(pi.ui.notes.at(-1)[1], /easy\|medium\|hard/);
});

test("completions offer each tier and its n= presets", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	const items = await pi.commands.challenge.getArgumentCompletions("easy");
	const values = items.map((i) => i.value);
	assert.ok(values.includes("easy"));
	assert.ok(values.includes("easy n=3"));
	assert.ok(values.includes("easy n=5"));
});
