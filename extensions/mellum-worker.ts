/**
 * Mellum mode: run the small model inside the main session with the worker's prompt
 * and tools, and show it nothing from before the mode began.
 *
 *   /mellum <task>  – one shot: switch to Mellum, run the task, switch back when settled.
 *                     One shot under `pi -p` or `--mode json` (no UI): the command waits for
 *                     the run, switches back and writes the run record before it returns.
 *   /mellum on      – stay on for several turns (switch model, tools, mark the start)
 *   /mellum off     – restore the previous model and tools
 *   /mellum check   – compare the oMLX server and the Pi provider entry with the measured
 *                     settings and print the findings; never switches, never writes
 *   /mellum learn [n] – name what went wrong in the last n runs (default 10) in this directory
 *                     and suggest a ## Mellum section; AGENTS.md is written only on a yes
 *   /mellum last    – the newest run in this directory (Mode or Worker) as a Markdown table;
 *                     a notification while Mode is on, so the table stays out of Mellum's context
 *
 * Each activation GETs the server's model settings (1 s at most) and warns once when they
 * differ from the measured profile; the run record keeps the result as `server`.
 *
 * While on, before_provider_request rewrites the outgoing payload: the system message
 * becomes the worker prompt (prompts/mellum-worker.md, or $MELLUM_MODE_PROMPT), and the
 * messages are only those after the on-marker, minus Superpowers' bootstrap message.
 * Earlier turns' reasoning_content is left in place: removing it made runs 60% slower
 * (ladder A12). The session keeps everything; after /mellum off the parent is sent one
 * handoff block per finished span (task, files touched, last command output, final reply)
 * in place of Mellum's tool calls (the `context` hook).
 *
 * Headless: MELLUM_MODE=1 activates at session start (the ladder's "mode" runner).
 * Installed as a Pi package extension it loads in every parent session and stays dormant until /mellum. While on, it runs the child guards (createGuardSet) itself, so no second extension is needed.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, isAbsolute, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { adminBaseOf, checkSetup, type Diff, fetchJson, formatFindings, gatherInputs, loadExpected, readProvider, serverCheck, type ServerCheck } from "./mellum-check.ts";
import { createGuardSet, type GuardSet } from "./mellum-guards.ts";
import { factsBlock, readProjectFacts, type ProjectFacts } from "./mellum-facts.ts";
import { type Activation, type Msg, promptVersionOf, runRecord, textOf, spanStats, type SpanStats } from "./mellum-record.ts";
import { formatMerge, formatReport, learnFromTexts, mergeSuggestion, modeRunsFile, overCap, recordFiles } from "./mellum-learn.ts";
import { formatLast, pickLast } from "./mellum-last.ts";

export const MARK_ON = "[mellum-worker on]";
export const MARK_OFF = "[mellum-worker off]";
export const BOOTSTRAP_MARKER = "superpowers:using-superpowers bootstrap for pi";
export const WORKER_TOOLS = ["read", "grep", "find", "ls", "bash", "edit", "write"];
const DEFAULT_MODEL = { provider: "omlx", id: "Mellum2.1-12B-A2.5B-Thinking-6bit" };

const INSTRUCTION_ROLES = new Set(["system", "developer"]);

/**
 * A copy of a user message with the project facts appended: to string content, to the
 * last text part of array content, or as a new text part when there is none. Never
 * mutates `m`; a message that already ends with the block is returned as is.
 */
export function withFacts(m: Msg, facts: string): Msg {
	if (typeof m.content === "string") return m.content.endsWith(facts) ? m : { ...m, content: m.content + facts };
	if (!Array.isArray(m.content)) return { ...m, content: facts.replace(/^\n+/, "") };
	const parts: any[] = [...m.content];
	for (let i = parts.length - 1; i >= 0; i--) {
		const p = parts[i];
		if (p && p.type === "text" && typeof p.text === "string") {
			if (!p.text.endsWith(facts)) parts[i] = { ...p, text: p.text + facts };
			return { ...m, content: parts };
		}
	}
	parts.push({ type: "text", text: facts.replace(/^\n+/, "") });
	return { ...m, content: parts };
}

