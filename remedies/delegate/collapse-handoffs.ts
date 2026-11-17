/**
 * Remedy unit: after /mellum off, give the parent one handoff block per finished span
 * instead of every read, edit and command the worker ran. This is the `context`-hook span
 * collapse lifted out of the worker — it changes only what the PARENT sees, needs no mode
 * state, and the session itself keeps everything.
 */
import { existsSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { collapseHandoffs, MARK_ON } from "../../extensions/mellum-worker.ts";
import { textOf } from "../../extensions/mellum-record.ts";
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "A delegated worker floods the parent's context",
	does: "Collapses each finished span into one handoff block",
	lesson: "",
	evidence: "delegation behaviour lifted from the worker; not measured on its own",
};

export function install(pi: PiLike): void {
	const existsInCwd = (p: string) => existsSync(isAbsolute(p) ? p : resolve(process.cwd(), p));
	pi.on("context", (event: any) => {
		const messages = event?.messages;
		if (!Array.isArray(messages) || !messages.some((m: any) => textOf(m).includes(MARK_ON))) return undefined;
		const collapsed = collapseHandoffs(messages, { exists: existsInCwd });
		return collapsed === messages ? undefined : { messages: collapsed };
	});
}

export default install;
