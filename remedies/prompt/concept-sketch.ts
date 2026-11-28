/** Remedy unit (prompt): coarse-to-fine, the idea behind Next-Concept Modeling (HazyResearch/ncm)
 * carried over to code. Instead of building one file to completion and then the next — which lets
 * the layout drift and earlier parts break — sketch the whole app first (the coarse concepts: every
 * file, its signatures, a one-line plan), then fill the bodies one at a time (the fine detail).
 * Agnostic — it names no path, file or route of any suite. Appends one line to each user message.
 *
 * This is the prose v1: it ASKS for coarse-to-fine. The enforced v2 (a harness that runs the sketch
 * pass and the refine passes as separate turns, optionally in parallel per file) is designed in
 * docs/superpowers/research/2026-11-03-next-concept-remedy.md and is the version expected to land,
 * since this project has measured that prose rules land unreliably on a small model. */
import type { PiLike, UnitMeta } from "../install.ts";

const LINE =
	"Work coarse to fine. FIRST, lay out every file the spec implies as a skeleton only — the " +
	"imports, the classes and functions with their real signatures, and each body left as a single " +
	"`...` or a `# TODO:` naming what it must do — plus a short plan comment listing each requirement. " +
	"Do not implement any body yet. THEN, once the whole skeleton stands, go back and fill one body " +
	"at a time, running the project's tests after each. Never finish one file before the others exist.";

export const meta: UnitMeta = {
	pathology: "Builds each file to completion in turn, so the layout drifts and earlier parts break",
	does: "Sketch every file first (signatures and stubs), then fill the bodies one at a time",
	lesson: "",
	evidence: "new unit (prose v1); unmeasured, a lead, see the next-concept research note",
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
