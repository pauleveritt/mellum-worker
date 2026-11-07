import assert from "node:assert/strict";
import test from "node:test";
import { formatLast, pickLast } from "../extensions/mellum-last.ts";

// A schema-2 record with the three newer fields, shaped like the ac-demo Phase 1 run.
const NEW = {
	schema: 2,
	kind: "mode",
	version: "0.1.7",
	promptVersion: "v5",
	host: "interactive",
	activation: "one-shot",
	startedAt: "2026-10-12T15:20:00.000Z",
	endedAt: "2026-10-12T15:21:02.000Z",
	wallSeconds: 62,
	cwd: "/Users/p/ac-demo",
	model: "llamacpp/Mellum2.1-12B-A2.5B-Thinking",
	task: "Implement Phase 1 of specs/roadmap.md",
	requests: 14,
	usage: { input: 41200, cacheRead: 120300, output: 6100 },
	files: ["templates/base.html", "app.py"],
	edits: 2,
	filesMissingAtEnd: [],
	commands: [{ command: "uv run --frozen python -m pytest tests", failed: false, mutates: false }],
	lastCommand: "ok",
	finalReply: "Phase 1 is done.\nAll tests pass.",
	finalTurn: { stopReason: "stop", hadText: true, hadToolCall: false },
	toolCalls: { bash: 4, read: 5, write: 4, ls: 2, edit: 1 },
	toolErrors: 1,
	firstWriteSeconds: 31,
	nudges: 0,
	guardBlocks: 0,
	facts: { source: "agents-md", testCommand: "uv run --frozen python -m pytest tests", chars: 276 },
	server: { match: true, diffs: [] },
};
const line = (r) => JSON.stringify(r);
const row = (md, name) => md.split("\n").find((l) => l.startsWith(`| ${name} |`));

test("formatLast renders the header, the metric table, the command table and the reply", () => {
	const md = formatLast(NEW);
	assert.match(md.split("\n")[0], /^\*\*mellum last\*\*: Mellum Worker \(one-shot\), 2026-10-12 \d\d:\d\d, \/Users\/p\/ac-demo$/);
	assert.ok(md.includes("| Metric | Value |\n|---|---|"));
	assert.equal(row(md, "Task"), "| Task | Implement Phase 1 of specs/roadmap.md |");
	assert.equal(row(md, "Time"), "| Time | 62 s; first write at 31 s (50%) |");
	assert.equal(row(md, "Turns"), "| Turns | 14; ended with text (stop) |");
	assert.equal(row(md, "Tool calls"), "| Tool calls | 16: read 5, bash 4, write 4, ls 2, edit 1 |");
	assert.equal(row(md, "Tool errors"), "| Tool errors | 1 |");
	assert.equal(row(md, "Commands"), "| Commands | 1 run, 0 failed, last ok |");
	assert.equal(row(md, "Files"), "| Files | 2: templates/base.html, app.py |");
	assert.equal(row(md, "Tokens"), "| Tokens | input 41,200 · cache read 120,300 · output 6,100 |");
	assert.equal(row(md, "Facts"), "| Facts | agents-md, 276 chars |");
	assert.equal(row(md, "Server"), "| Server | settings match |");
	assert.equal(row(md, "Guards"), "| Guards | 0 nudges, 0 blocks |");
	assert.equal(row(md, "Versions"), "| Versions | mellum-worker 0.1.7 · prompt v5 · llamacpp/Mellum2.1-12B-A2.5B-Thinking |");
	assert.equal(row(md, "Missing"), undefined);
	assert.equal(row(md, "Changed files via bash"), undefined);
	assert.ok(md.includes("| Command | Result |\n|---|---|\n| `uv run --frozen python -m pytest tests` | ok |"));
	assert.ok(md.trimEnd().endsWith("> Phase 1 is done. All tests pass."));
});

test("formatLast shows dashes for an older record without the newer fields", () => {
	const { toolCalls, toolErrors, firstWriteSeconds, usage, facts, server, ...old } = NEW;
	const md = formatLast({ ...old, version: "0.1.6" });
	assert.equal(row(md, "Time"), "| Time | 62 s |");
	assert.equal(row(md, "Tool calls"), "| Tool calls | — |");
	assert.equal(row(md, "Tool errors"), "| Tool errors | — |");
	assert.equal(row(md, "Tokens"), "| Tokens | — |");
	assert.equal(row(md, "Facts"), "| Facts | — |");
	assert.equal(row(md, "Server"), "| Server | — |");
});

test("formatLast reports llama.cpp server liveness (no match key) instead of differs", () => {
	const up = formatLast({ ...NEW, server: { up: true, nCtx: 50176 } });
	assert.equal(row(up, "Server"), "| Server | up, ctx 50,176 |");
	const down = formatLast({ ...NEW, server: { up: false } });
	assert.equal(row(down, "Server"), "| Server | down |");
});

