import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { readRecords } from "../extensions/mellum-learn.ts";

// The CLI never touches the network here: MELLUM_CHECK_FIXTURES makes it read the three
// GET responses from a directory, and HOME is a temp dir holding the host's config.
const ROOT = resolve(import.meta.dirname, "..");
const FIX = join(ROOT, "tests/fixtures/check");
const SCRIPT = join(ROOT, "scripts/mellum.mjs");
const version = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")).version;

const temp = (prefix) => mkdtempSync(join(tmpdir(), prefix));
// A path as it sits inside a JSON string, and as a literal in a RegExp: a Windows path's
// backslashes must be escaped in both.
const inJson = (p) => JSON.stringify(p).slice(1, -1);
const re = (p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// os.tmpdir() reads TMPDIR on POSIX and TEMP/TMP on Windows.
const tmpEnv = (dir) => ({ TMPDIR: dir, TEMP: dir, TMP: dir });
const copy = (from, to) => {
	mkdirSync(dirname(to), { recursive: true });
	copyFileSync(from, to);
};

// A fixtures dir with the given props fixture as props.json, beside health and the model list.
function fixtures(props) {
	const dir = temp("mellum-cli-fix-");
	copy(join(FIX, "health.json"), join(dir, "health.json"));
	copy(join(FIX, "v1-models.json"), join(dir, "v1-models.json"));
	copy(join(FIX, props), join(dir, "props.json"));
	return dir;
}

function home() {
	const dir = temp("mellum-cli-home-");
	copy(join(FIX, "pi-models.json"), join(dir, ".pi/agent/models.json"));
	return dir;
}

function run(args, { props = "props.json", script = SCRIPT, env = {} } = {}) {
	return spawnSync(process.execPath, [script, ...args], {
		encoding: "utf8",
		env: { ...process.env, HOME: home(), MELLUM_CHECK_FIXTURES: fixtures(props), ...env },
	});
}

test("check --json on the matching fixtures exits 0 with parseable findings and no fail", () => {
	const r = run(["check", "--json"]);
	assert.equal(r.status, 0, r.stderr);
	const out = JSON.parse(r.stdout);
	assert.equal(out.host, "pi");
	assert.equal(out.baseUrl, "http://127.0.0.1:8001/v1");
	assert.ok(Array.isArray(out.findings) && out.findings.length > 0);
	assert.deepEqual(out.findings.filter((f) => f.level === "fail"), []);
	assert.equal(out.findings.find((f) => f.id === "server").level, "ok");
	assert.equal(out.findings.find((f) => f.id === "model").level, "ok");
	assert.equal(out.findings.find((f) => f.id === "context").level, "ok");
});

test("check --json on a low context window exits 1 and reports the context fail with a relaunch fix, no PUT", () => {
	const r = run(["check", "--json"], { props: "props-low.json" });
	assert.equal(r.status, 1, r.stderr);
	const context = JSON.parse(r.stdout).findings.find((f) => f.id === "context");
	assert.equal(context.level, "fail");
	assert.match(context.message, /below the measured 50000/);
	assert.match(context.fix, /relaunch/);
	assert.doesNotMatch(context.fix, /curl -X PUT/);
});

test("check without --json prints the findings as text, fails first", () => {
	const r = run(["check"], { props: "props-low.json" });
	assert.equal(r.status, 1);
	assert.match(r.stdout, /^FAIL context: context window 32768 is below the measured 50000/);
	assert.match(r.stdout, /checks ok\n?$/);
});

test("a missing fixture file reads as an unreachable server", () => {
	const dir = temp("mellum-cli-empty-");
	const r = run(["check", "--json"], { env: { MELLUM_CHECK_FIXTURES: dir } });
	assert.equal(r.status, 1);
	const server = JSON.parse(r.stdout).findings.find((f) => f.id === "server");
	assert.equal(server.level, "fail");
	assert.match(server.message, /ENOENT/);
});

test("usage errors exit 2: no command, an unknown command, an unknown host", () => {
	for (const args of [[], ["frobnicate"], ["check", "--host", "vim"]]) {
		const r = run(args);
		assert.equal(r.status, 2, `${args.join(" ")}: ${r.stdout}${r.stderr}`);
		assert.match(r.stderr, /usage: node .*mellum\.mjs check/);
	}
});

test("installed under node_modules, the CLI runs from a mirror in the temp dir", () => {
	const pkg = join(temp("mellum-cli-nm-"), "node_modules", "mellum-worker");
	const files = [
		"package.json",
		"scripts/mellum.mjs",
		"templates/llama-model-settings.json",
		...readdirSync(join(ROOT, "extensions")).filter((f) => f.endsWith(".ts")).map((f) => `extensions/${f}`),
	];
	for (const f of files) copy(join(ROOT, f), join(pkg, f));
	const tmp = temp("mellum-cli-tmp-");
	const r = run(["check", "--json"], { script: join(pkg, "scripts/mellum.mjs"), env: tmpEnv(tmp) });
	assert.equal(r.status, 0, r.stderr);
	assert.equal(JSON.parse(r.stdout).host, "pi");
	assert.ok(existsSync(join(tmp, `mellum-worker-${version}`, "extensions", "mellum-check.ts")), "mirror written under the temp dir");
	assert.ok(existsSync(join(tmp, `mellum-worker-${version}`, "templates", "llama-model-settings.json")), "the llama settings template is mirrored");
	const cwd = project("servers");
	const l = learnRun(["learn", "--json", "--file", cwd.runs], { cwd: cwd.dir, script: join(pkg, "scripts/mellum.mjs"), env: tmpEnv(tmp) });
	assert.equal(l.status, 0, l.stderr);
	assert.deepEqual(JSON.parse(l.stdout).suggestion, ["Do not: start servers"]);
	assert.ok(existsSync(join(tmp, `mellum-worker-${version}`, "extensions", "mellum-learn.ts")), "learn ran from the mirror");
});

// ---- learn: prints only, never writes AGENTS.md ----

const LEARN = join(ROOT, "tests/fixtures/learn");

// A temp project dir (its real path, as process.cwd() reports it) and a runs file holding the
// given pattern fixture's records moved into that dir.
function project(pattern) {
	const dir = realpathSync(temp("mellum-cli-proj-"));
	const runs = join(temp("mellum-cli-runs-"), "runs.jsonl");
	writeFileSync(runs, readFileSync(join(LEARN, "patterns", `${pattern}.jsonl`), "utf8").replaceAll("/home/user/proj", inJson(dir)));
	return { dir, runs };
}

function learnRun(args, { cwd, script = SCRIPT, env = {} } = {}) {
	return spawnSync(process.execPath, [script, ...args], {
		cwd,
		encoding: "utf8",
		env: { ...process.env, HOME: temp("mellum-cli-home-"), MELLUM_MODE_RUNS: "0", ...env },
	});
}

test("learn --file paul-runs.jsonl --n 10 prints the report and never creates AGENTS.md", () => {
	const dir = realpathSync(temp("mellum-cli-proj-"));
	const r = learnRun(["learn", "--file", join(LEARN, "paul-runs.jsonl"), "--n", "10"], { cwd: dir });
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, new RegExp(`^mellum learn: 0 runs in ${re(dir)}\\nSkipped \\d+ old and 0 bad lines\\.\\nnothing to fix\\n$`));
	assert.equal(existsSync(join(dir, "AGENTS.md")), false);
});

