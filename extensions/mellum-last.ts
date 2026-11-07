/**
 * `last`: the newest Mellum run record (Mode or Worker) at or under a directory, as a
 * Markdown table. Pure: front ends read the records files and show the text. Loads without
 * Pi, like mellum-learn.ts. Records are files a user can edit, so every field is checked.
 */
import { isUnder, readRecords, type RunLine } from "./mellum-learn.ts";

const DASH = "—";
const MAX_COMMANDS = 12;

const num = (v: unknown): number | undefined => (typeof v === "number" && Number.isFinite(v) ? v : undefined);
const str = (v: unknown): string | undefined => (typeof v === "string" ? v : undefined);
const isObject = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;
const thousands = (n: number) => n.toLocaleString("en-US");

function clip(text: string, max: number): string {
	return text.length <= max ? text : `${text.slice(0, max - 1)}…`;
}

/**
 * One table cell: newlines become spaces and every `|` is escaped, so a value never breaks the
 * row. Backslashes before a pipe are doubled first: in `a\\|b` (grep alternation) the pipe would
 * otherwise follow an escaped backslash and still split the cell.
 */
function cell(text: string, max = 200): string {
	return clip(text.replace(/\s*\r?\n\s*/g, " ").trim(), max).replace(/(\\*)\|/g, (_, bs: string) => `${bs}${bs}\\|`);
}

const timeOfEnd = (r: RunLine) => {
	const t = Date.parse(r.endedAt ?? "");
	return Number.isNaN(t) ? -Infinity : t;
};

/**
 * The newest record at or under `cwd` (as `learn` matches it) across the files' texts, by
 * `endedAt` as a time; on a tie the later line or file wins. Also the lines skipped.
 */
export function pickLast(texts: Array<string | undefined>, cwd: string): { record?: RunLine; skipped: { bad: number; old: number } } {
	const skipped = { bad: 0, old: 0 };
	let record: RunLine | undefined;
	for (const t of texts) {
		if (t === undefined) continue;
		const r = readRecords(t);
		skipped.bad += r.bad;
		skipped.old += r.old;
		for (const rec of r.records) {
			if (typeof rec.cwd !== "string" || !isUnder(rec.cwd, cwd)) continue;
			if (record === undefined || timeOfEnd(rec) >= timeOfEnd(record)) record = rec;
		}
	}
	return { record, skipped };
}

