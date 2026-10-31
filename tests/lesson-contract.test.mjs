import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

// The lesson contract (docs/superpowers/specs/2026-10-29-uniform-lessons-design.md): one concept,
// a before line on the lesson's own challenge that fails, an after line one remedy away that
// passes. This checks the shape; the lesson check under evals/ proves the FAIL -> PASS.
const ROOT = new URL("..", import.meta.url).pathname;
const tutor = () => import("../extensions/mellum-lessons.ts");

// Lessons that do not conform yet, by slug. The list may only shrink: a lesson leaves it when it
// conforms, and the cycle (LC.28) closes when it is empty.
const PENDING = new Set([
	"searching", "creating-files",
	"too-many-tools",
	"tell-it-how-to-test", "a-short-prompt", "nudge-an-empty-turn",
	"run-long-commands-safely", "look-it-up",
	"check-before-finishing",
	"know-when-to-stop", "keep-a-plan", "build-a-suite",
	"plan-examine-code", "frozen-gates-and-checkpoints",
	"dont-trust-the-self-exit", "best-of-n", "build-a-tool", "build-a-remedy",
]);

// S0 is the one lesson without a model: stand-ins play it, on a fixture suite.
const EXEMPT = new Set(["start-here"]);
const SHARED_SUITES = new Set(["easy", "medium", "hard"]);

/** argv after the script name, as [flag, value] pairs and bare flags, order kept. */
function options(command) {
	const argv = command.trim().split(/\s+/);
	const at = argv.findIndex((a) => /(harness|flow_run)\.py$/.test(a));
	const rest = argv.slice(at + 1);
	if (rest[0] === "run" || rest[0] === "qualify") rest.shift();
	const out = [];
	for (let i = 0; i < rest.length; i++) {
		if (rest[i].startsWith("--") && rest[i + 1] !== undefined && !rest[i + 1].startsWith("--")) out.push([rest[i], rest[++i]]);
		else out.push([rest[i], undefined]);
	}
	return out;
}

function unitMeta(unit) {
	const file = join(ROOT, "remedies", `${unit}.ts`);
	if (!existsSync(file)) return undefined;
	return readFileSync(file, "utf8").match(/lesson:\s*"([^"]*)"/)?.[1];
}

function flowSwitches() {
	const file = join(ROOT, "remedies", "flow.json");
	return existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : {};
}

/** The after line's one addition to the before line: a unit appended to --remedy, a learner's
 * file (--extension, --grader), or a flow switch. Undefined when it is not exactly one. */
function remedyOf(b, a) {
	const list = (line) => (line.find(([f]) => f === "--remedy")?.[1] ?? "").split(",").filter(Boolean);
	const same = (x, y) => JSON.stringify(x) === JSON.stringify(y);
	const strip = (line) => line.filter(([f]) => f !== "--remedy");
	const bl = list(b), al = list(a);
	if (same(strip(b), strip(a)) && al.length === bl.length + 1 && same(al.slice(0, -1), bl))
		return { kind: "unit", name: al.at(-1) };
	if (same(bl, al) && a.length === b.length + 1 && same(a.slice(0, b.length), b)) {
		const [flag, value] = a.at(-1);
		if (flag === "--extension" || flag === "--grader") return { kind: "file", name: value ?? "" };
		return { kind: "switch", name: flag };
	}
	return undefined;
}

