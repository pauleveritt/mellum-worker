/** Remedy unit (opt-in, unmeasured as a remedy): Keeps a TODO.md the model writes, follows and amends on failures. Re-exports extensions/mellum-plan.ts unchanged. */
import ext from "../../extensions/mellum-plan.ts";
import { keepingTools, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Loses track of a long task part-way through",
	does: "Keeps a TODO.md the model writes, follows and amends on failures",
	lesson: "M7",
	evidence: "unit-tested; not measured on the suites",
};

/** Loads the extension unchanged; any tool it registers is kept by `context/narrow-tools`. */
export default (pi: any) => ext(keepingTools(pi));