export function filterForMellum(payload: any, systemPrompt: string, opts: { expectMarker?: boolean; facts?: string; keepSystem?: boolean; stripThinking?: boolean } = {}) {
	if (!payload || !Array.isArray(payload.messages)) return payload;
	const msgs: Msg[] = payload.messages;
	const isMarker = (m: Msg) => m.role === "user" && (textOf(m).includes(MARK_ON) || textOf(m).includes(MARK_OFF));
	const isBootstrap = (m: Msg) => textOf(m).includes(BOOTSTRAP_MARKER);
	let start = 0;
	let markerAt = -1;
	for (let i = msgs.length - 1; i >= 0; i--) {
		if (msgs[i].role === "user" && textOf(msgs[i]).includes(MARK_ON)) {
			markerAt = i;
			break;
		}
	}
	let markerMissing = false;
	if (markerAt >= 0) {
		start = markerAt + 1;
		// Pi delivers a queued marker after the user message it was queued for, so the
		// prompt that started the mode sits just before the marker (possibly behind an
		// off-marker). Keep it unless a later user message already carries the task.
		const laterUser = msgs.slice(start).some((m) => m.role === "user" && !isMarker(m));
		if (!laterUser) {
			let j = markerAt - 1;
			while (j >= 0 && isMarker(msgs[j])) j--;
			if (j >= 0 && msgs[j].role === "user" && !isBootstrap(msgs[j])) start = j;
		}
	} else if (opts.expectMarker) {
		// The marker was compacted away or never arrived: send only the last user
		// message rather than the whole parent history, and say so.
		markerMissing = true;
		for (let i = msgs.length - 1; i >= 0; i--) {
			if (msgs[i].role === "user" && !isMarker(msgs[i]) && !isBootstrap(msgs[i])) {
				start = i;
				break;
			}
		}
	}
	const facts = opts.facts ?? "";
	const kept = msgs
		.slice(start)
		.filter((m) => !INSTRUCTION_ROLES.has(m.role ?? "") && !isMarker(m) && !isBootstrap(m))
		.map((m) => (facts && m.role === "user" ? withFacts(m, facts) : m));
	const system = opts.keepSystem
		? (msgs.find((m) => m.role === "system") ?? { role: "system", content: "" })
		: { role: "system", content: systemPrompt };
	const messages = opts.stripThinking ? stripReasoning(kept as Record<string, any>[]) : kept;
	const out: any = { ...payload, messages: [system, ...messages] };
	// pi-subagents re-adds its own tools after setActiveTools; the worker gets only its seven.
	if (Array.isArray(payload.tools)) narrowTools(payload, out);
	if (markerMissing) out.mellumModeMarkerMissing = true;
	return out;
}

/** Keep only the worker's seven tools in `out` (and drop a tool_choice outside them), reading
 * them from `payload`. Shared with the `context/narrow-tools` remedy unit. */
export function narrowTools(payload: any, out: any): void {
	const tools = payload.tools.filter((t: any) => WORKER_TOOLS.includes(t?.function?.name ?? t?.name));
	if (tools.length) out.tools = tools;
	else delete out.tools;
	const chosen = payload.tool_choice?.function?.name ?? payload.tool_choice?.name;
	if (chosen && !WORKER_TOOLS.includes(chosen)) delete out.tool_choice;
}

/**
 * Drop earlier assistant reasoning from the payload.
 *
 * Left in place by default: removing it made runs 60% slower on the ladder (A12),
 * because this backend's prefix cache absorbs the repeated reasoning and the run
 * pays for the lost context in output tokens instead. `MELLUM_STRIP_THINKING=1`
 * opens the seam so the claim can be measured rather than assumed.
 */
export function stripReasoning<T extends Record<string, any>>(messages: T[]): T[] {
	return messages.map((m) => {
		if (m?.role !== "assistant") return m;
		if (!("reasoning_content" in m) && !("reasoning" in m)) return m;
		const { reasoning_content: _content, reasoning: _reasoning, ...rest } = m;
		return rest as T;
	});
}