test("formatLast escapes pipes and newlines in cells, marks file-changing commands, and adds Missing", () => {
	const md = formatLast({
		...NEW,
		task: "fix a | b\nthen test",
		filesMissingAtEnd: ["tmp.py"],
		commands: [
			{ command: "grep -r x . | head", failed: true, mutates: false },
			{ command: "sed -i 's/a/b/' app.py", failed: false, mutates: true },
		],
		lastCommand: "ok",
	});
	assert.equal(row(md, "Task"), "| Task | fix a \\| b then test |");
	assert.equal(row(md, "Missing"), "| Missing | 1: tmp.py |");
	assert.equal(row(md, "Changed files via bash"), "| Changed files via bash | 1 command |");
	assert.equal(row(md, "Commands"), "| Commands | 2 run, 1 failed, last ok |");
	assert.ok(md.includes("| `grep -r x . \\| head` | failed |"));
	assert.ok(md.includes("| `sed -i 's/a/b/' app.py` | ok, changes files |"));
	for (const l of md.split("\n").filter((l) => l.startsWith("| "))) {
		assert.equal(l.replace(/\\\|/g, "").split("|").length, 4, `three pipes in: ${l}`);
	}
});

test("formatLast clips long values and lists at most 12 commands", () => {
	const commands = Array.from({ length: 15 }, (_, i) => ({ command: `echo ${i} ${"x".repeat(200)}`, failed: false, mutates: false }));
	const md = formatLast({ ...NEW, task: "t".repeat(500), commands });
	assert.ok(row(md, "Task").length < 260);
	const cmdRows = md.split("\n").filter((l) => l.startsWith("| `echo"));
	assert.equal(cmdRows.length, 12);
	assert.ok(cmdRows.every((l) => l.length < 180));
	assert.ok(md.includes("| … 3 more | |"));
});

test("pickLast takes the newest record at or under the directory, from every file, skipping bad lines", () => {
	const mode = [
		line({ ...NEW, endedAt: "2026-10-12T15:00:00.000Z", task: "older" }),
		"not json",
		line({ ...NEW, cwd: "/Users/p/other", endedAt: "2026-10-12T18:00:00.000Z", task: "elsewhere" }),
	].join("\n");
	const newest = [line({ ...NEW, cwd: "/Users/p/ac-demo/sub", endedAt: "2026-10-12T16:00:00.000Z", task: "newest" }), '{"task":"no schema"}'].join("\n");
	const r = pickLast([mode, undefined, newest], "/Users/p/ac-demo");
	assert.equal(r.record.task, "newest");
	assert.deepEqual(r.skipped, { bad: 1, old: 1 });
});

test("pickLast with nothing under the directory returns no record", () => {
	assert.equal(pickLast([line({ ...NEW, cwd: "/elsewhere" })], "/Users/p/ac-demo").record, undefined);
	assert.equal(pickLast([undefined], "/Users/p/ac-demo").record, undefined);
});

test("formatLast drops code fences and long rules from the quoted reply", () => {
	const md = formatLast({ ...NEW, finalReply: "Done.\nTest output:\n```\n======= test session starts =======\n1 passed\n```" });
	assert.ok(md.trimEnd().endsWith("> Done. Test output: === test session starts === 1 passed"), md.split("\n").pop());
});

test("formatLast keeps a cell whole when a value has a backslash before a pipe (grep alternation)", () => {
	const md = formatLast({ ...NEW, task: "find a\\|b", commands: [{ command: "grep 'a\\|b' x | wc -l", failed: false, mutates: false }] });
	for (const l of md.split("\n").filter((l) => l.startsWith("| "))) {
		// A pipe is a column break unless an odd number of backslashes precede it.
		const breaks = [...l.matchAll(/(\\*)\|/g)].filter((m) => m[1].length % 2 === 0).length;
		assert.equal(breaks, 3, `three column pipes in: ${l}`);
	}
	assert.ok(md.includes("| ok |"));
});

test("formatLast shows the run's full directory, skips an empty Missing row and a percentage without positive wall time", () => {
	const md = formatLast({ ...NEW, filesMissingAtEnd: [1, 2], wallSeconds: -5 });
	assert.match(md.split("\n")[0], /, \/Users\/p\/ac-demo$/);
	assert.equal(row(md, "Missing"), undefined);
	assert.equal(row(md, "Time"), "| Time | -5 s; first write at 31 s |");
});

test("pickLast compares endedAt as times, and on a tie the later line or file wins", () => {
	const a = line({ ...NEW, endedAt: "2026-10-12T15:00:00.500Z", task: "later by half a second" });
	const b = line({ ...NEW, endedAt: "2026-10-12T15:00:00Z", task: "earlier" });
	assert.equal(pickLast([`${b}\n${a}`], "/Users/p/ac-demo").record.task, "later by half a second");
	const m = line({ ...NEW, task: "mode" });
	const later = line({ ...NEW, task: "later" });
	assert.equal(pickLast([m, later], "/Users/p/ac-demo").record.task, "later");
});