function localTime(iso: string | undefined): string {
	const t = iso === undefined ? Number.NaN : Date.parse(iso);
	if (Number.isNaN(t)) return "unknown time";
	const d = new Date(t);
	const p = (n: number) => String(n).padStart(2, "0");
	return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function timeOf(r: Record<string, unknown>): string {
	const wall = num(r.wallSeconds);
	const first = num(r.firstWriteSeconds);
	const parts = [wall === undefined ? DASH : `${wall} s`];
	if (first !== undefined) parts.push(`first write at ${first} s${wall !== undefined && wall > 0 ? ` (${Math.round((first / wall) * 100)}%)` : ""}`);
	else if (isObject(r.toolCalls) && !("edit" in r.toolCalls) && !("write" in r.toolCalls)) parts.push("no edit or write");
	return parts.join("; ");
}

function turnsOf(r: Record<string, unknown>): string {
	const requests = num(r.requests);
	if (requests === undefined) return DASH;
	const ft = isObject(r.finalTurn) ? r.finalTurn : undefined;
	if (!ft) return String(requests);
	const ended = ft.hadText === true ? "text" : ft.hadToolCall === true ? "a tool call" : "no text";
	const stop = str(ft.stopReason);
	return `${requests}; ended with ${ended}${stop ? ` (${stop})` : ""}`;
}

function toolCallsOf(r: Record<string, unknown>): string {
	if (!isObject(r.toolCalls)) return DASH;
	const counts = Object.entries(r.toolCalls)
		.filter((e): e is [string, number] => num(e[1]) !== undefined)
		.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
	const total = counts.reduce((s, [, n]) => s + n, 0);
	return total === 0 ? "0" : `${total}: ${counts.map(([k, n]) => `${k} ${n}`).join(", ")}`;
}

function commandsOf(r: RunLine): string {
	const cmds = r.commands ?? [];
	if (cmds.length === 0) return "none";
	const failed = cmds.filter((c) => c.failed).length;
	return `${cmds.length} run, ${failed} failed, last ${str(r.lastCommand) ?? DASH}`;
}

const pathsOf = (v: unknown): string[] => (Array.isArray(v) ? v.filter((p): p is string => typeof p === "string") : []);

function listOf(xs: string[]): string {
	return xs.length === 0 ? "none" : `${xs.length}: ${xs.join(", ")}`;
}

function tokensOf(r: Record<string, unknown>): string {
	if (!isObject(r.usage)) return DASH;
	const u = r.usage;
	const v = (k: string) => (num(u[k]) === undefined ? DASH : thousands(num(u[k]) as number));
	return `input ${v("input")} · cache read ${v("cacheRead")} · output ${v("output")}`;
}

function factsOf(r: Record<string, unknown>): string {
	if (r.facts === null) return "off";
	if (!isObject(r.facts)) return DASH;
	const chars = num(r.facts.chars);
	return `${str(r.facts.source) ?? "unknown"}${chars ? `, ${chars} chars` : ""}`;
}

function serverOf(r: Record<string, unknown>): string {
	if (!isObject(r.server)) return DASH;
	const s = r.server;
	if (s.match === true) return "settings match";
	if (s.match === null) return "unreadable";
	// A llama.cpp run records liveness (up, nCtx) and no settings match — that is not "differs".
	if (s.match === undefined) {
		if (s.up === true) {
			const ctx = num(s.nCtx);
			return ctx ? `up, ctx ${thousands(ctx)}` : "up";
		}
		if (s.up === false) return "down";
		return DASH;
	}
	const keys = (Array.isArray(s.diffs) ? s.diffs : []).map((d) => (isObject(d) ? str(d.key) : undefined)).filter(Boolean);
	return keys.length ? `differs: ${keys.join(", ")}` : "differs";
}

/** The record as Markdown: a header line, a Metric/Value table, a Command/Result table, the final reply quoted. */
export function formatLast(record: RunLine): string {
	const r = record as unknown as Record<string, unknown>;
	const who = `Mellum Worker (${str(r.activation) ?? "unknown"})`;
	// The full directory: the run may be in a subdirectory of the one asked about.
	const dir = (str(r.cwd) ?? "").replace(/(.)\/+$/, "$1") || DASH;
	const rows: Array<[string, string]> = [
		["Task", str(r.task) ?? DASH],
		["Time", timeOf(r)],
		["Turns", turnsOf(r)],
		["Tool calls", toolCallsOf(r)],
		["Tool errors", num(r.toolErrors) === undefined ? DASH : String(r.toolErrors)],
		["Commands", commandsOf(record)],
		["Files", listOf(pathsOf(r.files))],
	];
	const missing = pathsOf(r.filesMissingAtEnd);
	if (missing.length > 0) rows.push(["Missing", listOf(missing)]);
	const mutating = (record.commands ?? []).filter((c) => c.mutates).length;
	if (mutating > 0) rows.push(["Changed files via bash", plural(mutating, "command")]);
	rows.push(
		["Tokens", tokensOf(r)],
		["Facts", factsOf(r)],
		["Server", serverOf(r)],
		["Guards", `${plural(num(r.nudges) ?? 0, "nudge")}, ${plural(num(r.guardBlocks) ?? 0, "block")}`],
		["Versions", `mellum-worker ${str(r.version) ?? DASH} · prompt ${str(r.promptVersion) ?? DASH} · ${str(r.model) ?? DASH}`],
	);
	const lines = [`**mellum last**: ${who}, ${localTime(str(r.endedAt))}, ${dir}`, "", "| Metric | Value |", "|---|---|"];
	for (const [k, v] of rows) lines.push(`| ${k} | ${cell(v)} |`);
	const cmds = record.commands ?? [];
	if (cmds.length > 0) {
		lines.push("", "| Command | Result |", "|---|---|");
		for (const c of cmds.slice(0, MAX_COMMANDS)) {
			const result = `${c.failed ? "failed" : "ok"}${c.mutates ? ", changes files" : ""}`;
			lines.push(`| \`${cell(c.command.replace(/`/g, "'"), 120)}\` | ${result} |`);
		}
		if (cmds.length > MAX_COMMANDS) lines.push(`| … ${cmds.length - MAX_COMMANDS} more | |`);
	}
	// One quoted line: fences would open a code span mid-line, and long rules are noise.
	const flat = (str(r.finalReply) ?? "").replace(/`{3,}\w*/g, " ").replace(/([=\-*_])\1{3,}/g, "$1$1$1");
	const reply = clip(flat.replace(/\s+/g, " ").trim(), 300);
	lines.push("", `> ${reply || "(no final reply)"}`);
	return lines.join("\n");
}
