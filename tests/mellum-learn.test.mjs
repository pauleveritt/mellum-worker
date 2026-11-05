import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import test from "node:test";
import { readProjectFacts } from "../extensions/mellum-facts.ts";
import { formatMerge, formatReport, isUnder, learn, learnFromTexts, mergeSuggestion, modeRunsFile, readRecords, recordFiles } from "../extensions/mellum-learn.ts";

const FIX = join(resolve(import.meta.dirname, ".."), "tests/fixtures/learn");
const text = (name) => readFileSync(join(FIX, name), "utf8");
const run = (name, over = {}) => {
	const { records, bad, old } = readRecords(text(`patterns/${name}.jsonl`));
	return learn(records, { cwd: "/home/user/proj", n: 100, skipped: { old, bad }, ...over });
};
const ids = (r) => r.patterns.map((p) => p.id);
const pat = (r, id) => r.patterns.find((p) => p.id === id);

const T1 = "uv run python -m pytest tests";

test("readRecords: bad lines, old lines, blank lines, a truncated last line", () => {
	const { records, bad, old } = readRecords(text("patterns/damaged.jsonl"));
	assert.equal(records.length, 2);
	assert.equal(old, 1);
	assert.equal(bad, 2); // "not json" and the truncated last line; the two blank lines are ignored
	assert.deepEqual(records.map((r) => r.kind), ["mode", "mode"]);
	const r = learn(records, { cwd: "/home/user/proj", n: 10, skipped: { old, bad } });
	assert.deepEqual(r.skipped, { old: 1, bad: 2 });
	assert.equal(r.runs, 2);
});

test("readRecords: JSON that is not an object is bad; schema below 2 is old", () => {
	const { records, bad, old } = readRecords('5\nnull\n[1]\n{"schema":1,"cwd":"/x"}\n{"schema":2,"cwd":"/x","endedAt":"2026-10-01T00:00:00Z"}\n');
	assert.equal(bad, 3);
	assert.equal(old, 1);
	assert.equal(records.length, 1);
});

test("test-thrash: fires in 3 of 6 runs with the median and the most frequent passing command", () => {
	const r = run("test-thrash");
	assert.deepEqual(ids(r), ["test-thrash"]);
	const p = pat(r, "test-thrash");
	assert.equal(p.count, 3);
	assert.equal(
		p.message,
		`Test command guessed wrong in 3 of 6 runs (median 2 commands before one passed). The command that passed: ${T1}`,
	);
	assert.deepEqual(p.bullets, [`Test command: ${T1}`]);
});

test("test-thrash: needs at least 2 runs (one run does not fire)", () => {
	const { records } = readRecords(text("patterns/test-thrash.jsonl"));
	const r = learn(records.slice(0, 1), { cwd: "/home/user/proj", n: 10 });
	assert.deepEqual(ids(r), []);
});

test("bent-project: files and commands become Do not values, never a Write only list", () => {
	const r = run("bent-project");
	assert.deepEqual(ids(r), ["bent-project"]);
	const p = pat(r, "bent-project");
	assert.equal(p.count, 3); // the sed on src/app.py, nested tests/conftest.py and uv sync run is a near-miss
	assert.equal(p.message, "Project bent to fit in 3 runs: conftest.py, pyproject.toml, src/__init__.py; uv add httpx");
	assert.deepEqual(p.bullets, ["Do not: install packages or add dependencies; add __init__.py, conftest.py, pytest.ini or setup.cfg files"]);
});

test("false-success: a failed or missing last command with a success claim; 'failed' and a passing last command do not", () => {
	const r = run("false-success");
	assert.deepEqual(ids(r), ["false-success"]);
	const p = pat(r, "false-success");
	assert.equal(p.count, 3);
	assert.equal(
		p.message,
		"Success claimed after a failed last command in 3 runs (2026-10-01, 2026-10-02, 2026-10-03). Run the tests yourself before trusting the reply.",
	);
	assert.deepEqual(p.bullets, []);
});

