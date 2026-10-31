import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const tutor = () => import("../extensions/mellum-lessons.ts");
const ROOT = new URL("..", import.meta.url).pathname;

test("the track lists Start Here, then every lesson in order: Easy, Medium, Hard, by number", async () => {
	const { lessonIndex } = await tutor();
	const ids = lessonIndex(ROOT).map((l) => l.number);
	const pages = ["easy", "medium", "hard"].flatMap((t) =>
		readdirSync(join(ROOT, "learn/lessons", t)).filter((f) => f.endsWith(".md") && f !== "index.md"));
	assert.equal(ids.length, pages.length + 1);
	assert.equal(ids[0], "S0");
	const key = (n) => "EMH".indexOf(n[0]) * 100 + Number(n.slice(1));
	assert.deepEqual(ids.slice(1), [...ids.slice(1)].sort((a, b) => key(a) - key(b)));
	assert.ok(ids.slice(1).every((n) => /^[EMH]\d+$/.test(n)), ids.join(" "));
});

test("every lesson page parses into what the walk-through shows", async () => {
	const { lessonIndex, parseLesson } = await tutor();
	for (const entry of lessonIndex(ROOT)) {
		const l = parseLesson(readFileSync(entry.file, "utf8"));
		assert.equal(l.number, entry.number);
		assert.ok(l.title && l.opening, `${l.number}: title/opening`);
		assert.match(l.image, /^(\.\.\/)+assets\/illustrations\/[a-z0-9-]+\.webp$/, `${l.number}: image`);
		assert.ok(l.alt.length >= 20, `${l.number}: alt`);
		assert.ok(l.questions.length && l.objectives.length, `${l.number}: overview`);
		for (const step of ["Problem", "Eval case", "Evidence of the problem", "Solution", "Validation", "Interpretation"])
			assert.ok(l.steps[step]?.trim(), `${l.number}: ${step}`);
		assert.ok(l.keyPoints.length >= 1, `${l.number}: key points`);
		assert.ok(l.commands.length >= 1, `${l.number}: commands`);
	}
});

test("a lesson with a before and an after line exposes both", async () => {
	const { parseLesson } = await tutor();
	const l = parseLesson(readFileSync(join(ROOT, "learn/lessons/easy/reasoning-as-text.md"), "utf8"));
	assert.match(l.before, /--suite reasoning-as-text --repeat 1/);
	assert.doesNotMatch(l.before, /--remedy/);
	assert.match(l.after, /--suite reasoning-as-text --remedy context\/repair-think-tags --repeat 1/);
	assert.match(l.unit, /context\/repair-think-tags/);
});

test("a run is summarised from its run.json files: passes, and why each failure failed", async () => {
	const { summariseRuns } = await tutor();
	const dir = mkdtempSync(join(tmpdir(), "runs-"));
	const write = (name, record) => { mkdirSync(join(dir, name)); writeFileSync(join(dir, name, "run.json"), JSON.stringify(record)); };
	write("a", { passed: true, checks_ran: true, stalled: null, missing_checks: [], wall: 120 });
	write("b", { passed: false, checks_ran: false, stalled: { command: "uv run python app.py" }, missing_checks: ["x", "y"], wall: 130 });
	write("c", { passed: false, checks_ran: true, stalled: null, missing_checks: ["grader_tests/test_challenge.py::test_items_lists_both"], wall: 300 });
	const s = summariseRuns(dir);
	assert.equal(s.verdict, "FAIL");
	assert.equal(s.passed, 1);
	assert.equal(s.total, 3);
	assert.deepEqual(s.lines, [
		"PASS  120 s",
		"FAIL  130 s  stalled on `uv run python app.py`; the checks never ran",
		"FAIL  300 s  1 hidden check missed: test_items_lists_both",
	]);
	const all = mkdtempSync(join(tmpdir(), "runs-"));
	mkdirSync(join(all, "a")); writeFileSync(join(all, "a", "run.json"), JSON.stringify({ passed: true, checks_ran: true, missing_checks: [], wall: 90 }));
	assert.equal(summariseRuns(all).verdict, "PASS");
});

