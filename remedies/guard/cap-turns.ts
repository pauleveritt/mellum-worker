/** Remedy unit: a tool-call budget that ends a runaway session with a reason to summarise. */
import { createStepBudget } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Keeps calling tools with no end, because Pi has no turn cap",
	does: "Blocks every call after a budget (default 200) and asks for a summary",
	lesson: "E7",
	evidence: "dormant in the worker; unmeasured",
};

export function install(pi: PiLike, opts: { max?: number } = {}): void {
	installGuard(pi, createStepBudget(opts.max ?? 200));
}

export default (pi: PiLike) => install(pi);