test("long-run: more than 30 requests fires, exactly 30 does not", () => {
	const r = run("long-run");
	assert.deepEqual(ids(r), ["long-run"]);
	const p = pat(r, "long-run");
	assert.equal(p.count, 2);
	assert.equal(p.message, "2 runs took more than 30 requests (max 45). Split the task: see README, Right-sizing.");
	assert.deepEqual(p.bullets, []);
});

test("servers: uvicorn, a trailing &, runserver and serve fire; observe.py and preserve.py do not", () => {
	const r = run("servers");
	assert.deepEqual(ids(r), ["servers"]);
	const p = pat(r, "servers");
	assert.equal(p.count, 3);
	assert.equal(p.message, "Mellum started a server in 3 runs.");
	assert.deepEqual(p.bullets, ["Do not: start servers"]);
});

test("drift: server.match false fires; null, true and absent do not", () => {
	const r = run("drift");
	assert.deepEqual(ids(r), ["drift"]);
	const p = pat(r, "drift");
	assert.equal(p.count, 2);
	assert.equal(p.message, "Server settings differed in 2 runs: turboquant_kv_enabled, max_context_window. Run /mellum check.");
	assert.deepEqual(p.bullets, []);
});

test("announce-stop: a text-only final turn without an ok last command; ok, a tool call and a missing finalTurn do not", () => {
	const r = run("announce-stop");
	assert.deepEqual(ids(r), ["announce-stop"]);
	const p = pat(r, "announce-stop");
	assert.equal(p.count, 2);
	assert.equal(p.message, "2 runs ended announcing a step without taking it.");
	assert.deepEqual(p.bullets, []);
});

test("patterns come in the table's order and the suggestion merges the bullets", () => {
	const all = ["test-thrash", "bent-project", "false-success", "long-run", "servers", "drift", "announce-stop"]
		.flatMap((n) => readRecords(text(`patterns/${n}.jsonl`)).records);
	const r = learn(all, { cwd: "/home/user/proj", n: 1000 });
	assert.deepEqual(ids(r), ["test-thrash", "bent-project", "false-success", "long-run", "servers", "drift", "announce-stop"]);
	// the Do not bullets share one label
	assert.deepEqual(r.suggestion, [
		`Test command: ${T1}`,
		"Do not: install packages or add dependencies; add __init__.py, conftest.py, pytest.ini or setup.cfg files; start servers",
	]);
});

test("a report with no bullets has an empty suggestion", () => {
	assert.deepEqual(run("long-run").suggestion, []);
});

test("n keeps the newest n records by endedAt", () => {
	const r = run("long-run", { n: 2 });
	// newest two of 31, 45, 30 requests are 45 and 30
	assert.equal(r.runs, 2);
	assert.equal(pat(r, "long-run").count, 1);
	assert.equal(pat(r, "long-run").message, "1 runs took more than 30 requests (max 45). Split the task: see README, Right-sizing.");
	assert.deepEqual(r.window, { from: "2026-10-02T10:01:00.000Z", to: "2026-10-03T10:01:00.000Z" });
});

test("window is null with no runs", () => {
	const r = run("long-run", { cwd: "/home/user/elsewhere" });
	assert.equal(r.runs, 0);
	assert.equal(r.window, null);
	assert.deepEqual(r.patterns, []);
});

test("cwd keeps records at or under it, path-segment aware", () => {
	const mk = (cwd) => ({ schema: 2, kind: "mode", cwd, endedAt: "2026-10-01T00:00:00.000Z", requests: 1 });
	const records = [
		mk("/home/user/ac-demo"),
		mk("/home/user/ac-demo/sub"),
		mk("/home/user/ac-demo-2"),
		mk("/home/user"),
	];
	assert.equal(learn(records, { cwd: "/home/user/ac-demo", n: 10 }).runs, 2);
	assert.equal(learn(records, { cwd: "/home/user/ac-demo/", n: 10 }).runs, 2);
	assert.equal(learn(records, { cwd: "/home/user", n: 10 }).runs, 4);
});

