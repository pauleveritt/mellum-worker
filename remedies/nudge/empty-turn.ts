/** Remedy unit: when a turn ends with no text and no tool call mid-task, ask for one more turn. */
import { createEmptyFinalNudge } from "../../extensions/mellum-guards.ts";
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Ends a turn empty, part-way through the task",
	does: "Restates the goal and asks for one more turn (at most 3)",
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
	pi.on("agent_before_settle", (event: any) => {
		if (!last) return undefined;
		const decision = nudge(last);
		if (!decision) return undefined;
		last = undefined;
		// Pi keeps the entries the last handler returns, so keep the earlier handlers' too.
		return { ...decision, entries: [...(event?.entries ?? []), ...decision.entries] };
	});
}

export default (pi: PiLike) => install(pi);
