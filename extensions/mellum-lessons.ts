/**
 * mellum-lessons: the lesson track as data, for the /lesson tutor (mellum-lesson-tutor.ts).
 *
 * The lesson page is the only source: front matter, opening, picture, Overview, Paul's six
 * steps, the Run it yourself commands and the key points are parsed from
 * learn/lessons/<tier>/<slug>.md, so the site and the tutor cannot disagree. Pure: no Pi
 * imports, so node can test it.
 */
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { join } from "node:path";

export const STEPS = ["Problem", "Eval case", "Evidence of the problem", "Solution", "Validation", "Interpretation"] as const;
const TIERS = ["easy", "medium", "hard"];

export interface LessonEntry {
	number: string;
	title: string;
	tier: string;
	slug: string;
	file: string;
}

export interface Lesson {
	number: string;
	title: string;
	opening: string;
	image: string;
	alt: string;
	questions: string[];
	objectives: string[];
	steps: Record<string, string>;
	commands: string[];
	before?: string;
	after?: string;
	unit: string;
	keyPoints: string[];
}

// A Windows checkout (git core.autocrlf) gives the lessons CRLF line endings; every parser reads LF.
const lf = (text: string): string => text.replace(/\r\n/g, "\n");

const frontMatter = (raw: string): Record<string, string> => {
	const text = lf(raw);
	const block = text.match(/^---\n([\s\S]*?)\n---/);
	return Object.fromEntries((block?.[1] ?? "").split("\n").map((l) => l.match(/^(\w+): (.*)$/)).filter(Boolean).map((m) => [m![1], m![2].replace(/^(["'])(.*)\1$/, "$2")]));
};

/** Every lesson, in track order: Easy, Medium, Hard, each by number. */
export function lessonIndex(root: string): LessonEntry[] {
	const entries: LessonEntry[] = [];
	for (const tier of TIERS) {
		const dir = join(root, "learn", "lessons", tier);
		if (!existsSync(dir)) continue; // a tier with no lessons yet (they are being rebuilt)
		for (const name of readdirSync(dir).filter((f) => f.endsWith(".md") && f !== "index.md")) {
			const file = join(dir, name);
			const fm = frontMatter(readFileSync(file, "utf8"));
			entries.push({ number: fm.number, title: fm.title, tier, slug: name.replace(/\.md$/, ""), file });
		}
	}
	const start = join(root, "learn", "lessons", "start-here.md");
	if (existsSync(start)) {
		const fm = frontMatter(readFileSync(start, "utf8"));
		entries.push({ number: fm.number, title: fm.title, tier: "start", slug: "start-here", file: start });
	}
	const startDir = join(root, "learn", "lessons", "start");
	if (existsSync(startDir)) {
		for (const name of readdirSync(startDir).filter((f) => f.endsWith(".md") && f !== "index.md")) {
			const file = join(startDir, name);
			const fm = frontMatter(readFileSync(file, "utf8"));
			entries.push({ number: fm.number, title: fm.title, tier: "start", slug: name.replace(/\.md$/, ""), file });
		}
	}
	// The Start tier (S0, then the command lessons S1..) comes first, then Easy, Medium, Hard.
	const rank = (n: string) => n[0] === "S"
		? Number(n.slice(1))
		: 100 + TIERS.indexOf(TIERS.find((t) => t[0].toUpperCase() === n[0])!) * 100 + Number(n.slice(1));
	return entries.sort((a, b) => rank(a.number) - rank(b.number));
}

const bullets = (block: string): string[] => [...block.matchAll(/^ {4}- (.+)$/gm)].map((m) => m[1]);

/** The commands in the Run it yourself block, continuation lines joined. */
function commandsIn(section: string): string[] {
	const run = section.split("### Run it yourself")[1] ?? "";
	const out: string[] = [];
	for (const block of run.matchAll(/```bash\n([\s\S]*?)```/g)) {
		const joined = block[1].replace(/\\\n\s*/g, " ");
		out.push(...joined.split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#")));
	}
	return out;
}

export function parseLesson(raw: string): Lesson {
	const text = lf(raw);
	const fm = frontMatter(text);
	const body = text.replace(/^---\n[\s\S]*?\n---\n/, "");
	const h1 = body.match(/^# (\S+) · (.+)$/m);
	const afterH1 = body.slice((h1?.index ?? 0) + (h1?.[0].length ?? 0)).trimStart();
	const opening = afterH1.split(/\n\s*\n/)[0].replace(/\n/g, " ").trim();
	const image = body.match(/^!\[([^\]]+)\]\(([^)]+)\)\{ \.illustration \}$/m);
	const head = body.split(/^## /m)[0];
	const questions = bullets(head.split("**Questions**")[1]?.split("**Objectives**")[0] ?? "");
	const objectives = bullets(head.split("**Objectives**")[1] ?? "");
	const steps: Record<string, string> = {};
	const parts = body.split(/^## (.+)$/m);
	for (let i = 1; i < parts.length; i += 2) steps[parts[i].trim()] = parts[i + 1] ?? "";
	const commands = commandsIn(steps.Interpretation ?? "");
	if (steps.Interpretation) steps.Interpretation = steps.Interpretation.split("### Run it yourself")[0];
	const keyPoints = bullets(body.split('!!! success "Key points"')[1] ?? "");
	const unit = body.match(/^\*\*Remedy unit:\*\* (.+)$/m)?.[1] ?? "";
	const harness = commands.filter((c) => c.includes("harness.py") || c.includes("flow_run.py"));
	return {
		number: fm.number ?? h1?.[1] ?? "",
		title: fm.title ?? h1?.[2] ?? "",
		opening,
		image: image?.[2] ?? "",
		alt: image?.[1] ?? "",
		questions,
		objectives,
		steps,
		commands,
		before: harness[0],
		after: harness.length > 1 ? harness[1] : undefined,
		unit,
		keyPoints,
	};
}

export interface RunSummary {
	verdict: "PASS" | "FAIL" | "NONE";
	passed: number;
	total: number;
	lines: string[];
}

/** PASS or FAIL for a runs folder, and one line per session saying why. */
export function summariseRuns(dir: string): RunSummary {
	let names: string[] = [];
	try {
		names = readdirSync(dir).sort();
	} catch {
		return { verdict: "NONE", passed: 0, total: 0, lines: [] };
	}
	const lines: string[] = [];
	let passed = 0;
	let total = 0;
	for (const name of names) {
		let r: any;
		try {
			r = JSON.parse(readFileSync(join(dir, name, "run.json"), "utf8"));
		} catch {
			continue;
		}
		total += 1;
		const wall = `${Math.round(r.wall ?? 0)} s`;
		if (r.passed) {
			passed += 1;
			lines.push(`PASS  ${wall}`);
			continue;
		}
		const missed = (r.missing_checks ?? []).length;
		const why = r.output_tokens === 0
			? "no model answered (0 output tokens): is the model server running?"
			: r.stalled
			? `stalled on \`${r.stalled.command}\`${r.checks_ran ? "" : "; the checks never ran"}`
			: !r.checks_ran
				? "the checks never ran (a module they import is missing)"
				: missed
					? `${missed} hidden check${missed === 1 ? "" : "s"} missed: ${(r.missing_checks as string[]).map((c) => c.split("::").pop()).join(", ")}`
					: r.tests_passed === false
						? "the hidden tests failed"
						: r.record_failures?.length
							? `the record shows: ${r.record_failures.join("; ")}`
							: "the tests passed but lint or type checks failed";
		lines.push(`FAIL  ${wall}  ${why}`);
	}
	return { verdict: total === 0 ? "NONE" : passed === total ? "PASS" : "FAIL", passed, total, lines };
}

/** The pathology line of the remedy unit a lesson's Remedy unit line names, for the FAIL screen's
 * "why". Undefined when the line names no unit or the unit has no file. */
/**
 * The solution file a run produced — the newest run's root-level `.py` in its
 * workspace (the grader's `tests/` stay in a subdir, so they are never picked).
 * Lets a lesson show the code the fix wrote, not just PASS/FAIL.
 */
export function producedCode(runsDir: string): { name: string; text: string } | undefined {
	let runs: string[];
	try {
		runs = readdirSync(runsDir).sort();
	} catch {
		return undefined;
	}
	for (const run of runs.reverse()) {
		const ws = join(runsDir, run, "workspace");
		let names: string[];
		try {
			names = readdirSync(ws).filter((n) => n.endsWith(".py")).sort();
		} catch {
			continue;
		}
		if (names.length === 0) continue;
		try {
			return { name: names[0], text: readFileSync(join(ws, names[0]), "utf8") };
		} catch {
			continue;
		}
	}
	return undefined;
}

/** The remedy unit's own source, shown under a lesson's Solution step. `unit` is e.g.
 * `prompt/name-the-layout`; returns its path (for the reference) and the file's text. */
export function remedyCode(root: string, unit: string): { name: string; text: string } | undefined {
	if (!/^[a-z]+\/[a-z-]+$/.test(unit)) return undefined;
	const name = `remedies/${unit}.ts`;
	try {
		return { name, text: readFileSync(join(root, name), "utf8") };
	} catch {
		return undefined;
	}
}

export function unitPathology(root: string, unitLine: string): string | undefined {
	const unit = unitLine.match(/`([a-z]+\/[a-z-]+)`/)?.[1];
	const file = unit && join(root, "remedies", `${unit}.ts`);
	if (!file || !existsSync(file)) return undefined;
	return readFileSync(file, "utf8").match(/pathology:\s*"((?:[^"\\]|\\.)*)"/)?.[1];
}

/** The argv for a page command: one session unless `full`, into `runsDir`, on `profile` (the
 * model Pi is on) unless the line names its own. */
export function runArgv(command: string, runsDir: string, full: boolean, profile?: string): string[] {
	const argv = command.trim().split(/\s+/);
	const i = argv.indexOf("--repeat");
	if (!full) {
		if (i >= 0) argv[i + 1] = "1";
		else argv.push("--repeat", "1");
	}
	if (profile && !argv.includes("--profile")) argv.push("--profile", profile);
	return [...argv, "--runs-dir", runsDir];
}

/** A harness profile pinned to the model Pi is on: its provider from the agent dir's models.json,
 * with only that model, written to `outDir`. Undefined when the model is not in models.json (a
 * built-in provider), so the line keeps the harness's default profile. Credentials are not copied. */
export function sessionProfile(agentDir: string, model: { provider: string; id: string } | undefined, outDir: string): string | undefined {
	const file = join(agentDir, "models.json");
	if (!model || !existsSync(file)) return undefined;
	const provider = JSON.parse(readFileSync(file, "utf8")).providers?.[model.provider];
	const pinned = provider?.models?.find((m: { id: string }) => m.id === model.id);
	if (!pinned) return undefined;
	mkdirSync(outDir, { recursive: true });
	writeFileSync(join(outDir, "models.json"), JSON.stringify({ providers: { [model.provider]: { ...provider, models: [pinned] } } }, null, 2));
	return outDir;
}

/** The PNG copy of a lesson picture that the terminal draws (scripts/terminal-pictures.py). */
export function terminalPicture(root: string, image: string): string {
	const name = image.split("/").pop()!.replace(/\.webp$/, ".png");
	return join(root, "learn", "assets", "illustrations", "terminal", name);
}

/** Join the soft line breaks of Markdown wrapped at 80 columns, so the terminal can rewrap it to
 * its own width. Code blocks, tables and list starts are kept; a list item's continuation joins
 * its item. */
export function unwrap(md: string): string {
	const out: string[] = [];
	let fenced = false;
	for (const line of md.split("\n")) {
		if (/^\s*```/.test(line)) {
			fenced = !fenced;
			out.push(line);
			continue;
		}
		const prev = out.at(-1);
		const starts = /^\s*([-*] |\d+\. |\||#|>|!!!|\?\?\?)/.test(line) || line.trim() === "";
		const joinable = !fenced && prev !== undefined && prev.trim() !== "" && !/^\s*(```|\|)/.test(prev) && !starts;
		if (joinable) out[out.length - 1] = `${prev} ${line.trim()}`;
		else out.push(line);
	}
	return out.join("\n");
}

/** The suite folder a lesson's before line runs: --suites-dir (default learn/code/suites) / --suite. */
export function lessonSuite(root: string, command: string | undefined): string | undefined {
	if (!command || !command.includes("harness.py")) return undefined;
	const argv = command.trim().split(/\s+/);
	const at = (flag: string) => (argv.indexOf(flag) >= 0 ? argv[argv.indexOf(flag) + 1] : undefined);
	const suite = at("--suite");
	if (!suite) return undefined;
	return join(root, at("--suites-dir") ?? join("learn", "code", "suites"), suite);
}

/** A new, empty Pi session whose working directory is `cwd`, written into `store`. Switching to it
 * moves the running Pi into that folder: no second terminal. `version` is Pi's session version. */
export function sessionIn(cwd: string, version: number, store: string): string {
	mkdirSync(store, { recursive: true });
	const id = randomUUID();
	const timestamp = new Date().toISOString();
	const file = join(store, `${timestamp.replace(/[:.]/g, "-")}_${id}.jsonl`);
	writeFileSync(file, JSON.stringify({ type: "session", version, id, timestamp, cwd }) + "\n");
	return file;
}

/** Manual work happens in project/<lesson number>, never in the repository root. Resets that folder
 * to the lesson's starting files, writes the task to TASK.md, and adds a .pi/extensions shim so
 * /remedy and /lesson work when Pi moves there. Returns the folder. */
export function prepareProject(root: string, lesson: Pick<Lesson, "number" | "before">): string {
	const dir = join(root, "project", lesson.number);
	rmSync(dir, { recursive: true, force: true });
	mkdirSync(dir, { recursive: true });
	const suite = lessonSuite(root, lesson.before);
	if (suite && existsSync(join(suite, "base"))) cpSync(join(suite, "base"), dir, { recursive: true });
	let task = "";
	if (suite && existsSync(join(suite, "prompts"))) {
		task = readdirSync(join(suite, "prompts")).filter((f) => f.endsWith(".md")).sort()
			.map((f) => readFileSync(join(suite, "prompts", f), "utf8").trim()).join("\n\n") + "\n";
	} else if (suite && existsSync(join(suite, "task.md"))) {
		task = readFileSync(join(suite, "task.md"), "utf8");
	}
	// A command lesson (the Start tier) has no suite; give it a small task to try the worker on.
	if (!task && !suite) task = "Create `add.py` with a function `add(a, b)` that returns their sum, and a\ntest `test_add.py` that checks it. Run the whole test file.\n";
	// A suite task is deliberately terse — the detail lives in the project, as it would in real work —
	// so TASK.md points at where to read it: the specs folder and AGENTS.md (whichever the base ships).
	if (suite && task) {
		const refs: string[] = [];
		if (existsSync(join(dir, "specs", "roadmap.md"))) refs.push("Your instructions are in the specs folder: read specs/roadmap.md for this phase.");
		if (existsSync(join(dir, "AGENTS.md"))) refs.push("The test command and what not to do are in AGENTS.md.");
		if (refs.length) task = `${task.trimEnd()}\n\n${refs.join("\n")}\n`;
	}
	if (task) writeFileSync(join(dir, "TASK.md"), task);
	mkdirSync(join(dir, ".pi", "extensions"), { recursive: true });
	writeFileSync(join(dir, ".pi", "extensions", "remedies.ts"),
		`// /remedy for this lesson's project folder (written by /lesson).\nexport { default } from ${JSON.stringify(join(root, "extensions", "mellum-remedies.ts"))};\n`);
	writeFileSync(join(dir, ".pi", "extensions", "lessons.ts"),
		`// /lesson in this lesson's project folder (written by /lesson): /lesson back returns to the lesson.\nexport { default } from ${JSON.stringify(join(root, "extensions", "mellum-lesson-tutor.ts"))};\n`);
	writeFileSync(join(dir, ".pi", "extensions", "worker.ts"),
		`// /mellum for this lesson's project folder (written by /lesson): the worker switches load the model.\nexport { default } from ${JSON.stringify(join(root, "extensions", "mellum-worker.ts"))};\n`);
	return dir;
}

/** The lesson number of the project folder `cwd` is in, or undefined outside project/<number>. */
export function projectNumber(root: string, cwd: string): string | undefined {
	const base = join(root, "project") + "/";
	return cwd.startsWith(base) ? cwd.slice(base.length).split("/")[0] || undefined : undefined;
}

/** What to do in project/<number>, for the widget the tutor shows above Pi's editor (seen by you,
 * never sent to the model). Undefined outside a lesson's project folder. */
export function projectGuide(root: string, cwd: string): string[] | undefined {
	const number = projectNumber(root, cwd);
	const entry = number && lessonIndex(root).find((e) => e.number === number);
	if (!entry) return undefined;
	const text = readFileSync(entry.file, "utf8");
	// A command lesson (the Start tier beyond S0) pins the /mellum commands to try, not a remedy task.
	if (entry.tier === "start" && entry.number !== "S0") {
		const tryit = (frontMatter(text).tryit ?? "").split("|").map((s) => s.trim()).filter(Boolean);
		return [
			`${entry.number} · ${entry.title}: try it here in project/${entry.number}`,
			...tryit.map((s, i) => `${i + 1}. ${s}`),
			"`/lesson back` returns to the lesson · `/lesson clear` starts this folder over",
		];
	}
	const lesson = parseLesson(text);
	// A stand-in lesson (no model: its before/after are fake-pi through the real harness) is a
	// run-and-read loop, not ask-the-model: run the two lines in-session and read why each one did.
	if (lesson.before?.includes("--pi-binary")) {
		return [
			`${lesson.number} · ${lesson.title}: run it here in project/${lesson.number}`,
			"1. Run the before line: `/lesson before` → FAIL (the stand-in writes the wrong answer)",
			"2. Read why in the result and the run's `run.json`: passed, checks_ran, stalled",
			"3. Run the after line: `/lesson after` → PASS (the stand-in writes the right one)",
			"`/lesson back` returns to the lesson · `/lesson clear` starts this folder over",
		];
	}
	const unit = lesson.unit.match(/`([a-z]+\/[a-z-]+)`/)?.[1];
	const why = unitPathology(root, lesson.unit);
	const steps = [
		`${lesson.number} · ${lesson.title}: trying it by hand in project/${lesson.number}`,
		"1. Ask the model: `Do the task in TASK.md`",
		why ? `2. Watch its tool calls for this failure: ${why}` : "2. Watch its tool calls, then read what it built.",
		unit
			? `3. Then from scratch with the remedy: \`/lesson clear\`, then \`/remedy on ${unit}\`, and ask again.`
			: "3. Then from scratch: `/lesson clear`, and ask again.",
	];
	// The before/after arms run in-session, so the panel shows the FAIL→PASS comparison to run.
	if (lesson.before) steps.push(lesson.after
		? "4. Or compare the arms: `/lesson before` (fails) and `/lesson after` (passes with the remedy)"
		: "4. Or run the arm yourself: `/lesson before`");
	steps.push("`/lesson back` returns to the lesson where you left it · `/lesson clear` starts this folder over");
	return steps;
}

/** The widget outside a project folder: the lesson commands, one line each. */
export function lessonLegend(): string[] {
	return [
		"Welcome to the Small AI Learning Center",
		"`/start` opens your next lesson · `/lesson` picks any · `/lesson E1` opens one",
		"In a lesson: talk to the model, or run `/lesson before` and `/lesson after`",
		"`/lesson read` the prose · `/lesson back` out · `/lesson clear` reset · `/remedy` units · `/lesson clean` wipe",
	];
}

/** Paint for the widget: the theme's colours in Pi, plain marks in a test. */
export interface GuidePaint {
	title(text: string): string;
	step(text: string): string;
	code(text: string): string;
	dim(text: string): string;
	rule(text: string): string;
}

/** The widget's lines, styled: the first line a title, numbered steps with their number set off,
 * `backticked` commands as code, and the last line a dimmed footer under a rule. */
export function styleGuide(lines: string[], paint: GuidePaint, width: number): string[] {
	const code = (text: string) => text.replace(/`([^`]+)`/g, (_m, c) => paint.code(c));
	const [title, ...rest] = lines;
	const footer = rest.length > 1 ? rest.pop()! : undefined;
	const out = [paint.title(`▍ ${title}`)];
	for (const line of rest) {
		const step = line.match(/^(\d+\.)\s+(.*)$/);
		out.push(step ? `  ${paint.step(step[1])} ${code(step[2])}` : `  ${code(line)}`);
	}
	if (footer) out.push(paint.rule("─".repeat(Math.max(1, width))), `  ${paint.dim(footer.replace(/`/g, ""))}`);
	return out;
}

/** Remove every lesson's project folder. */
export function cleanProjects(root: string): void {
	rmSync(join(root, "project"), { recursive: true, force: true });
}