/**
 * What the parent sees of a finished Mellum span: one block instead of every
 * read, edit and test run. Built from the span's own messages (Pi's internal
 * message format, as seen by the `context` event). Open spans are untouched.
 */
export interface HandoffOptions {
	/** Reports whether a written path still exists at handoff time; omitted means never flag. */
	exists?: (path: string) => boolean;
}

export function collapseHandoffs(messages: Msg[], opts: HandoffOptions = {}): Msg[] {
	// At the `context` event a sent marker is a `custom` message; in the provider
	// payload it has become a user message. Accept both.
	const hasMark = (m: Msg, mark: string) => (m.role === "user" || m.role === "custom") && textOf(m).includes(mark);
	const out: Msg[] = [];
	let i = 0;
	while (i < messages.length) {
		const m = messages[i];
		if (hasMark(m, MARK_ON)) {
			let j = i + 1;
			while (j < messages.length && !hasMark(messages[j], MARK_OFF)) j++;
			if (j >= messages.length) {
				out.push(...messages.slice(i));
				break;
			}
			// The task is the user message just before the on-marker (Pi queues the
			// marker after the prompt it was queued with), else the first after it.
			const last = out[out.length - 1];
			const prev = last && last.role === "user" && !hasMark(last, MARK_OFF) ? out.pop() : undefined;
			let span = messages.slice(i + 1, j);
			// The off-marker is queued "next turn", so it lands after the prompt the user
			// typed next; trailing user messages after the span's last reply are that
			// prompt, not part of the task.
			let tail = span.length;
			while (tail > 0 && span[tail - 1].role === "user") tail--;
			const trailing = span.slice(tail);
			span = span.slice(0, tail);
			const task = prev ? textOf(prev) : textOf(span.find((x) => x.role === "user") ?? {});
			const factsSource = /facts: (\S+)/.exec(textOf(m))?.[1];
			out.push(handoffMessage(task, span, opts, factsSource), ...trailing);
			i = j + 1;
			continue;
		}
		out.push(m);
		i++;
	}
	return out;
}

const MAX_HANDOFF_COMMANDS = 15;

function summaryLine(stats: SpanStats, factsSource?: string): string {
	const n = stats.requests;
	const wall = stats.wallSeconds === undefined ? "wall unknown" : `${stats.wallSeconds} s`;
	const last = { ok: "last command ok", failed: "last command failed", unfinished: "last command did not finish", none: "no commands" }[stats.lastCommand];
	return `Mellum: ${n} request${n === 1 ? "" : "s"}, ${stats.usage.output.toLocaleString("en-US")} output tokens, ${wall}, ${last}${factsSource ? `, facts: ${factsSource}` : ""}`;
}

function handoffMessage(task: string, span: Msg[], opts: HandoffOptions = {}, factsSource?: string): Msg {
	const stats = spanStats(span);
	const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n) + "…" : s);
	const oneLine = (s: string) => s.replace(/\s+/g, " ").trim();
	const fileList = stats.files.map((f) => (opts.exists && !opts.exists(f) ? `${f} (missing at handoff)` : f));
	const shown = stats.commands.slice(-MAX_HANDOFF_COMMANDS);
	const hidden = stats.commands.length - shown.length;
	const commandLines = shown.map((c) => `- ${clip(oneLine(c.command), 200)}${!c.finished ? " (no result)" : c.failed ? " (failed)" : ""}`);
	const body = [
		"[mellum-worker handoff] Mellum ran a task in this session; its tool calls are in the transcript but not repeated here.",
		summaryLine(stats, factsSource),
		`Task: ${clip(task.trim(), 400)}`,
		`Files edited or written: ${fileList.length ? fileList.join(", ") : "none"}`,
		commandLines.length
			? `Commands run${hidden ? ` (${hidden} earlier not shown)` : ""}:\n${commandLines.join("\n")}`
			: "Commands run: none",
		stats.lastCommandOutput ? `Last command output:\n${clip(stats.lastCommandOutput, 600)}` : "Last command output: none",
		stats.finalReply ? `Mellum's final reply:\n${clip(stats.finalReply, 1500)}` : "Mellum's final reply: (empty)",
	].join("\n");
	return { role: "user", content: [{ type: "text", text: body }], timestamp: Date.now() };
}

