/** Remedy unit (opt-in, unmeasured as a remedy): Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py). Re-exports extensions/mellum-flow.ts unchanged. */
import ext from "../../extensions/mellum-flow.ts";
import { keepingTools, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Builds a multi-phase app in one go and breaks earlier phases",
	does: "Plan, frozen per-phase gates and checkpoints, as tools the agent calls (run with learn/code/flow_run.py)",
	lesson: "H1",
	evidence: "flow runs 2026-10-29: Bronze 4/4, Silver 18/18, Gold 30/34 (n = 1)",
};

/** Loads the extension unchanged; any tool it registers is kept by `context/narrow-tools`. */
export default (pi: any) => ext(keepingTools(pi));
