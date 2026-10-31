/** Remedy unit: offer the model only the seven worker tools, whatever else is installed. */
import { narrowTools } from "../../extensions/mellum-worker.ts";
import { keptTools, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Reaches for tools it uses badly (subagents, todo lists) instead of reading and editing",
	does: "Keeps read, grep, find, ls, bash, edit and write, plus tools your units register; drops the rest",
	lesson: "E6",
	evidence: "part of the Baseline Worker; not measured on its own",
};

export function install(pi: PiLike): void {
	pi.on("before_provider_request", (event) => {
		const payload = event?.payload;
		if (!payload || !Array.isArray(payload.tools)) return undefined;
		const out: any = { ...payload };
		narrowTools(payload, out);
		// Keep tools that later units or a learner's extension registered (see keepTool).
		const kept = keptTools();
		const nameOf = (t: any) => t?.function?.name ?? t?.name;
		if (kept.size) {
			const extra = payload.tools.filter((t: any) => kept.has(nameOf(t)));
			if (extra.length) out.tools = [...(out.tools ?? []), ...extra];
			const chosen = payload.tool_choice?.function?.name ?? payload.tool_choice?.name;
			if (chosen && kept.has(chosen)) out.tool_choice = payload.tool_choice;
		}
		return out;
	});
}

export default install;
