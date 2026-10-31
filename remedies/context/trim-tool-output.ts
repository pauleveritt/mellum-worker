/** Remedy unit: a tool result too big for the context is trimmed, with a note on how to get the rest. */
import { type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Reads more than the context holds, so Pi compacts it and the model loses what it read first",
	does: "Trims a read, bash, grep, find or ls result over 8,000 characters and says how to search for the rest",
	lesson: "E2",
	evidence: "context-overflow screen: 8 notes read whole, 2 compactions, 8 notes read again",
};

/** Characters a single tool result may put into the context (about 2,000 tokens). */
export const LIMIT = 8000;
const TRIMMED = new Set(["read", "bash", "grep", "find", "ls"]);

export function install(pi: PiLike): void {
	pi.on("tool_result", (event: any) => {
		if (!TRIMMED.has(event?.toolName)) return undefined;
		const content: any[] = event.content ?? [];
		const text = content.filter((c) => c.type === "text").map((c) => c.text ?? "").join("");
		if (text.length <= LIMIT) return undefined;
		const n = (x: number) => x.toLocaleString("en-US");
		const note = `\n\n[trimmed: showing ${n(LIMIT)} of ${n(text.length)} characters. ` +
			"Do not read the whole of it; get the part you need: search with `grep -n \"<what you need>\" <file>`, " +
			"or read a part with offset and limit.]";
		return { content: [{ type: "text", text: text.slice(0, LIMIT) + note }, ...content.filter((c) => c.type !== "text")] };
	});
}

export default install;
