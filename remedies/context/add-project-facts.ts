/** Remedy unit: add the project's facts (the `## Mellum` section of AGENTS.md, and the test
 * command) to each user message, so the model knows how this project is tested. */
import { readFileSync } from "node:fs";
import { factsBlock, readProjectFacts } from "../../extensions/mellum-facts.ts";
import { withFacts } from "../../extensions/mellum-worker.ts";
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Guesses how to run the tests instead of using the project's own command",
	does: "Appends the project facts (AGENTS.md `## Mellum`, test command) to user messages",
	lesson: "M1",
	evidence: "screen: 3/3 against 2/3 on Bronze (2026-10-29); a null in the page's record",
};

export function install(pi: PiLike, opts: { cwd?: string; env?: Record<string, string | undefined> } = {}): void {
	const facts = factsBlock(readProjectFacts(opts.cwd ?? process.cwd(), { read: (p) => readFileSync(p, "utf8") }, opts.env ?? process.env));
	pi.on("before_provider_request", (event) => {
		const payload = event?.payload;
		if (!facts || !payload || !Array.isArray(payload.messages)) return undefined;
		return { ...payload, messages: payload.messages.map((m: any) => (m.role === "user" ? withFacts(m, facts) : m)) };
	});
}

export default (pi: PiLike) => install(pi);
