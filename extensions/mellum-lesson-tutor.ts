/**
 * mellum-lesson-tutor: /lesson, the course inside Pi.
 *
 *   /lesson          pick a lesson (finished ones are ticked; the next one is first)
 *   /lesson E3       open lesson E3
 *
 * One screen per step: the cover (picture, opening, questions, objectives), Paul's six steps, and
 * the key points. On the Eval case step `r` runs the page's before line and on the Solution step
 * its after line, one session each (`R` runs the page's own n), and the result is summarised from
 * each session's run.json. → / Enter next, ← back, n next lesson (on the last step), Esc leave.
 * The lesson page is the only source (see mellum-lessons.ts). No model is involved.
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

export default function (pi: any): void {
	pi.on("session_shutdown", () => {
		for (const child of running) child.kill();
		running.clear();
	});
	// Always a widget above the editor, for you and never the model: the project guide in a lesson's
	// project folder, the command legend anywhere else in the checkout.
	pi.on("session_start", (_event: unknown, ctx: any) => {
		const root = findRoot(ctx.cwd ?? process.cwd());
		const guide = root ? projectGuide(root, ctx.cwd ?? process.cwd()) : undefined;
		const lines = guide ?? (root ? lessonLegend() : undefined);
		ctx.ui?.setWidget?.("lesson", lines ? (_tui: any, theme: any) => ({
			render: (width: number) => styleGuide(lines, {
				title: (t) => theme.bold(theme.fg("accent", t)),
				step: (t) => theme.fg("accent", t),
				code: (t) => theme.fg("mdCode", t),
				dim: (t) => theme.fg("dim", t),
				rule: (t) => theme.fg("borderMuted", t),
			}, width).flatMap((line) => wrapTextWithAnsi(line, width)),
			invalidate: () => {},
		}) : undefined);
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
		description: "Take a lesson: /lesson to pick one, /lesson E1 to open it; in a project folder, /lesson back returns to the lesson and /lesson clear starts over",
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
			const here = projectNumber(root, ctx.cwd ?? process.cwd());
			if (here && ["", "back", "home"].includes(args.trim())) {
				// Back to the repository, and straight into the lesson at the step it was left on.
				return moveTo(ctx, root, `Back from project/${here}.`, (next) => openLesson(here, next, loadProgress().at[here] ?? 0));
			}
			if (args.trim() === "back" || args.trim() === "home") return ctx.ui.notify("already in the repository: /lesson opens the next lesson", "info");
			if (args.trim() === "clear") {
				const number = projectNumber(root, ctx.cwd ?? process.cwd());
				const entry = number && lessonIndex(root).find((e) => e.number === number);
				if (!entry) return ctx.ui.notify("/lesson clear works in a project folder: open a lesson and press p", "info");
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
			const track = lessonIndex(root);
			const done = loadDone();
			let index = track.findIndex((l) => l.number.toLowerCase() === args.trim().toLowerCase());
			if (index < 0) {
				const next = track.findIndex((l) => !done.has(l.number));
				const order = next > 0 ? [...track.slice(next), ...track.slice(0, next)] : track;
				const options = order.map((l) => `${done.has(l.number) ? "✓" : " "} ${l.number} · ${l.title}`);
				const picked = await ctx.ui.select("Lessons (the next one is first)", options);
				if (!picked) return;
				index = track.findIndex((l) => picked.includes(` ${l.number} · `));
				if (index < 0) return;
			}
			while (index < track.length) {
				const entry = track[index];
				const lesson = parseLesson(readFileSync(entry.file, "utf8"));
				const result = await walk(ctx, root, lesson, entry, { index, count: track.length }, startPage);
				startPage = 0;
				if (result === "project") return moveTo(ctx, join(root, "project", entry.number),
					`Now in project/${entry.number}: the steps are above the editor. /lesson back returns to the lesson.`);
				if (result !== "next") break;
				index += 1;
			}
}
