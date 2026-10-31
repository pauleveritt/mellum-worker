/**
 * mellum-plan: identify the problem, write a TODO.md, follow it, amend it on
 * failures, repeat until done.
 *
 * The recorded pathology is "declares done without doing the work": on a
 * multi-phase build the worker reads the spec, edits straight away, satisfies
 * the visible page and drops a requirement no visible test checks (the phase-4
 * id/status miss, the phase-6 aggregation keys). A developer plans first — lists
 * the whole contract as steps — then works the list, and when something fails it
 * updates the list and goes round again.
 *
 * This gates on a concrete artifact, a `TODO.md`, not a flaky "text turn" that a
 * thinking+tool-call model never emits (the earlier design deadlocked). Before
 * the first source edit the gate blocks and asks for a `TODO.md` — a checklist
 * of every step to satisfy the whole spec. Writing the `TODO.md` is always
 * allowed; once it exists the worker is free to implement and FOLLOW it. The
 * reason tells the worker to amend the TODO.md from the test failures and loop
 * (the `mellum-ncm` gate supplies the re-run-until-green pressure). Bounded: it
 * fails open after `max` blocks, so it can never deadlock the build.
 */
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

export interface ToolCall {
	toolName: string;
	input: unknown;
}

export interface Block {
	block: true;
	reason: string;
}

export const PLAN_REASON =
	"[mellum-plan] Fail to plan, plan to fail — even for a simple task a plan beats " +
	"flailing. First gather information: read the spec and the code. Then write a " +
	"TODO.md — a checklist of every step to satisfy the WHOLE spec (each route, each " +
	"model field, each exact output key, each migration), not only what a visible test " +
	"checks. Then follow TODO.md: do each step and check it off, run the tests; if " +
	"anything is still failing, go back to TODO.md, update it with what failed, and run " +
	"again — repeat until every step is checked off and the tests pass. (Writing TODO.md " +
	"itself is allowed right now.)";

const DEFAULT_MAX = 2;
const EDIT_TOOLS = new Set(["edit", "write"]);

function pathOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const record = input as Record<string, unknown>;
	for (const key of ["path", "filePath", "file_path"]) {
		if (typeof record[key] === "string") return record[key] as string;
	}
	return undefined;
}

/** The plan file, by basename, anywhere and case-insensitive. */
export function isTodoPath(path: string): boolean {
	const base = (path || "").split(/[\\/]/).pop() || "";
	return base.toLowerCase() === "todo.md";
}

/** Whether a non-empty TODO.md exists under cwd. */
export function todoExists(cwd: string): boolean {
	try {
		return readFileSync(resolve(cwd, "TODO.md"), "utf8").trim().length > 0;
	} catch {
		return false;
	}
}

/** MELLUM_PLAN (JSON) overrides the block cap, e.g. {"max":1}; 0 disables the gate. */
export function resolvePlanMax(env: string | undefined): number {
	if (!env) return DEFAULT_MAX;
	try {
		const parsed = JSON.parse(env);
		if (parsed && typeof parsed === "object" && Number.isInteger(parsed.max) && parsed.max >= 0) {
			return parsed.max;
		}
	} catch {
		// fall through to default
	}
	return DEFAULT_MAX;
}

export interface PlanGate {
	toolCall(call: ToolCall): Block | undefined;
}

/**
 * Blocks the first source edit/write until a TODO.md exists, then stays out of
 * the way (the worker follows and amends the plan). Writing the TODO.md is never
 * blocked. Fails open after `max` blocks so a model that will not write a plan
 * still builds.
 */
export function createPlanGate(max: number, hasTodo: () => boolean): PlanGate {
	let blocks = 0;
	return {
		toolCall(call) {
			if (!EDIT_TOOLS.has(call.toolName)) return undefined;
			const path = pathOf(call.input);
			if (path && isTodoPath(path)) return undefined; // making/updating the plan is always allowed
			if (hasTodo()) return undefined; // the plan exists — follow it
			if (blocks >= max) return undefined; // fail open: never deadlock the build
			blocks += 1;
			return { block: true, reason: PLAN_REASON };
		},
	};
}

export default function (
	pi: { on: (event: string, handler: (event: any, ctx?: any) => unknown) => void },
	options: { hasTodo?: () => boolean } = {},
): void {
	const max = resolvePlanMax(process.env.MELLUM_PLAN);
	const hasTodo = options.hasTodo ?? (() => todoExists(process.cwd()));
	const gate = createPlanGate(max, hasTodo);
	pi.on("tool_call", (event) => gate.toolCall(event));
}
