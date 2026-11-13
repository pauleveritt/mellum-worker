/** Remedy unit: replace Pi's system prompt with the worker's short task prompt. */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Follows a long system prompt instead of the files",
	does: "Swaps in the 643-character worker prompt",
	lesson: "M2",
	evidence: "screen: 3/3 against 1/3 on Easy (2026-10-29), 3/9 against 3/9 earlier; not decided",
};

const SHIPPED = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "prompts", "mellum-worker.md");

export function install(pi: PiLike, opts: { promptFile?: string } = {}): void {
	const prompt = readFileSync(opts.promptFile ?? process.env.MELLUM_MODE_PROMPT ?? SHIPPED, "utf8").trim();
	pi.on("before_provider_request", (event) => {
		const payload = event?.payload;
		if (!payload || !Array.isArray(payload.messages)) return undefined;
		const system = { role: "system", content: prompt };
		const rest = payload.messages.filter((m: any) => m.role !== "system");
		return { ...payload, messages: [system, ...rest] };
	});
}

export default (pi: PiLike) => install(pi);