export type Subcommand = { cmd: "on" | "off" | "check" | "learn" | "last" | "task"; n?: number; task?: string };

/** `/mellum` arguments: on (or nothing), off, check, learn [n], last; anything else is a task. */
export function parseSubcommand(args: string): Subcommand {
	const want = (args || "").trim();
	if (want === "" || want === "on") return { cmd: "on" };
	if (want === "off" || want === "check" || want === "last") return { cmd: want };
	const learn = /^learn(?:\s+(\d+))?$/.exec(want);
	if (learn) return { cmd: "learn", n: learn[1] === undefined ? 10 : Number(learn[1]) };
	return { cmd: "task", task: want };
}

/** The one line shown on activation when the server's settings differ. */
export function serverWarning(diffs: Diff[]): string {
	const show = (v: unknown) => JSON.stringify(v) ?? "missing";
	return `Mellum server settings differ: ${diffs.map((d) => `${d.key} ${show(d.actual)} (expected ${show(d.expected)})`).join(", ")}. Run /mellum check.`;
}

/** The trailing span still open at the end of `messages`: its task text and messages, or undefined. */
export function openSpan(messages: Msg[]): { task: string; span: Msg[] } | undefined {
	const hasMark = (m: Msg, mark: string) => (m.role === "user" || m.role === "custom") && textOf(m).includes(mark);
	let on = -1;
	for (let i = messages.length - 1; i >= 0; i--) {
		if (hasMark(messages[i], MARK_OFF)) return undefined;
		if (hasMark(messages[i], MARK_ON)) {
			on = i;
			break;
		}
	}
	if (on === -1) return undefined;
	const span = messages.slice(on + 1);
	// The prompt sits just before the on-marker, or behind the previous one-shot's off-marker,
	// which Pi delivers after the next prompt (as filterForMellum allows for).
	let p = on - 1;
	while (p >= 0 && hasMark(messages[p], MARK_OFF)) p--;
	const prev = messages[p];
	const task = prev && prev.role === "user" && !hasMark(prev, MARK_ON) ? textOf(prev) : textOf(span.find((m) => m.role === "user") ?? {});
	return { task, span };
}

function runsFile(): string | undefined {
	const file = modeRunsFile(process.env, process.env.HOME ?? ".");
	return file === undefined ? undefined : resolve(file);
}

function loadPrompt(): string {
	const here = dirname(fileURLToPath(import.meta.url));
	const file = process.env.MELLUM_MODE_PROMPT || resolve(here, "..", "prompts", "mellum-worker.md");
	return readFileSync(file, "utf8").trim();
}

/**
 * Reports a problem the user must see. Without a UI (`pi -p`, `--mode json`) Pi's notify
 * is a no-op, so the message goes to stderr instead. Never throws.
 */
function warn(ctx: any, msg: string, level: "warning" | "error") {
	try {
		if (ctx?.hasUI === false) console.error(msg);
		else ctx?.ui?.notify?.(msg, level);
	} catch {}
}

/** Shows output the user asked for: notify with a UI, stdout without one. */
function say(ctx: any, msg: string, level: "info" | "warning" | "error" = "info") {
	if (ctx?.hasUI === false) console.log(msg);
	else ctx?.ui?.notify?.(msg, level);
}

const home = () => process.env.HOME || homedir();
const readIfExists = (p: string) => (existsSync(p) ? readFileSync(p, "utf8") : undefined);

/**
 * `options.fetch` replaces the global fetch for the server checks (tests pass a fake).
 */
