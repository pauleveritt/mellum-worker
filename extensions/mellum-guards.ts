/**
 * Child-only guards for the Mellum worker: pure `ToolCall -> Decision`
 * functions in the shape proven in the ladder (`ladder/`), adapted
 * to Pi's hooks at the bottom of this file; Mellum Worker reuses `createGuardSet` while it is on.
 *
 * Each guard exists for a recorded pathology:
 * - newFileOnlyWrite: a model wrote the changed fragment as the whole file
 *   (942 lines -> 2) under a write-only envelope. The refusal states the fact
 *   the model lacked, at the moment it matters.
 * - createLoopBreaker (repeats are forgotten after an edit, write, or bash call): 245 identical `ls -R` calls, all successful; ported
 *   unchanged (window 20, threshold 5, keyed on tool + sorted arguments).
 * - createStepBudget: Pi has no turn cap; a budget that blocks with a reason
 *   to summarise beats an abort, which the parent reads as a failed run.
 * - createEmptyFinalNudge: the one pathology the ladder recorded (5 of 45
 *   v3 runs, every failure): a turn ends with `stop`, no text, no tool call,
 *   part-way through the task. At `agent_before_settle` the guard proposes
 *   one custom message restating the completion fact and asks for one more
 *   model request, at most `max` times per run.
 *
 * The recorder (`createRecorder`, wired next to the guard set in the default export) only
 * observes: it keeps the run's messages and the nudge and block counts, and at
 * `agent_settled` appends one `kind: "worker"` run record. It never changes a guard
 * decision and never throws into Pi.
 *
 * ENABLED is set from the ladder records: the empty-final nudge capped at 3
 * and the loop breaker live are phase 2b's 15/15 configuration
 * (evals/2026-10-09-phase2b-guards-bounded). The other guards stay
 * dormant: their columns never went non-zero in direct mode.
 */

import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, isAbsolute, resolve } from "node:path";
import { adminBaseOf, readProvider, serverCheck, type ServerCheck } from "./mellum-check.ts";
import { type Msg, promptVersionOf, runRecord, textOf } from "./mellum-record.ts";

export interface ToolCall {
	toolName: string;
	input: unknown;
}

export interface Block {
	block: true;
	reason: string;
}

export type Decision = Block | undefined;
export type Guard = (call: ToolCall) => Decision;

export const ENABLED: {
	newFileOnlyWrite?: boolean;
	loopBreaker?: boolean;
	stepBudget?: number;
	emptyFinalNudge?: number;
	blockForegroundServer?: boolean;
	confineToWorkspace?: boolean;
} = { emptyFinalNudge: 3, loopBreaker: true, blockForegroundServer: true, confineToWorkspace: true };

export const NUDGE_TEXT =
	"[mellum-guard] Your last turn ended with no reply and no tool call. " +
	"The task is complete only when the test command exits 0. " +
	"Continue: run the next step, and when the tests pass reply with the files changed and the test output.";

interface MessageLike {
	role?: string;
	content?: unknown;
}

export interface Continuation {
	entries: { type: "custom_message"; customType: string; content: string; display: boolean }[];
	continue: true;
}

function isEmptyAssistantTurn(message: MessageLike): boolean {
	if (message.role !== "assistant") return false;
	// Only a turn the model ended itself is a lapse; an aborted or errored turn is not ours to continue.
	const stop = (message as Record<string, unknown>).stopReason;
	if (typeof stop === "string" && stop !== "stop") return false;
	const blocks = Array.isArray(message.content) ? (message.content as Record<string, unknown>[]) : [];
	const hasText = blocks.some((b) => b.type === "text" && typeof b.text === "string" && b.text.trim() !== "");
	const hasCall = blocks.some((b) => b.type === "toolCall");
	return !hasText && !hasCall;
}

export function createEmptyFinalNudge(max: number): (message: MessageLike) => Continuation | undefined {
	let used = 0;
	return (message) => {
		if (!isEmptyAssistantTurn(message) || used >= max) return undefined;
		used += 1;
		return {
			entries: [{ type: "custom_message", customType: "mellum-guard", content: NUDGE_TEXT, display: true }],
			continue: true,
		};
	};
}

export function callKey(toolName: string, input: unknown): string {
	const stable = (value: unknown): unknown => {
		if (Array.isArray(value)) return value.map(stable);
		if (value && typeof value === "object") {
			return Object.fromEntries(
				Object.entries(value as Record<string, unknown>)
					.sort(([a], [b]) => a.localeCompare(b))
					.map(([k, v]) => [k, stable(v)]),
			);
		}
		return value;
	};
	return `${toolName}\u0000${JSON.stringify(stable(input))}`;
}

function pathOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const record = input as Record<string, unknown>;
	for (const key of ["path", "filePath", "file_path"]) {
		if (typeof record[key] === "string") return record[key] as string;
	}
	return undefined;
}