test("a quick run is one session; the full run keeps the page's n", async () => {
	const { runArgv } = await tutor();
	const cmd = "uv run python learn/code/harness.py run --suite easy --arm bare --remedy guard/break-repeat-loops --repeat 3 --grade";
	const quick = runArgv(cmd, "/tmp/r", false);
	assert.equal(quick[quick.indexOf("--repeat") + 1], "1");
	assert.equal(quick[quick.indexOf("--runs-dir") + 1], "/tmp/r");
	const full = runArgv(cmd, "/tmp/r", true);
	assert.equal(full[full.indexOf("--repeat") + 1], "3");
});

test("every lesson picture has a PNG copy for the terminal (Kitty draws PNG only)", async () => {
	const { lessonIndex, parseLesson, terminalPicture } = await tutor();
	const { existsSync } = await import("node:fs");
	for (const entry of lessonIndex(ROOT)) {
		const png = terminalPicture(ROOT, parseLesson(readFileSync(entry.file, "utf8")).image);
		assert.ok(png.endsWith(".png") && existsSync(png), `${entry.number}: ${png}`);
	}
});

test("soft line breaks are joined for the terminal; code, lists and tables are kept", async () => {
	const { unwrap } = await tutor();
	const md = "One line\nwraps here.\n\n- a list\n- item\n\n```ts\nconst a = 1;\nconst b = 2;\n```\n\n| a | b |\n| --- | --- |\n| 1 | 2 |";
	assert.equal(unwrap(md), "One line wraps here.\n\n- a list\n- item\n\n```ts\nconst a = 1;\nconst b = 2;\n```\n\n| a | b |\n| --- | --- |\n| 1 | 2 |");
	assert.equal(unwrap("- a long item\n  that wraps\n- next"), "- a long item that wraps\n- next");
});

test("a session in which no model answered says so, instead of blaming the checks", async () => {
	const { summariseRuns } = await tutor();
	const dir = mkdtempSync(join(tmpdir(), "runs-"));
	mkdirSync(join(dir, "a"));
	writeFileSync(join(dir, "a", "run.json"), JSON.stringify({ passed: false, checks_ran: false, missing_checks: ["x"], wall: 14, requests: 0, output_tokens: 0 }));
	assert.match(summariseRuns(dir).lines[0], /no model answered/);
});

test("failed hidden tests are named as such, even when no check IDs are listed", async () => {
	const { summariseRuns } = await tutor();
	const dir = mkdtempSync(join(tmpdir(), "runs-"));
	mkdirSync(join(dir, "a"));
	writeFileSync(join(dir, "a", "run.json"), JSON.stringify({ passed: false, tests_passed: false, quality_ok: true, checks_ran: true, missing_checks: [], wall: 1 }));
	assert.match(summariseRuns(dir).lines[0], /the hidden tests failed/);
	mkdirSync(join(dir, "b"));
	writeFileSync(join(dir, "b", "run.json"), JSON.stringify({ passed: false, tests_passed: true, quality_ok: false, checks_ran: true, missing_checks: [], wall: 1 }));
	assert.match(summariseRuns(dir).lines[1], /lint or type checks failed/);
});

test("Start Here runs in seconds with no model: its before fails and its after passes", async () => {
	const { parseLesson } = await tutor();
	const l = parseLesson(readFileSync(join(ROOT, "learn/lessons/start-here.md"), "utf8"));
	assert.match(l.before, /--pi-binary learn\/code\/tests\/fixtures\/fake-pi-wrong\.sh/);
	assert.match(l.after, /--pi-binary learn\/code\/tests\/fixtures\/fake-pi\.sh/);
});

