/**
 * mellum-loopguard: the loop-breaker on its own, for the read-only phases.
 *
 * The coder loads the full mellum-guards (write-confinement, server-blocking, the
 * empty-final nudge AND the loop-breaker). The read-only phases — plan, review_plan,
 * examine, review_code — must stay minimal, so they must NOT carry the write-oriented
 * guards. But a tool-using model still loops: it emits a call, reads the result, and
 * on its next turn re-decides to run the SAME read call rather than emit its answer.
 * examine is the sharp case — its reply must BE the acceptance test, so "done" is a
 * stop-and-write decision the model makes alone; on a fresh workspace a thinking model
 * whose reasoning is stripped between turns can re-issue `ls .` without bound (measured:
 * 1000+ events, one phase). The loop-breaker caps exactly that — after an unbroken run
 * of identical no-op calls it blocks with "you already ran this, take the next concrete
 * action", which forces the emit. It keys off repeats alone, so it is agnostic to the
 * model and the task: a no-op on a model that converges, a safety net on one that does
 * not. This is why it is its own tiny extension rather than the whole guard set.
 */

import { createLoopBreaker } from "./mellum-guards.ts";

/** The read phase gives up exploring and produces its answer after this many tool calls. */
const STEP_BUDGET = 60;

/**
 * The step budget: an arg-agnostic backstop for the runaway the loop-breaker misses. The model
 * already HAS every tool result in its context (each comes back as a toolResult message), so it is
 * not short of data — it re-calls because its reasoning is stripped between turns and it re-decides
 * to explore rather than act, or because it keeps retrying a tool this read-only phase does not
 * have (every `mkdir` errors, so it tries again). Neither is fixed by handing back a result it
 * already holds; both are fixed by telling it, past a generous call budget, that it has enough and
 * must now produce its answer. The loop-breaker catches a TIGHT exact-repeat fast; this catches a
 * VARYING-arg or error-retry runaway that never trips the exact match.
 */
function emitNudgeBudget(max: number) {
	let calls = 0;
	return () => {
		calls += 1;
		if (calls <= max) return undefined;
		return {
			block: true,
			reason:
				`You have made ${calls - 1} tool calls and already have the results of each in context — ` +
				`you are not missing information. Stop calling tools: do not read, list, search or create ` +
				`anything else. Produce your FINAL answer now, in full, and nothing else.`,
		};
	};
}

export default function (pi: { on: (event: string, handler: (event: any, ctx?: any) => unknown) => void }) {
	const breaker = createLoopBreaker();
	const budget = emitNudgeBudget(STEP_BUDGET);
	pi.on("tool_call", (event) => {
		const call = { toolName: event.toolName, input: event.input };
		const decision = breaker(call) || budget(call);
		return decision?.block ? decision : undefined;
	});
}
