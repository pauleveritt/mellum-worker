/** Remedy unit (prompt): cut the per-turn thinking. Mellum exposes no reasoning-effort dial
 * (supportsReasoningEffort: false) and enable_thinking=false pollutes the content channel, so the
 * only working lever is the prompt — tell the worker to reason in one short sentence per action.
 * A denser turn costs fewer turns, so a per-step turn cap covers the work instead of cutting it off.
 * Agnostic: names no suite, file or route. Appends one line to each user message. Off by default
 * (in no preset). Measured as a lead on medium (median 10 -> 16 under a turn cap):
 * docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md. */
import type { PiLike, UnitMeta } from "../install.ts";

const LINE =
	"Think briefly — reason in one short sentence before each action, then act; do not debate " +
	"back and forth or restate your plan. A concise turn is the goal, not a long one.";

export const meta: UnitMeta = {
	pathology: "Spends many turns thinking per step, so a turn cap starves the bigger steps",
	does: "Tells the model to reason in one short sentence per action, so each step costs fewer turns",
	lesson: "",
	evidence:
		"screen: medium median 10 -> 16, floor 8 -> 15 under a turn cap (docs/superpowers/research/2026-11-06-medium-cap-thinking-digest.md); a lead, off by default",
};

/** Append `line` to a user message's content, whether it is a plain string or content blocks. */
function append(content: any, line: string): any {
	if (typeof content === "string") return `${content}\n\n${line}`;
	if (Array.isArray(content)) return [...content, { type: "text", text: `\n\n${line}` }];
	return content;
}

export function install(pi: PiLike): void {
	pi.on("before_provider_request", (event) => {
		const payload = event?.payload;
		if (!payload || !Array.isArray(payload.messages)) return undefined;
		return {
			...payload,
			messages: payload.messages.map((m: any) => (m.role === "user" ? { ...m, content: append(m.content, LINE) } : m)),
		};
	});
}

export default (pi: PiLike) => install(pi);