// Manual work happens in project/<lesson number>, never in the repository root: easy to find,
// easy to clean up.
test("prepareProject sets up project/<number> with the lesson's starting files, task and /remedy shim", async () => {
	const { prepareProject, parseLesson } = await tutor();
	const root = mkdtempSync(join(tmpdir(), "repo-"));
	const suite = join(root, "learn/code/suites/demo");
	mkdirSync(join(suite, "base"), { recursive: true });
	mkdirSync(join(suite, "prompts"), { recursive: true });
	writeFileSync(join(suite, "base", "pyproject.toml"), "[project]\nname='d'\n");
	writeFileSync(join(suite, "prompts", "01.md"), "Build it.\n");
	writeFileSync(join(suite, "prompts", "02.md"), "Then test it.\n");
	const lesson = { number: "E6", before: "uv run python learn/code/harness.py run --suite demo --repeat 3" };
	const dir = prepareProject(root, lesson);
	assert.equal(dir, join(root, "project", "E6"));
	assert.equal(readFileSync(join(dir, "pyproject.toml"), "utf8"), "[project]\nname='d'\n");
	assert.equal(readFileSync(join(dir, "TASK.md"), "utf8"), "Build it.\n\nThen test it.\n");
	assert.match(readFileSync(join(dir, ".pi", "extensions", "remedies.ts"), "utf8"), /extensions\/mellum-remedies\.ts/);
	assert.match(readFileSync(join(dir, ".pi", "extensions", "lessons.ts"), "utf8"), /extensions\/mellum-lesson-tutor\.ts/);
	assert.equal(existsSync(join(dir, ".pi", "extensions", "think-tags.ts")), false, "the repair is a unit there: /remedy on context/repair-think-tags");
	assert.match(readFileSync(join(ROOT, ".pi", "extensions", "think-tags.ts"), "utf8"), /extensions\/mellum-think-tags\.ts/);
	writeFileSync(join(dir, "stray.py"), "x = 1\n");
	prepareProject(root, lesson);
	assert.equal(existsSync(join(dir, "stray.py")), false, "a second prepare starts fresh");
});

test("a lesson's suites folder comes from --suites-dir when the page gives one", async () => {
	const { lessonSuite } = await tutor();
	assert.deepEqual(lessonSuite("/r", "harness.py run --suites-dir learn/challenges --suite e6 --repeat 3"), "/r/learn/challenges/e6");
	assert.deepEqual(lessonSuite("/r", "harness.py run --suite easy --repeat 3"), "/r/learn/code/suites/easy");
	assert.equal(lessonSuite("/r", "pi -p hello"), undefined);
});

test("cleanProjects removes project/ and nothing else", async () => {
	const { cleanProjects } = await tutor();
	const root = mkdtempSync(join(tmpdir(), "repo-"));
	mkdirSync(join(root, "project", "E6"), { recursive: true });
	writeFileSync(join(root, "keep.md"), "x");
	cleanProjects(root);
	assert.equal(existsSync(join(root, "project")), false);
	assert.equal(existsSync(join(root, "keep.md")), true);
});

test("a lesson run uses the model Pi is on: runArgv adds --profile, unless the line names one", async () => {
	const { runArgv } = await tutor();
	const cmd = "uv run python learn/code/harness.py run --suite easy --repeat 3";
	const argv = runArgv(cmd, "/tmp/r", false, "/tmp/p");
	assert.equal(argv[argv.indexOf("--profile") + 1], "/tmp/p");
	const own = runArgv(`${cmd} --profile mine`, "/tmp/r", false, "/tmp/p");
	assert.equal(own.filter((a) => a === "--profile").length, 1);
	assert.equal(own[own.indexOf("--profile") + 1], "mine");
	assert.ok(!runArgv(cmd, "/tmp/r", false).includes("--profile"));
});

test("sessionProfile writes a profile pinned to Pi's current provider and model", async () => {
	const { sessionProfile } = await tutor();
	const agent = mkdtempSync(join(tmpdir(), "agent-"));
	writeFileSync(join(agent, "models.json"), JSON.stringify({ providers: {
		other: { baseUrl: "http://x/v1", models: [{ id: "a" }] },
		lan: { baseUrl: "http://192.0.2.1/v1", apiKey: "not-needed", models: [{ id: "skip" }, { id: "mellum" }] },
	} }));
	const out = mkdtempSync(join(tmpdir(), "profile-"));
	assert.equal(sessionProfile(agent, { provider: "lan", id: "mellum" }, out), out);
	const written = JSON.parse(readFileSync(join(out, "models.json"), "utf8"));
	assert.deepEqual(Object.keys(written.providers), ["lan"]);
	assert.deepEqual(written.providers.lan.models.map((m) => m.id), ["mellum"]);
	assert.equal(written.providers.lan.baseUrl, "http://192.0.2.1/v1");
	assert.equal(sessionProfile(agent, { provider: "anthropic", id: "x" }, mkdtempSync(join(tmpdir(), "p-"))), undefined);
	assert.equal(sessionProfile(join(agent, "missing"), { provider: "lan", id: "mellum" }, out), undefined);
	assert.equal(sessionProfile(agent, undefined, out), undefined);
});

