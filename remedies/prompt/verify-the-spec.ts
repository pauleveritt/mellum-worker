/** Remedy unit (prompt): make the model finish only after it has checked every requirement the
 * spec lists and actually run the project's own tests — not after reading files or starting a
 * server. Agnostic: it names no requirement, route, file or expected value; the model reads the
 * requirements from the spec itself. Appends one line to each user message. New unit; unmeasured
 * (easy-ladder, 2026-11-02); screened on Easy 2026-11-08, see its evidence. */
import type { PiLike, UnitMeta } from "../install.ts";

const LINE =
	"Before you finish, check that every requirement the spec lists is present in your code, and " +
	"run the project's own tests to confirm — do not finish while a requirement is unimplemented " +
	"or a test you can run is failing. Reading the files is not verification; run them.";

export const meta: UnitMeta = {
	pathology: "Declares done with a spec requirement unimplemented or unverified",
	does: "Tells the model to check every spec requirement and run the tests before finishing",
	lesson: "",
	evidence: "screen, n = 3, Easy, 2026-11-08: reached every request, title override still missed 3 of 3",
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
