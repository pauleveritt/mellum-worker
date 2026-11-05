/** Remedy unit: a tool-call budget that ends a runaway session with a reason to summarise. */
import { createStepBudget } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Calls tools with no end",
	does: "Blocks calls past a budget (default 200) and asks for a summary",
	lesson: "E7",
	evidence: "dormant in the worker; unmeasured",
};

export function install(pi: PiLike, opts: { max?: number } = {}): void {
	installGuard(pi, createStepBudget(opts.max ?? 200));
}

/** The budget from MELLUM_TURN_CAP, or 200 when unset or invalid. 200 is the frozen default
 * (effectively off); a delegated run sets it low (e.g. 25) so a worker that stalls is stopped
 * near a healthy step's turn count instead of thrashing. */
export function budgetFromEnv(env = process.env.MELLUM_TURN_CAP): number {
	const n = Number(env);
	return Number.isFinite(n) && n > 0 ? n : 200;
}

export default (pi: PiLike) => install(pi, { max: budgetFromEnv() });
