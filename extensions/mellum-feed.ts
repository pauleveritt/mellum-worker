/**
 * mellum-feed — an agnostic realtime feed of a Pi worker run (a Pi extension).
 *
 * Hooks Pi's turn/tool/settle events and appends one compact NDJSON line per
 * event to `$MELLUM_FEED` (default `~/.pi/agent/mellum-feed.ndjson`). Any Pi
 * session that loads it — direct, Mellum Mode, any model — produces the same
 * feed, so a dashboard (or any consumer) can tail it without knowing anything
 * about the ladder or where the trace temp files live.
 *
 * Self-contained: Node `fs` + Pi hooks only, no Pi-internal imports; loads with
 * `-e extensions/mellum-feed.ts` or the ladder's `--pi-extension`.
 *
 * Events (one per line): {t, kind, ...}
 *   kind "turn"    — an assistant turn: { think, call }
 *   kind "tool"    — a tool call starting: { name }
 *   kind "settled" — the run finished
 */
import { appendFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname } from "node:path";

/** One NDJSON feed line: timestamp + kind + the event's extra fields. */
export function feedLine(kind: string, extra: Record<string, unknown> = {}): string {
	return JSON.stringify({ t: Date.now(), kind, ...extra }) + "\n";
}

/** Pull the thinking text and the (first) tool call out of an assistant turn. */
export function turnFields(message: unknown): { think: string; call: string } {
	let think = "";
	let call = "";
	const content = (message as { content?: unknown })?.content;
	if (Array.isArray(content)) {
		for (const b of content) {
			if (!b || typeof b !== "object") continue;
			const block = b as Record<string, unknown>;
			if (block.type === "text" && typeof block.text === "string" && block.text.trim()) {
				think = block.text;
			}
			if (block.type === "toolCall" && typeof block.name === "string") {
				const args = JSON.stringify(block.arguments ?? {});
				call = `${block.name}(${args.slice(0, 90)})`;
			}
		}
	}
	return { think: think.slice(0, 200), call };
}

/** The text of a message, whether its content is a string or an array of blocks. */
function textOf(message: unknown): string {
	const content = (message as { content?: unknown })?.content;
	if (typeof content === "string") return content;
	if (Array.isArray(content)) {
		return content
			.filter((b) => b && typeof b === "object" && (b as any).type === "text" && typeof (b as any).text === "string")
			.map((b) => (b as any).text)
			.join(" ");
	}
	return "";
}

/** The prompts a request carries: the system prompt and the latest task/injected message. */
export function promptFields(messages: unknown): { system: string; task: string } {
	if (!Array.isArray(messages)) return { system: "", task: "" };
	const system = messages.find((m) => (m as any)?.role === "system");
	const userish = messages.filter((m) => {
		const role = (m as any)?.role;
		return role === "user" || role === "custom";
	});
	const last = userish[userish.length - 1];
	// Wide enough for the dashboard to show the full context being fed, not a teaser.
	return { system: textOf(system).slice(0, 8000), task: textOf(last).slice(0, 8000) };
}

function feedPath(): string {
	return process.env.MELLUM_FEED || `${process.env.HOME || homedir()}/.pi/agent/mellum-feed.ndjson`;
}

export default function (pi: { on: (event: string, handler: (ev: any, ctx?: any) => unknown) => void }) {
	const path = feedPath();
	const write = (kind: string, extra: Record<string, unknown> = {}) => {
		try {
			mkdirSync(dirname(path), { recursive: true });
			appendFileSync(path, feedLine(kind, extra));
		} catch {
			// a feed is best-effort; never throw into Pi
		}
	};
	let lastPrompt = "";
	pi.on("context", (event: any) => {
		const { system, task } = promptFields(event?.messages);
		const key = `${system}\u0000${task}`;
		if ((system || task) && key !== lastPrompt) {
			lastPrompt = key;
			write("prompt", { system, task });
		}
		return undefined;
	});
	pi.on("tool_call", (event: any) => {
		if (event?.toolName) write("tool", { name: event.toolName });
		return undefined;
	});
	pi.on("turn_end", (event: any) => {
		if (event?.message?.role === "assistant") {
			const { think, call } = turnFields(event.message);
			if (think || call) write("turn", { think, call });
		}
		return undefined;
	});
	pi.on("agent_settled", () => {
		write("settled");
		return undefined;
	});
}
