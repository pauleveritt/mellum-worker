/**
 * mellum-lesson-tutor: /lesson, the course inside Pi.
 *
 *   /lesson          pick a lesson (finished ones are ticked; the next one is first)
 *   /lesson E3       open lesson E3 — hands-on, in project/E3, with the lesson panel pinned on top
 *   /lesson before   run the open lesson's before line in-session; /lesson after runs the after line
 *   /lesson read E3  the prose deck for E3 (the opt-in slideshow), one screen per step
 *   /lesson back     leave the project folder, back to the repository
 *
 * A lesson opens into its project folder with a live panel at the top (setHeader): the banner, what
 * to do, and the before/after runs as they finish (summarised from each session's run.json). The
 * prompt below stays yours. The lesson page is the only source (see mellum-lessons.ts).
 */
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { CURRENT_SESSION_VERSION, getMarkdownTheme } from "@earendil-works/pi-coding-agent";
import { Image, Key, Markdown, matchesKey, truncateToWidth, wrapTextWithAnsi } from "@earendil-works/pi-tui";
import { cleanProjects, lessonIndex, type Lesson, type LessonEntry, parseLesson, lessonLegend, prepareProject, projectGuide, projectNumber, producedCode, runArgv, styleGuide, sessionIn, sessionProfile, STEPS, summariseRuns, terminalPicture, unitPathology, unwrap } from "./mellum-lessons.ts";

const HERE = dirname(fileURLToPath(import.meta.url));

/** The repository root: the nearest folder above the session's cwd (or this file) with lessons. */
function findRoot(cwd: string): string | undefined {
	for (const start of [cwd, HERE]) {
		let dir = start;
		for (let i = 0; i < 8; i++) {
			if (existsSync(join(dir, "learn", "lessons", "easy"))) return dir;
			const up = dirname(dir);
			if (up === dir) break;
			dir = up;
		}
	}
	return undefined;
}

const agentDir = () => process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent");
const progressFile = () => join(agentDir(), "mellum-lessons.json");

/** Progress: the lessons finished, and the step each lesson was left on. */
function loadProgress(): { done: string[]; at: Record<string, number> } {
	try {
		const p = JSON.parse(readFileSync(progressFile(), "utf8"));
		return { done: p.done ?? [], at: p.at ?? {} };
	} catch {
		return { done: [], at: {} };
	}
}

function saveProgress(update: (p: { done: string[]; at: Record<string, number> }) => void): void {
	const p = loadProgress();
	update(p);
	try {
		mkdirSync(dirname(progressFile()), { recursive: true });
		writeFileSync(progressFile(), JSON.stringify(p, null, 2) + "\n");
	} catch {
		// Progress is a convenience; never fail a lesson over it.
	}
}

const loadDone = (): Set<string> => new Set(loadProgress().done);
const markDone = (number: string) => saveProgress((p) => { if (!p.done.includes(number)) p.done.push(number); });

interface RunState {
	label: string;
	started: number;
	child?: ChildProcess;
	lines: string[];
	verdict?: string;
	runsDir?: string;
}

/** Strip the badge lines and the remedy/check lines the step screens show in their own way. */
const tidy = (md: string) => unwrap(md.replace(/^\*\*Badge:\*\*.*$/gm, "").replace(/\n{3,}/g, "\n\n").trim());