/** Why a lesson breaks the contract, or [] when it conforms. */
export function contractProblems(lesson, slug) {
	const problems = [];
	const { before, after } = lesson;
	if (!before || !after) return ["needs a before line and an after line"];
	const b = options(before), a = options(after);
	for (const [name, line] of [["before", b], ["after", a]]) {
		const suite = line.find(([f]) => f === "--suite")?.[1];
		if (suite !== slug) problems.push(`${name} runs --suite ${suite}, not its own challenge ${slug}`);
		if (SHARED_SUITES.has(suite)) problems.push(`${name} runs the shared suite ${suite}`);
		if (line.some(([, v]) => v?.includes("preset:"))) problems.push(`${name} uses a preset`);
	}
	if (!existsSync(join(ROOT, "learn", "challenges", slug))) problems.push(`no challenge at learn/challenges/${slug}`);
	const remedy = remedyOf(b, a);
	if (!remedy) problems.push("the after line is not the before line plus exactly one remedy");
	else if (remedy.kind === "unit" && unitMeta(remedy.name) !== lesson.number)
		problems.push(`${remedy.name}'s meta.lesson is not ${lesson.number}`);
	else if (remedy.kind === "switch" && flowSwitches()[remedy.name]?.lesson !== lesson.number)
		problems.push(`${remedy.name} has no remedies/flow.json entry for ${lesson.number}`);
	if (remedy && !lesson.unit.includes(remedy.name.replace(/^--/, "")))
		problems.push(`the Remedy unit line does not name ${remedy.name}`);
	return problems;
}

test("every lesson outside PENDING meets the lesson contract", async () => {
	const { lessonIndex, parseLesson } = await tutor();
	for (const entry of lessonIndex(ROOT)) {
		if (EXEMPT.has(entry.slug) || PENDING.has(entry.slug)) continue;
		const problems = contractProblems(parseLesson(readFileSync(entry.file, "utf8")), entry.slug);
		assert.deepEqual(problems, [], `${entry.number} ${entry.slug}`);
	}
});

test("PENDING only shrinks: a listed lesson that conforms, or no longer exists, must leave it", async () => {
	const { lessonIndex, parseLesson } = await tutor();
	const slugs = new Map(lessonIndex(ROOT).map((e) => [e.slug, e]));
	for (const slug of PENDING) {
		const entry = slugs.get(slug);
		assert.ok(entry, `${slug} is not in the track; remove it from PENDING`);
		const problems = contractProblems(parseLesson(readFileSync(entry.file, "utf8")), slug);
		assert.notDeepEqual(problems, [], `${slug} conforms; remove it from PENDING`);
	}
});

test("no remedy is the remedy of two lessons", async () => {
	const { lessonIndex, parseLesson } = await tutor();
	const seen = new Map();
	for (const entry of lessonIndex(ROOT)) {
		if (EXEMPT.has(entry.slug) || PENDING.has(entry.slug)) continue;
		const l = parseLesson(readFileSync(entry.file, "utf8"));
		const name = remedyOf(options(l.before), options(l.after)).name;
		assert.ok(!seen.has(name), `${entry.number} and ${seen.get(name)} share ${name}`);
		seen.set(name, entry.number);
	}
});

test("the contract checker refuses a shared suite, a preset and a two-unit step, and passes a clean pair", () => {
	const line = (rest) => `uv run python learn/code/harness.py run --suites-dir learn/challenges ${rest} --repeat 3`;
	const lesson = (before, after, unit = "**Remedy unit:** `guard/block-foreground-server`") =>
		({ number: "E4", before, after, unit });
	const r = "guard/break-repeat-loops,guard/stay-in-workspace,guard/refuse-whole-file-rewrite";
	assert.deepEqual(contractProblems(lesson(line(`--suite running-commands --remedy ${r}`),
		line(`--suite running-commands --remedy ${r},guard/block-foreground-server`)), "running-commands")
		.filter((p) => !p.includes("meta.lesson")), []);
	assert.ok(contractProblems(lesson(line("--suite easy"), line("--suite easy --remedy guard/block-foreground-server")), "running-commands")
		.some((p) => p.includes("shared suite")));
	assert.ok(contractProblems(lesson(line("--suite running-commands --remedy preset:easy"),
		line("--suite running-commands --remedy preset:easy,guard/cap-turns")), "running-commands")
		.some((p) => p.includes("preset")));
	assert.ok(contractProblems(lesson(line("--suite running-commands"),
		line("--suite running-commands --remedy guard/cap-turns,guard/block-foreground-server")), "running-commands")
		.some((p) => p.includes("exactly one remedy")));
	assert.deepEqual(contractProblems({ number: "E4", before: undefined, after: undefined, unit: "" }, "x"),
		["needs a before line and an after line"]);
});
