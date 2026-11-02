/** Remedy unit (prompt): tell the model to take the file layout from the project's own spec,
 * instead of inventing one. Agnostic — it names no path, file or route of any suite; the model
 * reads the layout from the spec itself. Appends one line to each user message. */
import type { PiLike, UnitMeta } from "../install.ts";

const LINE =
	"Read the project's own spec or notes for where each file and route belongs, and create " +
	"files at exactly those paths — do not invent your own layout.";

export const meta: UnitMeta = {
	pathology: "Invents its own file layout instead of the one the spec names (e.g. writes main.py, skips the named folders)",
	does: "Appends one line telling the model to take the file layout from the project's spec, not invent one",
	lesson: "",
	evidence: "new unit; unmeasured",
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