test("the FAIL screen's why: a lesson's remedy unit gives its pathology line", async () => {
	const { unitPathology } = await tutor();
	assert.match(unitPathology(ROOT, "**Remedy unit:** `guard/block-foreground-server`; apply it with --remedy"),
		/foreground and the session hangs/);
	assert.equal(unitPathology(ROOT, "**Remedy unit:** none: you write it"), undefined);
	assert.equal(unitPathology(ROOT, "`guard/no-such-unit`"), undefined);
});

test("sessionIn writes an empty Pi session whose working directory is the folder, so /lesson can move Pi there", async () => {
	const { sessionIn } = await tutor();
	const dir = mkdtempSync(join(tmpdir(), "project-"));
	const store = join(dir, ".pi", "sessions");
	const file = sessionIn(dir, 3, store);
	assert.ok(file.startsWith(store) && file.endsWith(".jsonl"), file);
	const lines = readFileSync(file, "utf8").trim().split("\n");
	assert.equal(lines.length, 1);
	const header = JSON.parse(lines[0]);
	assert.equal(header.type, "session");
	assert.equal(header.version, 3);
	assert.equal(header.cwd, dir);
	assert.match(header.id, /^[0-9a-f-]{36}$/);
	assert.notEqual(sessionIn(dir, 3, store), file, "each call is a fresh session");
});

test("in project/<number>, the tutor's guide says what to do, step by step, and how to get back", async () => {
	const { projectGuide, projectNumber } = await tutor();
	const lines = projectGuide(ROOT, join(ROOT, "project", "E1"));
	const text = lines.join("\n");
	assert.match(lines[0], /E1 · Reasoning Returned as Text/);
	for (const t of ["Do the task in TASK.md", "returns reasoning as", "/lesson clear", "/remedy on context/repair-think-tags", "/lesson back"])
		assert.ok(text.includes(t), `guide lacks ${t}`);
	assert.equal(projectNumber(ROOT, join(ROOT, "project", "E4", "app")), "E4");
	assert.equal(projectNumber(ROOT, ROOT), undefined);
	assert.equal(projectGuide(ROOT, ROOT), undefined);
	assert.equal(projectGuide(ROOT, join(ROOT, "project", "Z9")), undefined);
});

test("outside a project folder the widget is a legend of the lesson commands", async () => {
	const { lessonLegend } = await tutor();
	const text = lessonLegend().join("\n");
	for (const t of ["/lesson", "/lesson E1", "/remedy", "/lesson clear", "/lesson back", "/lesson clean"])
		assert.ok(text.includes(t), `legend lacks ${t}`);
});

test("the widget is styled: a title, numbered steps, commands as code, a dimmed footer under a rule", async () => {
	const { projectGuide, styleGuide } = await tutor();
	const paint = { title: (s) => `<T>${s}</T>`, step: (s) => `<S>${s}</S>`, code: (s) => `<C>${s}</C>`, dim: (s) => `<D>${s}</D>`, rule: (s) => `<R>${s.length}</R>` };
	const out = styleGuide(projectGuide(ROOT, join(ROOT, "project", "E1")), paint, 40);
	assert.match(out[0], /^<T>▍ E1 · Reasoning Returned as Text/);
	assert.ok(out.some((l) => l.includes("<S>1.</S>") && l.includes("<C>Do the task in TASK.md</C>")), out.join("\n"));
	assert.ok(out.some((l) => l.includes("<C>/lesson clear</C>")));
	assert.equal(out.at(-2), "<R>40</R>");
	assert.match(out.at(-1), /^\s*<D>/);
	assert.ok(!out.join("").includes("`"), "backticks are styling marks, never shown");
});

test("a failure in the record is named on the FAIL screen", async () => {
	const { summariseRuns } = await tutor();
	const dir = mkdtempSync(join(tmpdir(), "runs-"));
	mkdirSync(join(dir, "a"));
	writeFileSync(join(dir, "a", "run.json"), JSON.stringify({ passed: false, tests_passed: true, checks_ran: true, missing_checks: [],
		record_failures: ["reasoning_as_text is 10 (at most 0)"], wall: 60, output_tokens: 900 }));
	assert.match(summariseRuns(dir).lines[0], /the record shows: reasoning_as_text is 10 \(at most 0\)/);
});
