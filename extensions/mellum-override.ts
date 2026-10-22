/**
 * mellum-override — edit the system prompt the worker is fed, live, from a file
 * (a Pi extension; agnostic, the dashboard's write side).
 *
 * Reads an override file (`$MELLUM_PROMPT_OVERRIDE`, default
 * `~/.pi/agent/mellum-prompt-override.json`, shape
 * `{"system"?: string, "append"?: string}`) at each turn boundary and applies
 * it to the request: `system` replaces the system prompt outright, `append`
 * adds to it. The dashboard writes the file; any Pi run that loads this
 * extension obeys it on the very next turn, so you can edit the prompt while a
 * run is in flight and watch the effect.
 *
 * Editing the system prompt deliberately changes the cached prefix, so a run
 * under an override forgoes prompt-cache reuse for that run — that is the point.
 *
 * Self-contained: Node `fs` + Pi hooks; loads with `-e` or `--pi-extension`.
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";

export interface Override {
	system?: string;
	append?: string;
}

/** Parse the override file's text; anything unparseable or empty is "no override". */
export function parseOverride(text: string): Override {
	try {
		const o = JSON.parse(text);
		const out: Override = {};
		if (typeof o?.system === "string" && o.system.trim()) out.system = o.system;
		if (typeof o?.append === "string" && o.append.trim()) out.append = o.append;
		return out;
	} catch {
		return {};
	}
}

/**
 * Apply an override to a request's messages, returning a new array. `system`
 * replaces the system message (or inserts one at the front if absent); `append`
 * adds to whatever system prompt is there. `system` wins over `append`.
 */
export function applyOverride(messages: any[], override: Override): any[] {
	if (!override.system && !override.append) return messages;
	const msgs = messages.map((m) => ({ ...m }));
	const idx = msgs.findIndex((m) => m?.role === "system");
	const base = idx >= 0 ? textOf(msgs[idx].content) : "";
	let system = base;
	if (override.system) system = override.system;
	if (override.append) system = system ? `${system}\n\n${override.append}` : override.append;
	if (idx >= 0) msgs[idx] = { role: "system", content: system };
	else msgs.unshift({ role: "system", content: system });
	return msgs;
}

function textOf(content: unknown): string {
	if (typeof content === "string") return content;
	if (Array.isArray(content)) {
		return content
			.filter((b: any) => b?.type === "text" && typeof b.text === "string")
			.map((b: any) => b.text)
			.join(" ");
	}
	return "";
}

function overridePath(): string {
	return (
		process.env.MELLUM_PROMPT_OVERRIDE ||
		`${process.env.HOME || homedir()}/.pi/agent/mellum-prompt-override.json`
	);
}

export default function (pi: any) {
	pi.on("before_provider_request", (event: any, ctx: any) => {
		let override: Override = {};
		try {
			override = parseOverride(readFileSync(overridePath(), "utf8"));
		} catch {
			return undefined; // no override file -> leave the request untouched
		}
		const payload = event?.payload;
		if ((override.system || override.append) && payload && Array.isArray(payload.messages)) {
			payload.messages = applyOverride(payload.messages, override);
			ctx?.ui?.notify?.("mellum-override: system prompt overridden from the dashboard", "info");
			return payload;
		}
		return undefined;
	});
}