export const newFileOnlyWrite =
	(exists: (path: string) => boolean): Guard =>
	(call) => {
		if (call.toolName !== "write") return undefined;
		const path = pathOf(call.input);
		if (!path || !exists(path)) return undefined;
		return {
			block: true,
			reason:
				`${path} exists; write replaces the entire file. ` +
				`Use edit for an existing file: give the exact old text and the new text.`,
		};
	};

function commandOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const record = input as Record<string, unknown>;
	for (const key of ["command", "cmd"]) {
		if (typeof record[key] === "string") return record[key] as string;
	}
	return undefined;
}

/** Commands that run a long-lived server in the foreground and never return. */
const SERVER_START =
	/\b(uvicorn|gunicorn|hypercorn|daphne|waitress-serve)\b|\bflask\s+run\b|\bpython\d?\s+-m\s+(http\.server|flask)\b|\bmanage\.py\s+runserver\b|\bfastapi\s+(dev|run)\b|\brails\s+server\b|\bnpm\s+(start|run\s+dev)\b|\bpython\d?(?:\.\d+)?\s+(?:-[\w-]+\s+)*(?:[\w.-]+\/)*(?:app|main|server|serve|asgi|wsgi)\.py\b/;

/** Whether a shell command is already detached (nohup, or a background `&` operator). */
export function isBackgrounded(command: string): boolean {
	if (/\bnohup\b/.test(command)) return true;
	// Ignore redirects that contain '&' (2>&1, &>, >&) before looking for a background '&'.
	const stripped = command.replace(/\d*>&\d*/g, " ").replace(/&>/g, " ");
	return /(^|[^&])&(\s|$)/.test(stripped.trim());
}

/** Read/search commands whose arguments may mention a server but never run one. */
const READONLY_FIRST = /^\s*(grep|rg|cat|less|more|head|tail|echo|printf|find|ls|awk|sed|sort|uniq|wc|diff|which|type|git)\b/;

/** A blocking server started in the foreground (so it would hang the run). */
export function isForegroundServer(command: string | undefined): boolean {
	if (!command) return false;
	if (READONLY_FIRST.test(command)) return false; // e.g. `grep uvicorn`, `cat app.py`
	return SERVER_START.test(command) && !isBackgrounded(command);
}

/** The non-blocking form: detached, logs aside, prints the pid to kill later. */
export function backgroundForm(command: string): string {
	return `nohup ${command.trim()} >/tmp/mellum-server.log 2>&1 & echo "server pid $!"`;
}

/** Block a foreground server start; it blocks forever and burns the time budget. */
export const serverGuard: Guard = (call) => {
	if (call.toolName !== "bash") return undefined;
	const command = commandOf(call.input);
	if (!isForegroundServer(command)) return undefined;
	return {
		block: true,
		reason:
			"That starts a server in the foreground; it blocks forever and burns your whole time budget. " +
			"You do not need a running server here — exercise an endpoint in process the way the tests do: " +
			'`from starlette.testclient import TestClient; TestClient(app).get("/...")`. ' +
			"If you truly must run it, start it in the background so it returns at once with a pid you can kill later: " +
			`\`${backgroundForm(command as string)}\`.`,
	};
};

/** Whether a bash command walks a directory tree: find, ripgrep (recursive by
 * default), recursive grep (-r/-R/--recursive), or `ls -R`. */
export function isTreeWalk(command: string): boolean {
	if (/\bfind\b/.test(command)) return true;
	if (/\b(rg|ripgrep)\b/.test(command)) return true;
	if (/\bgrep\b/.test(command) && /(?:\s-\w*[rR]|\s--recursive\b)/.test(command)) return true;
	if (/\bls\b.*\s-\w*R/.test(command)) return true;
	return false;
}

/** Absolute-path arguments in a command (whitespace- or start-delimited `/...` tokens).
 * A quoted regex like `sed 's/a/b/'` starts with a quote, not `/`, so it is not matched. */
