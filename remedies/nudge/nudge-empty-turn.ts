/** Remedy unit: when a turn ends with no text and no tool call mid-task, ask for one more turn. */
import { createEmptyFinalNudge } from "../../extensions/mellum-guards.ts";
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Ends a turn with no reply and no tool call, part-way through the task",
	does: "Restates the completion fact and asks for one more turn, at most 3 times",
	lesson: "M3",
	evidence: "ladder: 5 of 45 v3 runs, every failure; a null on the suites (M2)",
};

export function install(pi: PiLike, opts: { max?: number } = {}): void {
	const nudge = createEmptyFinalNudge(opts.max ?? 3);
	let last: any;
	pi.on("turn_end", (event) => {
		if (event?.message?.role === "assistant") last = event.message;
		return undefined;
	});
	pi.on("agent_before_settle", () => {
		if (!last) return undefined;
		const decision = nudge(last);
		if (decision) last = undefined;
		return decision;
	});
}

export default (pi: PiLike) => install(pi);