export default function (pi: any, options: { startTimeoutMs?: number; fetch?: typeof fetch } = {}) {
	let active = false;
	let interactive = false;
	let saved: { model: any; tools: string[] } | undefined;
	let prompt = "";
	let warnedMissing = false;
	let guards: GuardSet | undefined;
	// Per-span counters for the one-line summary shown at /mellum off.
	let span = { startedAt: 0, requests: 0, toolCalls: 0, outputTokens: 0 };
	let activeModel = "";
	// The parent's context as last seen while on, plus assistant turns since; the run record is built from these.
	let lastContext: Msg[] = [];
	let turnsSinceContext: Msg[] = [];
	// Per-span facts for the run record, reset in activate.
	let host = "unknown";
	let activation: Activation = "on";
	let promptVersion = "unknown";
	let nudges = 0;
	let guardBlocks = 0;
	let spanFacts: ProjectFacts = { source: "none", bullets: [], testCommand: null, chars: 0 };
	let server: ServerCheck = { match: null, diffs: [] };

	// The activation check: one admin GET, at most 1 s, never throws; unreadable gives match null.
	async function checkServer(): Promise<ServerCheck> {
		try {
			const { baseUrl } = readProvider("pi", home(), readIfExists);
			return await serverCheck(adminBaseOf(baseUrl), { timeoutMs: 1000, fetch: options.fetch });
		} catch {
			return { match: null, diffs: [] };
		}
	}

	// /mellum check: the whole check for Pi, printed. Never activates, never writes.
	async function runCheck(ctx: any) {
		try {
			const inputs = await gatherInputs("pi", { home: home(), read: readIfExists, get: (url) => fetchJson(url, { timeoutMs: 3000, fetch: options.fetch }) });
			const findings = checkSetup(inputs, loadExpected());
			const level = findings.some((f) => f.level === "fail") ? "error" : findings.some((f) => f.level === "warn") ? "warning" : "info";
			say(ctx, formatFindings(findings), level);
		} catch (error) {
			warn(ctx, `mellum check: ${(error as Error)?.message ?? String(error)}`, "error");
		}
	}

	// /mellum learn [n]: the report for this directory, from Mode's and the Worker's records.
	// AGENTS.md is written only when the user answers yes; without a UI, or past the facts cap,
	// nothing is asked or written. After the yes it is read and merged again, and written only
	// when the lines to add are still the ones asked about and still within the cap.
	async function runLearn(ctx: any, n: number | undefined) {
		if (n === undefined || !Number.isInteger(n) || n < 1) return warn(ctx, "mellum learn: n must be a whole number above 0", "warning");
		const cwd: string = typeof ctx?.cwd === "string" ? ctx.cwd : process.cwd();
		const agentsPath = resolve(cwd, "AGENTS.md");
		let merged: ReturnType<typeof mergeSuggestion>;
		let suggestion: string[];
		try {
			const report = learnFromTexts(recordFiles(process.env, home()).map(readIfExists), { cwd, n });
			suggestion = report.suggestion;
			merged = mergeSuggestion(readIfExists(agentsPath), suggestion);
			say(ctx, formatReport(report, cwd, merged.added) + formatMerge(merged, suggestion));
		} catch (error) {
			return warn(ctx, `mellum learn: ${(error as Error)?.message ?? String(error)}`, "error");
		}
		// Past the facts cap Mode would ignore the whole section, so do not offer the write.
		if (ctx?.hasUI === false || merged.added.length === 0 || overCap(merged) || typeof ctx?.ui?.confirm !== "function") return;
		let yes = false;
		try {
			yes = (await ctx.ui.confirm("Add these lines to AGENTS.md?", merged.added.map((b) => `- ${b}`).join("\n"))) === true;
		} catch (error) {
			return warn(ctx, `mellum learn: ${(error as Error)?.message ?? String(error)}`, "error");
		}
		if (!yes) return;
		try {
			const now = mergeSuggestion(readIfExists(agentsPath), suggestion);
			if (overCap(now) || JSON.stringify(now.added) !== JSON.stringify(merged.added)) {
				return warn(ctx, "mellum learn: AGENTS.md changed while asking; run /mellum learn again", "warning");
			}
			writeFileSync(agentsPath, now.text);
			const k = merged.added.length;
			say(ctx, `mellum learn: added ${k} line${k === 1 ? "" : "s"} to ${agentsPath}`);
		} catch (error) {
			warn(ctx, `mellum learn: could not write AGENTS.md: ${(error as Error)?.message ?? String(error)}`, "error");
		}
	}

	// /mellum last: the newest record at or under this directory, as Markdown. A custom message
	// renders it and lets the main model answer questions about it; while Mode is on it is a
	// notification instead, since a message would join Mellum's span. Never starts a turn.
	function runLast(ctx: any) {
		const cwd: string = typeof ctx?.cwd === "string" ? ctx.cwd : process.cwd();
		try {
			const files = recordFiles(process.env, home());
			if (files.length === 0) return say(ctx, "mellum last: run records are off (MELLUM_MODE_RUNS=0)", "warning");
			const { record } = pickLast(files.map(readIfExists), cwd);
			if (!record) return say(ctx, `mellum last: no Mellum runs recorded under ${cwd} (read ${files.join(", ")})`, "warning");
			const text = formatLast(record);
			if (ctx?.hasUI === false || active) return say(ctx, text);
			pi.sendMessage({ customType: "mellum-last", content: text, display: true }, { triggerTurn: false });
		} catch (error) {
			warn(ctx, `mellum last: ${(error as Error)?.message ?? String(error)}`, "error");
		}
	}

	// Same resolver for the handoff collapse and the run record: absolute, else relative to the cwd.
	const existsInCwd = (p: string) => existsSync(isAbsolute(p) ? p : resolve(process.cwd(), p));

	async function activate(ctx: any, notify: boolean, how: Activation) {
		if (active) {
			ctx.ui?.notify?.("mellum-worker is already on", "info");
			return;
		}
		const { provider, id } = DEFAULT_MODEL;
		// The shipped model when the registry has it; otherwise a session model that
		// is itself Mellum, which is what a llama.cpp profile configures.
		const sessionModel = /mellum/i.test(String(ctx.model?.id ?? "")) ? ctx.model : undefined;
		const model = ctx.modelRegistry.find(provider, id) ?? sessionModel;
		if (!model) {
			warn(ctx, `mellum-worker: model ${provider}/${id} not found and the session model is not Mellum; mode stays off`, "error");
			return;
		}
		const label = `${model.provider}/${model.id}`;
		const previous = { model: ctx.model, tools: pi.getActiveTools() };
		prompt = loadPrompt();
		// Runs while the model switches; awaited below, so it adds at most its own timeout.
		const pendingServer = checkServer();
		const switched = await pi.setModel(model);
		if (!switched) {
			warn(ctx, `mellum-worker: could not select ${label} (auth or provider error); mode stays off`, "error");
			return;
		}
		saved = previous;
		pi.setActiveTools(WORKER_TOOLS);
		active = true;
		guards = createGuardSet();
		span = { startedAt: Date.now(), requests: 0, toolCalls: 0, outputTokens: 0 };
		activeModel = label;
		lastContext = [];
		turnsSinceContext = [];
		host = typeof ctx.mode === "string" ? ctx.mode : "unknown";
		activation = how;
		promptVersion = promptVersionOf(prompt);
		nudges = 0;
		guardBlocks = 0;
		interactive = notify;
		warnedMissing = false;
		// Read once per span, headless or not: the request hook forwards the same block every time.
		spanFacts = readProjectFacts(process.cwd(), { read: (p) => (existsSync(p) ? readFileSync(p, "utf8") : undefined) });
		if (spanFacts.warning) warn(ctx, spanFacts.warning, "warning");
		server = await pendingServer;
		if (server.match === false) warn(ctx, serverWarning(server.diffs), "warning");
		if (notify) pi.sendMessage({ customType: "mellum-worker", content: `${MARK_ON} facts: ${spanFacts.source}`, display: true }, { deliverAs: "nextTurn" });
		if (notify) ctx.ui?.notify?.(`mellum-worker on: ${label}, tools ${WORKER_TOOLS.join(",")}`, "info");
	}

	async function deactivate(ctx: any) {
		if (!active) {
			ctx.ui?.notify?.("mellum-worker is not on", "info");
			return;
		}
		if (!saved?.model) {
			warn(ctx, "mellum-worker: no previous model to restore; staying on. Pick a model with /model, then /mellum off.", "warning");
			return;
		}
		const restored = await pi.setModel(saved.model);
		if (!restored) {
			warn(ctx, "mellum-worker: could not restore the previous model; staying on", "error");
			return;
		}
		pi.setActiveTools(saved.tools);
		writeRunRecord(ctx);
		active = false;
		guards = undefined;
		pi.sendMessage({ customType: "mellum-worker", content: MARK_OFF, display: true }, { deliverAs: "nextTurn" });
		const secs = Math.round((Date.now() - span.startedAt) / 1000);
		ctx.ui?.notify?.(`mellum-worker off: ${span.requests} request${span.requests === 1 ? "" : "s"}, ${span.toolCalls} tool call${span.toolCalls === 1 ? "" : "s"}, ${span.outputTokens.toLocaleString("en-US")} output tokens, ${secs} s`, "info");
	}

	// Never lets an error escape: deactivation must complete whatever happens here.
	function writeRunRecord(ctx: any) {
		let file: string | undefined;
		try {
			file = runsFile();
			if (!file) return;
			const open = openSpan([...lastContext, ...turnsSinceContext]);
			if (!open) return;
			mkdirSync(dirname(file), { recursive: true });
			appendFileSync(file, JSON.stringify(runRecord(open.task, open.span, { endedAt: Date.now(), cwd: process.cwd(), model: activeModel, exists: existsInCwd, host, activation, promptVersion, nudges, guardBlocks, facts: { source: spanFacts.source, testCommand: spanFacts.testCommand, chars: spanFacts.chars }, server })) + "\n");
		} catch (error) {
			warn(ctx, `mellum-worker: could not write the run record${file ? ` to ${file}` : ""}: ${(error as Error)?.message ?? String(error)}`, "warning");
		}
	}

	let oneShot = false;
	// The one in-flight deactivation of a one shot, shared by agent_settled and the headless handler.
	let settling: Promise<void> | undefined;
	// Resolves the headless handler's wait for the run to start; set only while it waits.
	let onRunStart: (() => void) | undefined;
	const startTimeoutMs = options.startTimeoutMs ?? 60_000;

	// Ends a one shot exactly once: a second caller gets the deactivation already under way.
	function settle(ctx: any): Promise<void> {
		if (settling) return settling;
		oneShot = false;
		settling = deactivate(ctx).finally(() => {
			settling = undefined;
		});
		return settling;
	}

	pi.registerCommand("mellum", {
		description: "mellum <task> | on | off | check | learn [n] | last — run Mellum with the worker prompt and tools inside this session",
		handler: async (args: string, ctx: any) => {
			const sub = parseSubcommand(args);
			if (sub.cmd === "off") return deactivate(ctx);
			if (sub.cmd === "on") return activate(ctx, true, "on");
			if (sub.cmd === "check") return runCheck(ctx);
			if (sub.cmd === "learn") return runLearn(ctx, sub.n);
			if (sub.cmd === "last") return runLast(ctx);
			const want = sub.task ?? "";
			// One shot: the task runs under the mode and the mode ends when the agent settles.
			if (active) {
				warn(ctx, "mellum-worker is already on; type the task as a normal prompt, or /mellum off first", "warning");
				return;
			}
			// Read while the ctx is certainly live. Without a UI (pi -p, JSON mode) Pi treats the
			// prompt as finished when this handler returns and disposes the runtime, so the
			// handler must wait for the run and the deactivation.
			const headless = ctx.hasUI === false && typeof ctx.waitForIdle === "function";
			const waitForIdle: () => Promise<void> = ctx.waitForIdle;
			await activate(ctx, true, "one-shot");
			if (!active) return;
			oneShot = true;
			if (!headless) {
				pi.sendUserMessage(want);
				return;
			}
			// sendUserMessage is fire-and-forget and the run is not active (so not "busy")
			// until Pi has run its input and before_agent_start handlers: wait for agent_start
			// first, or waitForIdle would return before the task ran.
			const started = new Promise<boolean>((resolve) => {
				onRunStart = () => resolve(true);
			});
			let timer: ReturnType<typeof setTimeout> | undefined;
			const timedOut = new Promise<boolean>((resolve) => {
				timer = setTimeout(() => resolve(false), startTimeoutMs);
			});
			pi.sendUserMessage(want);
			let didStart: boolean;
			try {
				didStart = await Promise.race([started, timedOut]);
			} finally {
				clearTimeout(timer);
				onRunStart = undefined;
			}
			if (!didStart) warn(ctx, `mellum-worker: the task did not start within ${startTimeoutMs / 1000} s; switching the mode off`, "warning");
			await waitForIdle();
			// Pi resolves the idle wait after agent_settled handlers return, so normally
			// agent_settled has already deactivated; cover the other order too.
			if (settling) await settling;
			else if (active && oneShot) await settle(ctx);
		},
	});

	pi.on("agent_start", () => {
		if (oneShot) onRunStart?.();
	});

	pi.on("agent_settled", async (_event: any, ctx: any) => {
		if (active && oneShot) await settle(ctx);
	});

	pi.on("session_start", async (_event: any, ctx: any) => {
		if (process.env.MELLUM_MODE === "1" && !active) await activate(ctx, false, "headless");
	});

	// Pi sizes auto-compaction against the active model's window (Mellum's 56k) over the
	// whole, unfiltered session. Compacting the parent's history with Mellum would be a
	// lossy change to the user's session, and it would erase the on-marker. Refuse while on.
	pi.on("session_before_compact", (event: any, ctx: any) => {
		if (!active || event?.reason === "manual") return undefined;
		ctx.ui?.notify?.("mellum-worker: auto-compaction skipped while the mode is on (/mellum off first, or /compact)", "warning");
		return { cancel: true };
	});

	// Off: the parent gets one handoff block per finished span instead of Mellum's
	// every read, edit and test run. The session itself keeps everything.
	pi.on("context", (event: any) => {
		if (active) {
			lastContext = event.messages;
			turnsSinceContext = [];
			return undefined;
		}
		if (!event.messages.some((m: any) => textOf(m).includes(MARK_ON))) return undefined;
		const collapsed = collapseHandoffs(event.messages, { exists: existsInCwd });
		return collapsed === event.messages ? undefined : { messages: collapsed };
	});

	pi.on("before_provider_request", (event: any, ctx: any) => {
		if (!active) return undefined;
		span.requests += 1;
		const out = filterForMellum(event.payload, prompt, {
			expectMarker: interactive,
			facts: factsBlock(spanFacts),
			keepSystem: process.env.MELLUM_WORKER_PROMPT === "pi",
			stripThinking: process.env.MELLUM_STRIP_THINKING === "1",
		});
		if (out?.mellumModeMarkerMissing) {
			delete out.mellumModeMarkerMissing;
			if (!warnedMissing) {
				warnedMissing = true;
				ctx?.ui?.notify?.("mellum-worker: the on-marker is gone from the context; sending only the last message", "warning");
			}
		}
		return out;
	});

	// The child's guards, run in-session while the mode is on. A fresh set per span.
	pi.on("tool_call", (event: any) => {
		if (!active || !guards) return undefined;
		span.toolCalls += 1;
		const result = guards.toolCall(event);
		if (result?.block) guardBlocks += 1;
		return result;
	});
	pi.on("turn_end", (event: any) => {
		if (active && guards) {
			guards.turnEnd(event);
			const out = event?.message?.usage?.output;
			if (event?.message?.role === "assistant") {
				if (typeof out === "number") span.outputTokens += out;
				turnsSinceContext.push(event.message);
			}
		}
		return undefined;
	});
	pi.on("agent_before_settle", () => {
		if (!active || !guards) return undefined;
		const result = guards.beforeSettle();
		if (result?.continue) nudges += 1;
		return result;
	});
}
