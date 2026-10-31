/**
 * mellum-loop: the variable-extension workflow loop (orchestration core).
 *
 * Measurement showed an in-session gate is waited out by a weak model, so the
 * fix is to orchestrate workflows the model cannot skip — each a separate `pi`
 * invocation over one shared workspace with its OWN extension set (and its own
 * thinking budget). The loop, with TWO review gates and failures routed to the
 * right place:
 *
 *   planning     — gather info, write TODO.md.                 extensions: none
 *   plan_review  — is the plan the SIMPLEST that meets the     extensions: none
 *                  task? too complicated -> back to planning.
 *   coding       — follow TODO.md, implement.                  extensions: guards + surgical
 *   code_review  — conformance + simplicity against the spec;  extensions: none
 *                  unmet/over-complex -> back to coding.
 *   testing      — run the suite (the orchestrator).           (no pi)
 *   rubberduck   — on a REPEATED broken test: reason it out,   extensions: none
 *                  amend TODO.md, then back to coding.
 *
 * plan -> plan_review -> (complicated? back to plan) -> code -> code_review ->
 * test -> (broken? back to CODE). The plan stabilises early; iteration happens
 * on the code, not by re-planning every failure. The orchestrator IS the
 * plan/verify control, so the plan and verify gates are not loaded as extensions.
 *
 * Pure state core (which workflow is next, its extension set); the Pi-invoking
 * runner builds on it.
 */

export type Workflow =
	| "start"
	| "planning"
	| "plan_review"
	| "coding"
	| "code_review"
	| "testing"
	| "rubberduck"
	| "done";

export interface LoopState {
	workflow: Workflow;
	round: number;
	passed?: boolean;
}

export interface LoopOptions {
	maxRounds?: number;
	/** Rubber-duck before re-coding once a test failure has repeated this many rounds (default 1). */
	duckAfter?: number;
}

/** The five main workflow nodes, in order. */
export const WORKFLOWS: Workflow[] = ["planning", "plan_review", "coding", "code_review", "testing"];

/** The variable, minimal extension set per workflow (bare names). Only coding carries guards. */
export function workflowExtensions(workflow: Workflow): string[] {
	return workflow === "coding" ? ["mellum-guards", "mellum-surgical"] : [];
}

/** The loop's transition. Plan stabilises first; code iterates; failures route to the nearest step. */
export function nextStep(state: LoopState, options: LoopOptions = {}): LoopState {
	const maxRounds = options.maxRounds ?? 3;
	const duckAfter = options.duckAfter ?? 1;
	const round = state.round ?? 0;
	switch (state.workflow) {
		case "start":
			return { workflow: "planning", round };
		case "planning":
			return { workflow: "plan_review", round };
		case "plan_review":
			if (state.passed) return { workflow: "coding", round };
			if (round >= maxRounds) return { workflow: "done", round };
			return { workflow: "planning", round: round + 1 }; // too complicated -> simplify the plan
		case "coding":
			return { workflow: "code_review", round };
		case "code_review":
			if (state.passed) return { workflow: "testing", round };
			if (round >= maxRounds) return { workflow: "done", round };
			return { workflow: "coding", round: round + 1 }; // unmet/over-complex -> fix the code
		case "testing":
			if (state.passed) return { workflow: "done", round };
			if (round >= maxRounds) return { workflow: "done", round };
			if (round >= duckAfter) return { workflow: "rubberduck", round: round + 1 }; // repeated break
			return { workflow: "coding", round: round + 1 }; // broken -> back to CODE, not planning
		case "rubberduck":
			return { workflow: "coding", round };
		default:
			return { workflow: "done", round };
	}
}