/** Walk one lesson. Resolves "next" to go on to the next lesson, or "leave". */
function walk(ctx: any, root: string, lesson: Lesson, entry: LessonEntry, total: { index: number; count: number }, startPage = 0): Promise<"next" | "leave" | "project"> {
	return ctx.ui.custom((tui: any, theme: any, _kb: unknown, done: (r: "next" | "leave" | "project") => void) => {
		const pages = ["Cover", ...STEPS, "Key points"];
		let page = Math.min(Math.max(startPage, 0), pages.length - 1);
		let cached: string[] | undefined;
		const runs: Record<string, RunState> = {};
		const md = (text: string) => new Markdown(text, 1, 0, getMarkdownTheme());
		const list = (items: string[]) => items.map((i) => `- ${i}`).join("\n");
		const pngPath = terminalPicture(root, lesson.image);
		const picture = existsSync(pngPath)
			? new Image(readFileSync(pngPath).toString("base64"), "image/png", { fallbackColor: (s: string) => theme.fg("muted", s) },
				{ maxWidthCells: 64, maxHeightCells: 14, filename: lesson.alt })
			: undefined;
		const timer = setInterval(() => {
			if (Object.values(runs).some((r) => r.child)) refresh();
		}, 1000);

		function refresh() {
			cached = undefined;
			tui.requestRender();
		}

		function leave(result: "next" | "leave" | "project") {
			clearInterval(timer);
			for (const r of Object.values(runs)) r.child?.kill();
			if (page === pages.length - 1) markDone(lesson.number);
			done(result);
		}

		function startRun(key: "before" | "after", full: boolean) {
			const command = key === "before" ? lesson.before : lesson.after;
			if (!command || runs[key]?.child) return;
			const runsDir = mkdtempSync(join(tmpdir(), `lesson-${lesson.number}-${key}-`));
			const isHarness = command.includes("harness.py");
			const profile = isHarness ? sessionProfile(agentDir(), ctx.model, mkdtempSync(join(tmpdir(), `lesson-${lesson.number}-profile-`))) : undefined;
			const argv = isHarness ? runArgv(command, runsDir, full, profile) : command.split(/\s+/);
			const state: RunState = { label: full ? "full run" : "one session", started: Date.now(), lines: [], runsDir: isHarness ? runsDir : undefined };
			runs[key] = state;
			const child = spawn(argv[0], argv.slice(1), { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
			state.child = child;
			running.add(child);
			let tail = "";
			const keep = (b: Buffer) => { tail = (tail + b.toString()).slice(-2000); };
			child.stdout?.on("data", keep);
			child.stderr?.on("data", keep);
			child.on("close", (code) => {
				running.delete(child);
				state.child = undefined;
				if (isHarness) {
					const s = summariseRuns(runsDir);
					state.verdict = s.verdict === "NONE" ? "NO RESULT" : `${s.verdict}  (${s.passed} of ${s.total} passed)`;
					state.lines = s.total ? s.lines : tail.trim().split("\n").slice(-4);
				} else {
					state.verdict = code === 0 ? "PASS" : `FAIL (exit ${code})`;
					state.lines = tail.trim().split("\n").slice(-4);
				}
				refresh();
			});
			refresh();
		}

		function projectBlock(_width: number): string[] {
			return ["", theme.fg("muted", ` p  try it by hand: this Pi moves into project/${lesson.number}, with the task in TASK.md`)];
		}

		function runBlock(key: "before" | "after", width: number): string[] {
			const command = key === "before" ? lesson.before : lesson.after;
			if (!command) return [];
			const out = ["", theme.fg("accent", key === "before" ? " Before" : " After"), ...wrapTextWithAnsi(theme.fg("dim", ` ${command}`), width)];
			const r = runs[key];
			if (!r) out.push(theme.fg("muted", ` r  run one session   R  run the page's n${ctx.model ? `   on ${ctx.model.provider}/${ctx.model.id}` : ""}`));
			else if (r.child) out.push(theme.fg("warning", ` running (${r.label}) … ${Math.round((Date.now() - r.started) / 1000)} s`));
			else {
				const good = r.verdict?.startsWith("PASS");
				out.push((good ? theme.fg("success", ` ${r.verdict}`) : theme.fg("error", ` ${r.verdict}`)));
				for (const l of r.lines) out.push(...wrapTextWithAnsi(`   ${l}`, width));
				const code = r.runsDir ? producedCode(r.runsDir) : undefined;
				if (code) {
					out.push("", theme.fg("accent", `   the code it wrote · ${code.name}`));
					for (const l of code.text.replace(/\n+$/, "").split("\n")) out.push(theme.fg("mdCode", `   ${l}`));
				}
				const why = good ? undefined : unitPathology(root, lesson.unit);
				if (why) out.push(...wrapTextWithAnsi(theme.fg("warning", `   Why: ${why}`), width));
				if (r.label === "one session") out.push(theme.fg("dim", "   one session is a demonstration, not the lesson check"));
			}
			return out;
		}

		function render(width: number): string[] {
			if (cached) return cached;
			const w = Math.max(20, width);
			const name = pages[page];
			const lines: string[] = [];
			const head = ` ${lesson.number} · ${lesson.title}   lesson ${total.index + 1} of ${total.count}   step ${page + 1} of ${pages.length}: ${name}`;
			lines.push(theme.fg("accent", truncateToWidth(head, w)), theme.fg("dim", "─".repeat(w)));
			if (name === "Cover") {
				if (picture) lines.push(...picture.render(w));
				lines.push("", ...md(`**${lesson.opening}**`).render(w), "");
				lines.push(theme.fg("accent", " Questions"), ...md(list(lesson.questions)).render(w));
				lines.push(theme.fg("accent", " Objectives"), ...md(list(lesson.objectives)).render(w));
			} else if (name === "Key points") {
				lines.push(...md(list(lesson.keyPoints)).render(w));
				lines.push("", theme.fg("muted", total.index + 1 < total.count ? " n  next lesson   Esc  leave" : " That was the last lesson. The Challenge is next: see learn/challenge/index.md"));
			} else {
				lines.push(...md(tidy(lesson.steps[name] ?? "")).render(w));
				if (name === "Eval case") lines.push(...runBlock("before", w), ...projectBlock(w));
				if (name === "Solution") {
					lines.push(...runBlock("after", w));
					const unit = lesson.unit.match(/`([a-z]+\/[a-z-]+)`/)?.[1];
					if (unit) lines.push("", theme.fg("muted", ` By hand: /remedy on ${unit}`));
					lines.push(...projectBlock(w));
				}
			}
			lines.push("", theme.fg("dim", " ← back   → / Enter next   Esc leave"));
			cached = lines.map((l) => truncateToWidth(l, w));
			return cached;
		}

		function handleInput(data: string) {
			const name = pages[page];
			if (matchesKey(data, Key.escape)) return leave("leave");
			if (matchesKey(data, Key.right) || matchesKey(data, Key.enter)) {
				if (page < pages.length - 1) page += 1;
				return refresh();
			}
			if (matchesKey(data, Key.left)) {
				if (page > 0) page -= 1;
				return refresh();
			}
			if ((data === "r" || data === "R") && (name === "Eval case" || name === "Solution"))
				return startRun(name === "Eval case" ? "before" : "after", data === "R");
			if (data === "n" && name === "Key points" && total.index + 1 < total.count) return leave("next");
			if (data === "p" && (name === "Eval case" || name === "Solution")) {
				prepareProject(root, lesson);
				saveProgress((p) => { p.at[lesson.number] = page; });
				return leave("project");
			}
		}

		return { render, invalidate: () => { cached = undefined; }, handleInput };
	});
}

/** Runs still going when the session ends are stopped with it. */
const running = new Set<ChildProcess>();

// The lesson panel's live state: the before/after runs the learner triggers with /lesson before|after,
// read by the pinned header and refreshed when a run starts or finishes. Reset when a lesson opens.
const panelRuns: Record<string, RunState> = {};
let panelRefresh: (() => void) | undefined;
let panelNumber: string | undefined;

/** A small banner for the top of the lesson panel. */
const BANNER = [
	"  .---.",
	"  |o_o|  Small AI Learning Center",
	"  '---'",
];

/** Run a lesson's before/after line in-session (cwd = repo root, as the harness expects), updating
 * the panel. One session; the model Pi is on is pinned in a throwaway profile. */
function startArm(root: string, ctx: any, key: "before" | "after", command: string): void {
	if (panelRuns[key]?.child) return;
	const runsDir = mkdtempSync(join(tmpdir(), `lesson-${key}-`));
	const isHarness = command.includes("harness.py") || command.includes("flow_run.py");
	const profile = isHarness ? sessionProfile(agentDir(), ctx.model, mkdtempSync(join(tmpdir(), "lesson-profile-"))) : undefined;
	const argv = isHarness ? runArgv(command, runsDir, false, profile) : command.split(/\s+/);
	const state: RunState = { label: "one session", started: Date.now(), lines: [], runsDir: isHarness ? runsDir : undefined };
	panelRuns[key] = state;
	const child = spawn(argv[0], argv.slice(1), { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
	state.child = child;
	running.add(child);
	let tail = "";
	const keep = (b: Buffer) => { tail = (tail + b.toString()).slice(-2000); };
	child.stdout?.on("data", keep);
	child.stderr?.on("data", keep);
	child.on("close", (code) => {
		running.delete(child);
		state.child = undefined;
		if (isHarness) {
			const s = summariseRuns(runsDir);
			state.verdict = s.verdict === "NONE" ? "NO RESULT" : `${s.verdict}  (${s.passed} of ${s.total} passed)`;
			state.lines = s.total ? s.lines : tail.trim().split("\n").slice(-4);
		} else {
			state.verdict = code === 0 ? "PASS" : `FAIL (exit ${code})`;
			state.lines = tail.trim().split("\n").slice(-4);
		}
		// A remedy/stand-in lesson is done when its after line passes.
		if (key === "after" && state.verdict?.startsWith("PASS") && panelNumber) markDone(panelNumber);
		panelRefresh?.();
	});
	panelRefresh?.();
}

/** The result block the panel shows for a before/after run: the command, a live "running" line, then
 * the verdict, the code the session wrote, and a "Why" for a fail. */
function panelRunBlock(root: string, lesson: Lesson, key: "before" | "after", width: number, theme: any): string[] {
	const command = key === "before" ? lesson.before : lesson.after;
	if (!command) return [];
	const out = ["", theme.fg("accent", key === "before" ? " Before" : " After"), ...wrapTextWithAnsi(theme.fg("dim", ` ${command}`), width)];
	const r = panelRuns[key];
	if (!r) return out;
	if (r.child) { out.push(theme.fg("warning", ` running (${r.label}) …`)); return out; }
	const good = r.verdict?.startsWith("PASS");
	out.push(good ? theme.fg("success", ` ${r.verdict}`) : theme.fg("error", ` ${r.verdict}`));
	for (const l of r.lines) out.push(...wrapTextWithAnsi(`   ${l}`, width));
	const code = r.runsDir ? producedCode(r.runsDir) : undefined;
	if (code) {
		out.push("", theme.fg("accent", `   the code it wrote · ${code.name}`));
		for (const l of code.text.replace(/\n+$/, "").split("\n")) out.push(theme.fg("mdCode", `   ${l}`));
	}
	const why = good ? undefined : unitPathology(root, lesson.unit);
	if (why) out.push(...wrapTextWithAnsi(theme.fg("warning", `   Why: ${why}`), width));
	return out;
}

// The panel is a fixed height and you page through it; which page is showing, and how many there are.
const PANEL_HEIGHT = 16;
let page = 0;
let pageCount = 1;
let unsubInput: (() => void) | undefined;

/** The lesson as pages for the fixed-height panel: the aim, each of the six steps (with the before
 * line on Eval case and the after line on Solution), then the key points. */
function buildPages(lesson: Lesson, root: string, cwd: string, width: number): { name: string; content: string[]; run?: "before" | "after" }[] {
	const md = (t: string) => new Markdown(t, 1, 0, getMarkdownTheme());
	const pages: { name: string; content: string[]; run?: "before" | "after" }[] = [];
	pages.push({ name: "Aim", content: md(`**${lesson.opening}**`).render(width) });
	// The hands-on "what to do" page (the same lines the project guide pins): run-and-read for a
	// stand-in lesson, the /mellum tryit for a command lesson, ask-the-model + /remedy for a remedy one.
	const guide = projectGuide(root, cwd);
	if (guide && guide.length > 2) pages.push({ name: "How to", content: md(guide.slice(1, -1).join("\n")).render(width) });
	for (const s of STEPS) {
		if (!lesson.steps[s]?.trim()) continue;
		const run = s === "Eval case" && lesson.before ? "before" : s === "Solution" && lesson.after ? "after" : undefined;
		pages.push({ name: s, content: md(tidy(lesson.steps[s])).render(width), run });
	}
	if (lesson.keyPoints.length) pages.push({ name: "Key points", content: md(lesson.keyPoints.map((k) => `- ${k}`).join("\n")).render(width) });
	return pages;
}

export default function (pi: any): void {
	pi.on("session_shutdown", () => {
		for (const child of running) child.kill();
		running.clear();
		unsubInput?.();
		unsubInput = undefined;
	});
	// One panel pinned above the editor, for you and never the model: the banner, the lesson guide in
	// a project folder (the command legend elsewhere), and the before/after runs as they happen. It
	// stays put while the chat scrolls (setHeader, the top slot, only shows at startup and scrolls off).
	pi.on("session_start", (_event: unknown, ctx: any) => {
		unsubInput?.();
		unsubInput = undefined;
		const root = findRoot(ctx.cwd ?? process.cwd());
		if (!root) return ctx.ui?.setWidget?.("lesson", undefined);
		const cwd = ctx.cwd ?? process.cwd();
		panelNumber = projectNumber(root, cwd);
		page = 0;
		for (const k of Object.keys(panelRuns)) delete panelRuns[k];
		const lessonEntry = panelNumber ? lessonIndex(root).find((e) => e.number === panelNumber) : undefined;
		const lesson = lessonEntry ? parseLesson(readFileSync(lessonEntry.file, "utf8")) : undefined;
		// Page the fixed-height panel with PageUp/PageDown; every other key still reaches the editor, so
		// you keep typing to the model. Only inside a lesson, and torn down when the session changes.
		if (lesson && ctx.ui?.onTerminalInput) {
			unsubInput = ctx.ui.onTerminalInput((data: string) => {
				if (matchesKey(data, Key.pageDown)) { page = Math.min(pageCount - 1, page + 1); panelRefresh?.(); return { consume: true }; }
				if (matchesKey(data, Key.pageUp)) { page = Math.max(0, page - 1); panelRefresh?.(); return { consume: true }; }
				return undefined;
			});
		}
		ctx.ui?.setWidget?.("lesson", (tui: any, theme: any) => {
			panelRefresh = () => tui.requestRender();
			const paint = {
				title: (t: string) => theme.bold(theme.fg("accent", t)),
				step: (t: string) => theme.fg("accent", t),
				code: (t: string) => theme.fg("mdCode", t),
				dim: (t: string) => theme.fg("dim", t),
				rule: (t: string) => theme.fg("borderMuted", t),
			};
			return {
				render: (width: number) => {
					const w = Math.max(20, width);
					if (!lesson) {
						const legend = [...BANNER.map((l) => theme.fg("accent", l)), "", ...styleGuide(lessonLegend(), paint, w)];
						return legend.flatMap((line) => wrapTextWithAnsi(line, w));
					}
					const pages = buildPages(lesson, root, cwd, w);
					pageCount = pages.length;
					if (page >= pageCount) page = pageCount - 1;
					const p = pages[page];
					let body = [...p.content];
					if (p.run) body.push(...panelRunBlock(root, lesson, p.run, w, theme));
					body = body.flatMap((line) => wrapTextWithAnsi(line, w));
					const area = Math.max(3, PANEL_HEIGHT - 2);
					if (body.length > area) body = [...body.slice(0, area - 1), theme.fg("dim", "   … more — PageDown")];
					while (body.length < area) body.push("");
					const header = theme.bold(theme.fg("accent", `▍ ${lesson.number} · ${lesson.title}  ·  ${p.name}  (${page + 1}/${pageCount})`));
					const foot = theme.fg("dim", ` PageUp/PageDown to page${p.run ? ` · /lesson ${p.run} runs it` : ""} · type below to talk to the model`);
					return [header, ...body, foot];
				},
				invalidate: () => {},
				dispose: () => { panelRefresh = undefined; },
			};
		}, { placement: "aboveEditor" });
	});
	pi.registerCommand("start", {
		description: "Start the course: open your next lesson (the same as /lesson)",
		handler: async (_args: string, ctx: any) => {
			try {
				await openLesson("", ctx);
			} catch (error) {
				ctx.ui.notify(`/start failed: ${(error as Error)?.stack ?? error}`, "error");
			}
		},
	});
	pi.registerCommand("lesson", {
		description: "Take a lesson: /lesson to pick one, /lesson E1 opens it hands-on; inside it /lesson before|after run the arms, /lesson read shows the prose, /lesson back returns, /lesson clear starts over",
		getArgumentCompletions: (prefix: string) => {
			const root = findRoot(process.cwd());
			if (!root) return null;
			const items = lessonIndex(root).filter((l) => l.number.toLowerCase().startsWith(prefix.toLowerCase()))
				.map((l) => ({ value: l.number, label: `${l.number} · ${l.title}` }));
			return items.length ? items : null;
		},
		handler: async (args: string, ctx: any) => {
			try {
				await openLesson(args, ctx);
			} catch (error) {
				ctx.ui.notify(`/lesson failed: ${(error as Error)?.stack ?? error}`, "error");
			}
		},
	});
}

/** Move this Pi into `dir`: a new session whose working directory is that folder. */
async function moveTo(ctx: any, dir: string, note: string, then?: (next: any) => Promise<void>): Promise<void> {
	const store = join(findRoot(dir) ?? dir, "project", ".sessions");
	await ctx.switchSession(sessionIn(dir, CURRENT_SESSION_VERSION, store), {
		withSession: async (next: any) => {
			next.ui.notify(note, "info");
			if (then) await then(next);
		},
	});
}

async function openLesson(args: string, ctx: any, startPage = 0): Promise<void> {
			const root = findRoot(ctx.cwd ?? process.cwd());
			if (!root) return ctx.ui.notify("/lesson runs in a checkout of mellum-worker (no learn/lessons here)", "error");
			if (ctx.mode && ctx.mode !== "tui") return ctx.ui.notify("/lesson needs Pi's interactive terminal", "error");
			if (args.trim() === "before" || args.trim() === "after") {
				const number = projectNumber(root, ctx.cwd ?? process.cwd());
				const entry = number && lessonIndex(root).find((e) => e.number === number);
				if (!entry) return ctx.ui.notify("/lesson before and /lesson after run inside a lesson's project folder", "info");
				const lesson = parseLesson(readFileSync(entry.file, "utf8"));
				const key = args.trim() as "before" | "after";
				const command = key === "before" ? lesson.before : lesson.after;
				if (!command) return ctx.ui.notify(`this lesson has no ${key} line`, "info");
				startArm(root, ctx, key, command);
				return ctx.ui.notify(`running the ${key} line … watch the panel above`, "info");
			}
			const here = projectNumber(root, ctx.cwd ?? process.cwd());
			if (here && ["", "back", "home"].includes(args.trim())) {
				// Back to the repository; the lesson's panel/legend shows there. No slideshow to resume.
				return moveTo(ctx, root, `Back from project/${here}. /lesson opens the next lesson.`);
			}
			if (args.trim() === "back" || args.trim() === "home") return ctx.ui.notify("already in the repository: /lesson opens the next lesson", "info");
			if (args.trim() === "clear") {
				const number = projectNumber(root, ctx.cwd ?? process.cwd());
				const entry = number && lessonIndex(root).find((e) => e.number === number);
				if (!entry) return ctx.ui.notify("/lesson clear works in a project folder: open a lesson first", "info");
				const lesson = parseLesson(readFileSync(entry.file, "utf8"));
				return moveTo(ctx, prepareProject(root, lesson), `project/${entry.number} is back to its starting files, in a fresh session.`);
			}
			if (args.trim() === "clean") {
				if (await ctx.ui.confirm("Remove project/ and every lesson's work in it?", "This deletes the folder; the repository is untouched.")) {
					cleanProjects(root);
					ctx.ui.notify("removed project/", "info");
				}
				return;
			}
			// /lesson read [<n>] opens the prose deck (the opt-in slideshow); otherwise the lesson opens
			// hands-on, straight into its project folder with the live panel pinned above the prompt.
			let arg = args.trim();
			const readMode = arg === "read" || arg.startsWith("read ");
			if (readMode) arg = arg.slice(4).trim();
			const track = lessonIndex(root);
			const done = loadDone();
			let index = track.findIndex((l) => l.number.toLowerCase() === arg.toLowerCase());
			if (index < 0) {
				const next = track.findIndex((l) => !done.has(l.number));
				const order = next > 0 ? [...track.slice(next), ...track.slice(0, next)] : track;
				const options = order.map((l) => `${done.has(l.number) ? "✓" : " "} ${l.number} · ${l.title}`);
				const picked = await ctx.ui.select("Lessons (the next one is first)", options);
				if (!picked) return;
				index = track.findIndex((l) => picked.includes(` ${l.number} · `));
				if (index < 0) return;
			}
			const entry = track[index];
			const lesson = parseLesson(readFileSync(entry.file, "utf8"));
			// Make the project folder when the lesson opens; only when missing, so reopening never wipes WIP.
			if (!existsSync(join(root, "project", entry.number))) prepareProject(root, lesson);
			if (readMode) {
				const result = await walk(ctx, root, lesson, entry, { index, count: track.length }, startPage);
				if (result === "project") return moveTo(ctx, join(root, "project", entry.number),
					`Now in project/${entry.number}: the lesson panel is above, the prompt is yours. /lesson back returns.`);
				return;
			}
			// A command lesson (no before/after arm) is done on opening; a remedy/stand-in on an after pass.
			if (!lesson.before) markDone(entry.number);
			return moveTo(ctx, join(root, "project", entry.number),
				`Now in project/${entry.number}: the lesson panel is above, the prompt is yours. /lesson before and /lesson after run the arms; /lesson back returns.`);
}