export function absolutePathArgs(command: string): string[] {
	return (command.match(/(?:^|\s)(\/[^\s'";|&]+)/g) ?? []).map((s) => s.trim());
}

/** Block a recursive search that reaches OUTSIDE the workspace. The recorded pathology:
 * a worker ran `grep -rl pattern /Users /var /tmp …`, which crawls the whole machine and
 * hangs the run for minutes. A tree-walk confined to the workspace (relative paths, or
 * absolute paths under `root`) is allowed; one that names an absolute path outside it is not. */
export function confineSearch(root: string): Guard {
	const base = resolve(root);
	const isUnder = (p: string): boolean => {
		const r = resolve(base, p);
		return r === base || r.startsWith(`${base}/`);
	};
	return (call) => {
		if (call.toolName !== "bash") return undefined;
		const command = commandOf(call.input);
		if (!command || !isTreeWalk(command)) return undefined;
		const outside = absolutePathArgs(command).filter((p) => !isUnder(p));
		if (outside.length === 0) return undefined;
		return {
			block: true,
			reason:
				`That searches outside your workspace (${outside.slice(0, 3).join(", ")}). ` +
				`It scans the whole machine and hangs the run. Search only within your working folder: ` +
				`use relative paths (e.g. \`grep -rl pattern .\`) or paths under ${base}.`,
		};
	};
}

/** Tools after which an earlier call's result may legitimately differ. */
const MUTATING_TOOLS = new Set(["edit", "write", "bash"]);

export function createLoopBreaker(window = 20, threshold = 5): Guard {
	let recent: string[] = [];
	return (call) => {
		if (MUTATING_TOOLS.has(call.toolName)) {
			// An edit, write, or command may change what any repeated call returns:
			// forget the repeats, so an edit/test loop or a re-read after an edit
			// is never mistaken for a loop. Only unbroken repeats trip the breaker.
			recent = [];
			return undefined;
		}
		const key = callKey(call.toolName, call.input);
		const seen = recent.filter((entry) => entry === key).length;
		if (seen >= threshold) {
			return {
				block: true,
				reason:
					`You have already run this exact ${call.toolName} call ${seen} times ` +
					`with nothing changed in between, and the result will not change. ` +
					`Do not repeat it. Use what you already know and take the next concrete action.`,
			};
		}
		recent.push(key);
		if (recent.length > window) recent.shift();
		return undefined;
	};
}

export function createStepBudget(max: number): Guard {
	let calls = 0;
	return () => {
		calls += 1;
		if (calls <= max) return undefined;
		return {
			block: true,
			reason: `Tool-call budget of ${max} reached. Summarise what was done and what remains, then stop.`,
		};
	};
}

/** The MELLUM_GUARDS environment variable (JSON) replaces ENABLED, for live smokes such as {"stepBudget":1}. */
export function resolveEnabled(defaults: typeof ENABLED, env: string | undefined): typeof ENABLED {
	if (!env) return defaults;
	try {
		const parsed = JSON.parse(env);
		return parsed && typeof parsed === "object" ? parsed : defaults;
	} catch {
		return defaults;
	}
}

export function activeGuards(enabled = ENABLED, cwd = process.cwd()): Guard[] {
	const guards: Guard[] = [];
	if (enabled.newFileOnlyWrite) {
		guards.push(newFileOnlyWrite((p) => existsSync(isAbsolute(p) ? p : resolve(cwd, p))));
	}
	if (enabled.loopBreaker) guards.push(createLoopBreaker());
	if (enabled.blockForegroundServer) guards.push(serverGuard);
	if (enabled.confineToWorkspace) guards.push(confineSearch(cwd));
	if (enabled.stepBudget) guards.push(createStepBudget(enabled.stepBudget));
	return guards;
}

export interface GuardSet {
	toolCall(event: { toolName: string; input: unknown }): Decision;
	turnEnd(event: { message?: MessageLike }): void;
	beforeSettle(): Continuation | undefined;
}

/** One run's worth of guard state. Mode creates a fresh set per span; the child extension creates one per session. */
export function createGuardSet(enabled: typeof ENABLED = resolveEnabled(ENABLED, process.env.MELLUM_GUARDS)): GuardSet {
	const guards = activeGuards(enabled);
	const nudge = enabled.emptyFinalNudge ? createEmptyFinalNudge(enabled.emptyFinalNudge) : undefined;
	let lastAssistant: MessageLike | undefined;
	return {
		toolCall(event) {
			for (const guard of guards) {
				const decision = guard({ toolName: event.toolName, input: event.input });
				if (decision?.block) return decision;
			}
			return undefined;
		},
		turnEnd(event) {
			if (event?.message?.role === "assistant") lastAssistant = event.message;
		},
		beforeSettle() {
			// Pi reports canContinue=false on the final turn, which is exactly where an
			// empty final lands; agent_before_settle still honours continue:true there
			// (probed 2026-10-08 in print mode).
			if (!nudge || !lastAssistant) return undefined;
			const decision = nudge(lastAssistant);
			if (decision) lastAssistant = undefined;
			return decision;
		},
	};
}

const readIfExists = (p: string) => (existsSync(p) ? readFileSync(p, "utf8") : undefined);

export default function (pi: { on: (event: string, handler: (event: any, ctx?: any) => unknown) => void }, options: { fetch?: typeof fetch } = {}) {
	const set = createGuardSet();
	const home = process.env.HOME || homedir();
	pi.on("tool_call", (event) => {
		const decision = set.toolCall(event);
		return decision;
	});
	pi.on("turn_end", (event) => {
		set.turnEnd(event);
		return undefined;
	});
	pi.on("agent_before_settle", () => {
		const result = set.beforeSettle();
		return result;
	});
}
