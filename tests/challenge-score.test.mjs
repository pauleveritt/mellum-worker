import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const host = () => import("../extensions/mellum-remedies.ts");

/** A fake Pi that records notifications and runs registered commands, like remedy-host's. */
function fakePi() {
	const commands = {};
	const ui = { notes: [], picks: [], seen: [] };
	const ctx = {
		hasUI: true,
		ui: {
			notify: (msg, level) => ui.notes.push([level, msg]),
			setStatus() {},
			select: async (_title, options) => { ui.seen.push(options); return ui.picks.shift()?.(options); },
		},
	};
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

test("completions offer each tier, its n= presets, and submit", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	const easy = (await pi.commands.challenge.getArgumentCompletions("easy")).map((i) => i.value);
	assert.ok(easy.includes("easy"));
	assert.ok(easy.includes("easy n=3"));
	assert.ok(easy.includes("easy:vanilla"));
	const sub = (await pi.commands.challenge.getArgumentCompletions("sub")).map((i) => i.value);
	assert.deepEqual(sub, ["submit"]);
});

/** Run a block with PI_CODING_AGENT_DIR pointed at a throwaway agent dir. */
async function withAgentDir(dir, fn) {
	const prev = process.env.PI_CODING_AGENT_DIR;
	process.env.PI_CODING_AGENT_DIR = dir;
	try {
		await fn();
	} finally {
		if (prev === undefined) delete process.env.PI_CODING_AGENT_DIR;
		else process.env.PI_CODING_AGENT_DIR = prev;
	}
}

test("/challenge submit with no recorded runs says so and opens nothing", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	await withAgentDir(mkdtempSync(join(tmpdir(), "agent-empty-")), () => pi.run("challenge", "submit"));
	assert.equal(pi.ui.notes.at(-1)[0], "info");
	assert.match(pi.ui.notes.at(-1)[1], /no challenge runs recorded/);
});

test("/challenge submit lists recorded runs to toggle, then confirms before any PR", async () => {
	const pi = fakePi();
	await (await host()).default(pi);
	const agent = mkdtempSync(join(tmpdir(), "agent-recs-"));
	writeFileSync(
		join(agent, "mellum-challenge-runs.jsonl"),
		JSON.stringify({ tier: "easy", remedies: ["guard/repeat-loops"], runs: 1, passed: 1, total: 1, turns: 42, wall: 300, at: "2026-11-02T15:34:00.000Z" }) + "\n",
	);
	pi.ui.picks.push(
		(o) => o.find((x) => x.includes("1. easy")), // toggle the run on
		(o) => o.find((x) => x.startsWith("✅")), // Submit
		() => "Cancel", // decline the PR, so no git/gh runs
	);
	await withAgentDir(agent, () => pi.run("challenge", "submit"));
	assert.ok(pi.ui.seen[0].some((x) => x.includes("easy · worker+1 · 1/1 · 42 turns")));
	assert.ok(pi.ui.seen.at(-1).includes("Open PR"));
});
