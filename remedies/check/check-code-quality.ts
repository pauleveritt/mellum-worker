/** Remedy unit (opt-in, unmeasured as a remedy): Runs the quality checks before the model may finish. Re-exports extensions/mellum-quality.ts unchanged. */
import ext from "../../extensions/mellum-quality.ts";
import { keepingTools, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Finishes with lint or type errors the grader counts as a fail",
	does: "Runs the quality checks before the model may finish",
	lesson: "M6",
	evidence: "unit-tested; not measured on the suites",
};

/** Loads the extension unchanged; any tool it registers is kept by `context/narrow-tools`. */
export default (pi: any) => ext(keepingTools(pi));