test("learn prints the patterns and the suggestion, and a conflict with AGENTS.md, which it leaves alone", () => {
	const p = project("test-thrash");
	const agents = "## Mellum\n\n- Test command: npm test\n";
	writeFileSync(join(p.dir, "AGENTS.md"), agents);
	const r = learnRun(["learn", "--file", p.runs], { cwd: p.dir });
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /Test command guessed wrong in 3 of 6 runs/);
	// the only suggested line conflicts, so nothing would be added and no Suggested block prints
	assert.doesNotMatch(r.stdout, /Suggested for AGENTS\.md/);
	assert.match(r.stdout, /- your Test command: npm test; runs passed with: uv run python -m pytest tests/);
	assert.equal(readFileSync(join(p.dir, "AGENTS.md"), "utf8"), agents);
});

test("learn --json parses, with the report, the lines it would add and the conflicts; still writes nothing", () => {
	const p = project("servers");
	const r = learnRun(["learn", "--json", "--file", p.runs, "--n", "2"], { cwd: p.dir });
	assert.equal(r.status, 0, r.stderr);
	const out = JSON.parse(r.stdout);
	assert.equal(out.cwd, p.dir);
	assert.equal(out.runs, 2);
	assert.deepEqual(out.patterns.map((x) => x.id), ["servers"]);
	assert.deepEqual(out.added, ["Do not: start servers"]);
	assert.deepEqual(out.conflicts, []);
	assert.equal(existsSync(join(p.dir, "AGENTS.md")), false);
});