test("no pattern: formatReport says the run count and nothing to fix", () => {
	const { records } = readRecords(text("patterns/clean.jsonl"));
	const r = learn(records, { cwd: "/home/user/proj", n: 10 });
	assert.deepEqual(r.patterns, []);
	const out = formatReport(r, "/home/user/proj");
	assert.match(out, /1 run/);
	assert.match(out, /nothing to fix/);
});

test("formatReport lists the patterns, the skipped counts and the suggested section", () => {
	const r = run("servers");
	const out = formatReport(r, "/home/user/proj");
	assert.match(out, /Mellum started a server in 3 runs\./);
	assert.match(out, /## Mellum/);
	assert.match(out, /- Do not: start servers/);
	assert.doesNotMatch(out, /nothing to fix/);
	const d = formatReport(run("damaged"), "/home/user/proj");
	assert.match(d, /1 old/);
	assert.match(d, /2 bad/);
});

test("paul-runs: ac-demo yields exactly what the rules give for his fixture (computed)", () => {
	const { records, bad, old } = readRecords(text("paul-runs.jsonl"));
	assert.equal(bad, 0);
	const lines = text("paul-runs.jsonl").split("\n").filter(Boolean).map((l) => JSON.parse(l));
	assert.equal(old, lines.filter((l) => l.schema === undefined).length);
	const mine = lines.filter((l) => l.schema === 2 && l.cwd === "/home/user/ac-demo");
	const r = learn(records, { cwd: "/home/user/ac-demo", n: 10, skipped: { old, bad } });
	assert.equal(r.runs, mine.length);
	assert.deepEqual(r.skipped, { old, bad });
	// R7: test-thrash needs at least 2 runs; the fixture has one schema-2 ac-demo run, so it cannot fire
	assert.ok(mine.length < 2);
	assert.equal(pat(r, "test-thrash"), undefined);
	// what does fire is computed from the data: his run started a server (a uvicorn command and a trailing &)
	const serverRuns = mine.filter((l) => l.commands.some((c) => /&\s*$|\buvicorn\b|\bserve\b|runserver/.test(c.command)));
	assert.equal(serverRuns.length, 1);
	assert.deepEqual(ids(r), ["servers"]);
	assert.equal(pat(r, "servers").message, `Mellum started a server in ${serverRuns.length} runs.`);
	// its last command passed, so no success claim or announcement fires
	assert.equal(mine[0].lastCommand, "ok");
	// the suggested section is the one servers remedy
	assert.deepEqual(r.suggestion, ["Do not: start servers"]);
});

test("paul-runs: the scratch runs (worktree cwd) fire false-success and announce-stop, computed", () => {
	const { records, old, bad } = readRecords(text("paul-runs.jsonl"));
	const lines = text("paul-runs.jsonl").split("\n").filter(Boolean).map((l) => JSON.parse(l));
	const scratch = lines.filter((l) => l.schema === 2 && l.cwd === "/home/user/scratch");
	const r = learn(records, { cwd: "/home/user/scratch", n: 10, skipped: { old, bad } });
	assert.equal(r.runs, scratch.length);
	const claimed = scratch.filter((l) => l.lastCommand !== "ok" && /\b(pass(es|ed)?|success(ful(ly)?)?|complete[d]?|done)\b/i.test(l.finalReply));
	const stopped = scratch.filter((l) => l.finalTurn.hadText && !l.finalTurn.hadToolCall && l.lastCommand !== "ok");
	assert.deepEqual(ids(r), ["false-success", "announce-stop"]);
	assert.equal(pat(r, "false-success").count, claimed.length);
	assert.equal(pat(r, "announce-stop").count, stopped.length);
	// the home directory is anonymised in the fixture
	assert.doesNotMatch(text("paul-runs.jsonl"), /pauleveritt/);
});

// ---- the suggestion merged into AGENTS.md (spec section 3, "The suggestion and the write") ----

const TC = "Test command: uv run python -m pytest tests";
const DN = "Do not: start servers";

test("mergeSuggestion: no AGENTS.md gives a new file with the section", () => {
	const m = mergeSuggestion(undefined, [TC, DN]);
	assert.equal(m.text, `# Project\n\n## Mellum\n\n- ${TC}\n- ${DN}\n`);
	assert.deepEqual(m.added, [TC, DN]);
	assert.deepEqual(m.conflicts, []);
});

test("mergeSuggestion: a file without the section gets it after one blank line, earlier bytes unchanged", () => {
	const before = "# Proj\n\nSome text.\n";
	const m = mergeSuggestion(before, [DN]);
	assert.equal(m.text, `${before}\n## Mellum\n\n- ${DN}\n`);
	assert.deepEqual(m.added, [DN]);
	// already ending in a blank line: no second one
	assert.equal(mergeSuggestion("# Proj\n\n", [DN]).text, `# Proj\n\n## Mellum\n\n- ${DN}\n`);
});

test("mergeSuggestion: a file without a trailing newline gets one before the new section", () => {
	assert.equal(mergeSuggestion("# Proj\n\nSome text.", [DN]).text, `# Proj\n\nSome text.\n\n## Mellum\n\n- ${DN}\n`);
});

test("mergeSuggestion: a ## Mellum between two sections takes the missing bullets after its last one; every other byte is identical", () => {
	const prefix = "# Proj\n\n## Setup\n\nRun it.\n\n## Mellum\n\nSome words.\n\n- Test command: uv run python -m pytest tests\n- Write only: src/,\n  tests/\n";
	const suffix = "\n## Notes\n\n- keep me\n";
	const m = mergeSuggestion(prefix + suffix, [TC, DN]);
	assert.deepEqual(m.added, [DN]);
	assert.deepEqual(m.conflicts, []);
	assert.ok(m.text.startsWith(prefix), "prefix identical");
	assert.ok(m.text.endsWith(suffix), "suffix identical");
	assert.equal(m.text.slice(prefix.length, m.text.length - suffix.length), `- ${DN}\n`);
});

test("mergeSuggestion: a ## Mellum ending the file without a trailing newline gets one, then the bullets", () => {
	const before = "# Proj\n\n## Mellum\n\n- Write only: src/";
	const m = mergeSuggestion(before, [DN]);
	assert.ok(m.text.startsWith(before));
	assert.equal(m.text, `${before}\n- ${DN}\n`);
});

test("mergeSuggestion: a ## Mellum with no bullets takes them after a blank line, before the next heading", () => {
	const m = mergeSuggestion("## Mellum\n\n## Other\n", [DN]);
	assert.equal(m.text, `## Mellum\n\n- ${DN}\n\n## Other\n`);
});

test("mergeSuggestion: CRLF files keep CRLF", () => {
	const before = "# Proj\r\n\r\n## Mellum\r\n\r\n- Write only: src/\r\n\r\n## Notes\r\n";
	const m = mergeSuggestion(before, [DN]);
	assert.equal(m.text, `# Proj\r\n\r\n## Mellum\r\n\r\n- Write only: src/\r\n- ${DN}\r\n\r\n## Notes\r\n`);
});

test("mergeSuggestion: a different existing value is a conflict, never rewritten; an identical bullet is not added", () => {
	const before = "## Mellum\n\n- test command: npm test\n- Do not: start servers\n";
	const m = mergeSuggestion(before, [TC, DN]);
	assert.equal(m.text, before, "file unchanged");
	assert.deepEqual(m.added, []);
	assert.deepEqual(m.conflicts, ["your test command: npm test; runs passed with: uv run python -m pytest tests"]);
});

test("mergeSuggestion: nothing to suggest leaves the text as it was", () => {
	assert.deepEqual(mergeSuggestion("# P\n", []), { text: "# P\n", added: [], conflicts: [], chars: 0 });
});

test("formatMerge: conflicts, what is missing, or nothing to add", () => {
	assert.equal(formatMerge({ added: [], conflicts: ["your Test command: a; runs passed with: b"] }, [TC]), "\nKept as written in AGENTS.md:\n- your Test command: a; runs passed with: b");
	// some lines missing: formatReport's Suggested block shows them, formatMerge adds nothing
	assert.equal(formatMerge({ added: [DN], conflicts: [] }, [TC, DN]), "");
	assert.equal(formatMerge({ added: [TC, DN], conflicts: [] }, [TC, DN]), "");
	assert.equal(formatMerge({ added: [], conflicts: [] }, [TC]), "\nAGENTS.md already has these lines.");
	assert.equal(formatMerge({ added: [], conflicts: [] }, []), "");
});

test("recordFiles: MELLUM_MODE_RUNS (0 or empty: none, ~ expanded) or the default", () => {
	assert.deepEqual(recordFiles({}, "/h"), [join("/h", ".pi", "agent", "mellum-mode-runs.jsonl")]);
	assert.deepEqual(recordFiles({ MELLUM_MODE_RUNS: "0" }, "/h"), []);
	assert.deepEqual(recordFiles({ MELLUM_MODE_RUNS: "" }, "/h"), []);
	assert.deepEqual(recordFiles({ MELLUM_MODE_RUNS: "~/r.jsonl" }, "/h"), ["/h/r.jsonl"]);
	assert.equal(modeRunsFile({ MELLUM_MODE_RUNS: "/x/r.jsonl" }, "/h"), "/x/r.jsonl");
});

test("learnFromTexts: sums the skipped counts over every file; a missing file is no records", () => {
	const r = learnFromTexts([text("patterns/damaged.jsonl"), undefined, text("patterns/damaged.jsonl")], { cwd: "/home/user/proj", n: 10 });
	assert.deepEqual(r.skipped, { old: 2, bad: 4 });
	assert.equal(r.runs, 4);
	assert.equal(learnFromTexts([undefined], { cwd: "/x", n: 10 }).runs, 0);
});

// A ## Mellum section whose bullets total 590 characters: 10 short of the facts cap.
const NEAR_CAP = `## Mellum\n\n- Note: ${"x".repeat(584)}\n`;
const factsOf = (md) => readProjectFacts("/p", { read: (f) => (f === join("/p", "AGENTS.md") ? md : undefined) }, {});

test("mergeSuggestion: chars is the merged section's bullet total, counted as readProjectFacts counts it", () => {
	const m = mergeSuggestion("# P\n\n## Mellum\n\n- Write only: src/\n", [TC, DN]);
	assert.equal(m.chars, factsOf(m.text).chars);
	assert.equal(m.chars, "Write only: src/".length + TC.length + DN.length);
	assert.equal(mergeSuggestion(undefined, [DN]).chars, DN.length);
});

test("mergeSuggestion near the cap: chars goes past 600, which readProjectFacts would ignore; formatMerge says so", () => {
	assert.equal(factsOf(NEAR_CAP).chars, 590);
	const m = mergeSuggestion(NEAR_CAP, [DN]);
	assert.equal(m.chars, 590 + DN.length);
	assert.ok(factsOf(m.text).warning, "the merged section would be ignored by Mode");
	assert.equal(formatMerge(m, [DN]), "\nAdding these would take the section past 600 characters; Mode would ignore it.");
	// within the cap, no such line
	assert.doesNotMatch(formatMerge(mergeSuggestion(undefined, [DN]), [DN]), /600/);
});

// ---- final review fix wave ----

test("readRecords: valid JSON of the wrong shape never makes learn throw; malformed entries and fields are dropped", () => {
	const lines = text("patterns/wrong-shape.jsonl").split("\n").filter(Boolean);
	for (const [i, line] of lines.entries()) {
		assert.doesNotThrow(() => {
			const { records } = readRecords(line);
			formatReport(learn(records, { cwd: "/home/user/proj", n: 10 }), "/home/user/proj");
		}, `line ${i + 1}`);
	}
	const { records, bad, old } = readRecords(text("patterns/wrong-shape.jsonl"));
	assert.equal(records.length, 8);
	assert.deepEqual({ bad, old }, { bad: 0, old: 0 });
	// commands: entries without a string command are dropped, the rest kept
	assert.deepEqual(records[0].commands.map((c) => c.command), ["uvicorn app:app"]);
	assert.deepEqual(records[1].commands, []);
	// files: strings only; endedAt: a string or dropped; server.diffs: an array of objects with a key
	assert.deepEqual(records[2].files, ["src/a.py"]);
	assert.equal(records[3].endedAt, undefined);
	assert.deepEqual(records[4].server, { match: false, diffs: [] });
	assert.deepEqual(records[5].server.diffs.map((d) => d.key), ["turboquant_kv_enabled"]);
	// requests a number, finalReply a string, finalTurn an object, lastCommand a string, or dropped
	for (const k of ["requests", "finalReply", "finalTurn", "lastCommand"]) assert.equal(records[6][k], undefined, k);
	// non-array commands and files read as none; a non-object server is dropped
	assert.deepEqual([records[7].commands, records[7].files, records[7].server, records[7].finalTurn], [[], [], undefined, undefined]);
	const r = learn(records, { cwd: "/home/user/proj", n: 10 });
	assert.deepEqual(ids(r), ["servers", "drift"]);
	assert.equal(pat(r, "servers").count, 1);
	assert.equal(pat(r, "drift").message, "Server settings differed in 2 runs: turboquant_kv_enabled. Run /mellum check.");
	assert.doesNotThrow(() => formatReport(r, "/home/user/proj"));
});

test("bent-project: each kind of bend becomes its own Do not value, and nothing else", () => {
	const mk = (files, commands = []) => ({ schema: 2, kind: "mode", cwd: "/home/user/proj", endedAt: "2026-10-01T00:00:00.000Z", files, commands });
	const bullets = (files, commands) => pat(learn([mk(files, commands)], { cwd: "/home/user/proj", n: 10 }), "bent-project").bullets;
	assert.deepEqual(bullets(["pyproject.toml", "src/a.py"]), ["Do not: install packages or add dependencies"]);
	assert.deepEqual(bullets(["src/a.py"], [{ command: "uv add httpx", failed: false }]), ["Do not: install packages or add dependencies"]);
	assert.deepEqual(bullets(["pytest.ini", "lib/b.py"]), ["Do not: add __init__.py, conftest.py, pytest.ini or setup.cfg files"]);
	assert.deepEqual(bullets(["src/__init__.py"]), ["Do not: add __init__.py, conftest.py, pytest.ini or setup.cfg files"]);
	assert.deepEqual(bullets(["__init__.py"]), ["Do not: add __init__.py, conftest.py, pytest.ini or setup.cfg files"]);
	assert.ok(!bullets(["app.py", "pytest.ini"]).join().includes("project root"), "never forbids root files in general");
	assert.deepEqual(bullets(["/tmp/out.txt", "uv.lock"]), ["Do not: install packages or add dependencies"]);
});

test("formatReport: one run is '1 run'", () => {
	const r = run("long-run", { n: 1 });
	assert.match(formatReport(r, "/home/user/proj"), /^mellum learn: 1 run in \/home\/user\/proj \(/);
	assert.match(formatReport(run("long-run"), "/home/user/proj"), /^mellum learn: 3 runs in /);
});

const DN2 = "Do not: install packages or add dependencies; start servers";

test("mergeSuggestion: Do not is additive; one new bullet with only the missing values, no conflict, other bytes kept", () => {
	const prefix = "# P\n\n## Mellum\n\n- Do not: start servers\n";
	const suffix = "\n## Notes\n";
	const m = mergeSuggestion(prefix + suffix, [DN2]);
	assert.deepEqual(m.added, ["Do not: install packages or add dependencies"]);
	assert.deepEqual(m.conflicts, []);
	assert.equal(m.text, `${prefix}- Do not: install packages or add dependencies\n${suffix}`);
	// values split on ';', trimmed, case-insensitive, over every existing Do not bullet
	const all = mergeSuggestion("## Mellum\n\n- do not: Start Servers\n- Do not:  INSTALL packages or add dependencies ; other\n", [DN2]);
	assert.deepEqual([all.added, all.conflicts], [[], []]);
	// the facts cap still applies to the added bullet
	const near = mergeSuggestion(`## Mellum\n\n- Note: ${"x".repeat(584)}\n- Do not: start servers\n`, [DN2]);
	assert.deepEqual(near.added, ["Do not: install packages or add dependencies"]);
	assert.ok(near.chars > 600);
});

test("mergeSuggestion: 'runs passed with:' only for Test command; other labels say 'runs suggest:'", () => {
	const m = mergeSuggestion("## Mellum\n\n- Write only: src/\n- Test command: npm test\n", ["Test command: uv run pytest", "Write only: app.py, src/"]);
	assert.deepEqual(m.conflicts, ["your Test command: npm test; runs passed with: uv run pytest", "your Write only: src/; runs suggest: app.py, src/"]);
	assert.deepEqual(m.added, []);
});

test("formatReport: the Suggested block shows only the lines that would be added, and is omitted when none would", () => {
	const r = learn(
		["bent-project", "servers"].flatMap((n) => readRecords(text(`patterns/${n}.jsonl`)).records),
		{ cwd: "/home/user/proj", n: 100 },
	);
	const m = mergeSuggestion("## Mellum\n\n- Do not: start servers\n- Write only: app.py, lib/, src/, tests/\n", r.suggestion);
	const out = formatReport(r, "/home/user/proj", m.added) + formatMerge(m, r.suggestion);
	assert.match(out, /Suggested for AGENTS\.md:\n\n## Mellum\n- Do not: install packages or add dependencies; add __init__\.py, conftest\.py, pytest\.ini or setup\.cfg files$/);
	assert.doesNotMatch(out, /start servers/);
	const none = mergeSuggestion("## Mellum\n\n- Do not: start servers; install packages or add dependencies; add __init__.py, conftest.py, pytest.ini or setup.cfg files\n- Write only: app.py, lib/, src/, tests/\n", r.suggestion);
	const outNone = formatReport(r, "/home/user/proj", none.added) + formatMerge(none, r.suggestion);
	assert.doesNotMatch(outNone, /Suggested/);
	assert.doesNotMatch(outNone, /Kept as written/);
	assert.match(outNone, /\nAGENTS\.md already has these lines\.$/);
});

test("the README's learn example is the real output on its fixture", () => {
	const readme = readFileSync(join(resolve(import.meta.dirname, ".."), "README.md"), "utf8");
	const shown = readme.split("`tests/fixtures/learn/patterns/bent-project.jsonl`:\n\n```\n")[1].split("```")[0];
	const r = learnFromTexts([text("patterns/bent-project.jsonl")], { cwd: "/home/user/proj", n: 10 });
	const m = mergeSuggestion(undefined, r.suggestion);
	assert.equal(shown, formatReport(r, "/home/user/proj", m.added) + formatMerge(m, r.suggestion) + "\n");
});

// On Windows a run's cwd is a backslash path, and a fixture or record may mix in "/".
test("isUnder matches Windows paths with either separator", { skip: process.platform !== "win32" }, () => {
	assert.equal(isUnder(String.raw`C:\p\proj`, String.raw`C:\p\proj`), true);
	assert.equal(isUnder(String.raw`C:\p\proj\sub`, String.raw`C:\p\proj`), true);
	assert.equal(isUnder(String.raw`C:\p\proj/sub`, String.raw`C:\p\proj\ `.trim()), true);
	assert.equal(isUnder(String.raw`C:\p\proj-2`, String.raw`C:\p\proj`), false);
	assert.equal(isUnder(String.raw`C:\p`, String.raw`C:\p\proj`), false);
});
