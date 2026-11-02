/** Remedy unit (prompt): prepend a focused role to the system prompt, so the coding model works
 * as a careful developer against the spec instead of drifting. Agnostic — names no suite, file or
 * route. Theory, unmeasured: see docs/superpowers/research/2026-11-02-easy-ladder.md. */
import type { PiLike, UnitMeta } from "../install.ts";

const ROLE = "You are an experienced, meticulous python developer working in a spec driven paradigm.";

export const meta: UnitMeta = {
	pathology: "Works without a focused, careful developer frame (ships typos, declares done unchecked)",
	does: "Prepends a meticulous experienced-Python-developer, spec-driven role to the system prompt",
	lesson: "",
	evidence: "theory; unmeasured (easy-ladder, 2026-11-02)",
};

/** Prepend `line` to a message's content, whether a plain string or content blocks. */
function prepend(content: any, line: string): any {
	if (typeof content === "string") return `${line}\n\n${content}`;
	if (Array.isArray(content)) return [{ type: "text", text: `${line}\n\n` }, ...content];
	return content;
}

export function install(pi: PiLike): void {
	pi.on("before_provider_request", (event) => {
		const payload = event?.payload;
		if (!payload || !Array.isArray(payload.messages)) return undefined;
		const messages = [...payload.messages];
		const i = messages.findIndex((m: any) => m.role === "system");
		if (i >= 0) messages[i] = { ...messages[i], content: prepend(messages[i].content, ROLE) };
		else messages.unshift({ role: "system", content: ROLE });
		return { ...payload, messages };
	});
}

export default (pi: PiLike) => install(pi);