test("learn near the 600-character facts cap says so, in text and in JSON", () => {
	const p = project("servers");
	writeFileSync(join(p.dir, "AGENTS.md"), `## Mellum\n\n- Note: ${"x".repeat(584)}\n`);
	const text = learnRun(["learn", "--file", p.runs], { cwd: p.dir });
	assert.match(text.stdout, /\nAdding these would take the section past 600 characters; Mode would ignore it\.\n$/);
	const json = JSON.parse(learnRun(["learn", "--json", "--file", p.runs], { cwd: p.dir }).stdout);
	assert.equal(json.chars, 590 + "Do not: start servers".length);
});

test("learn usage errors exit 2: --n not a whole number above 0, a missing --file, an unknown flag", () => {
	const dir = realpathSync(temp("mellum-cli-proj-"));
	for (const args of [["learn", "--n", "0"], ["learn", "--n", "ten"], ["learn", "--n"], ["learn", "--file", join(dir, "nope.jsonl")], ["learn", "--file"], ["learn", "--file", "--json"], ["learn", "--host", "pi"]]) {
		const r = learnRun(args, { cwd: dir });
		assert.equal(r.status, 2, `${args.join(" ")}: ${r.stdout}${r.stderr}`);
		assert.match(r.stderr, /usage: node [\s\S]*mellum\.mjs learn \[--n 10\]/);
	}
});

test("learn --json: suggestion holds only the lines that would be added (a Do not value AGENTS.md has is left out)", () => {
	const p = project("servers");
	writeFileSync(join(p.dir, "AGENTS.md"), "## Mellum\n\n- Do not: start servers\n");
	const all = JSON.parse(learnRun(["learn", "--json", "--file", p.runs], { cwd: p.dir }).stdout);
	assert.deepEqual(all.suggestion, []);
	assert.deepEqual(all.added, []);
	assert.deepEqual(all.conflicts, []);
	const none = learnRun(["learn", "--file", p.runs], { cwd: p.dir });
	assert.doesNotMatch(none.stdout, /Suggested/);
	assert.match(none.stdout, /AGENTS\.md already has these lines\.\n$/);
});

test("last --file prints the newest run under the directory as a Markdown table", () => {
	const p = project("servers");
	const r = learnRun(["last", "--file", p.runs], { cwd: p.dir });
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /^\*\*mellum last\*\*: Mellum Worker/);
	assert.match(r.stdout, /\| Metric \| Value \|\n\|---\|---\|/);
	const newest = readRecords(readFileSync(p.runs, "utf8")).records.sort((a, b) => b.endedAt.localeCompare(a.endedAt))[0];
	assert.ok(r.stdout.includes(`| Task | ${newest.task.replace(/\|/g, "\\|")} |`), r.stdout);
});

test("last --json prints the record itself", () => {
	const p = project("servers");
	const r = learnRun(["last", "--json", "--file", p.runs], { cwd: p.dir });
	assert.equal(r.status, 0, r.stderr);
	const rec = JSON.parse(r.stdout);
	assert.equal(rec.schema, 2);
	assert.equal(rec.cwd.startsWith(p.dir), true);
});

test("last with no runs under the directory, or with recording off, exits 1 and says why", () => {
	const p = project("servers");
	const elsewhere = realpathSync(temp("mellum-cli-elsewhere-"));
	const none = learnRun(["last", "--file", p.runs], { cwd: elsewhere });
	assert.equal(none.status, 1);
	assert.match(none.stderr, new RegExp(`no Mellum runs recorded under ${re(elsewhere)}`));
	const off = learnRun(["last"], { cwd: p.dir, env: { MELLUM_MODE_RUNS: "0" } });
	assert.equal(off.status, 1);
	assert.match(off.stderr, /run records are off/);
});

test("last usage errors exit 2: --n is learn's, and --file needs an existing path", () => {
	const p = project("servers");
	for (const args of [["last", "--n", "3"], ["last", "--file", join(p.dir, "nope.jsonl")], ["last", "--file"]]) {
		const r = learnRun(args, { cwd: p.dir });
		assert.equal(r.status, 2, `${args.join(" ")}: ${r.stderr}`);
		assert.match(r.stderr, /mellum\.mjs last \[--file <jsonl>\] \[--json\]/);
	}
});
