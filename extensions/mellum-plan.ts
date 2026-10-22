/**
 * mellum-plan: plan before you implement.
 *
 * The recorded pathology is "declares done without doing the work": on a
 * multi-phase build the worker reads the phase spec and edits straight away,
 * satisfying the visible page while dropping a data-model rule no visible test
 * checks (the phase-4 id/status miss). A developer plans first — lists the
 * files and the whole contract — so a later requirement is not forgotten.
 *
 * This makes planning structural rather than a prompt line the model can reason
 * past: the FIRST edit/write is blocked until the worker has stated a plan (a
 * substantive assistant text turn). Reads, greps and shell commands are never
 * gated — exploration before a plan is fine. Once a plan exists the gate never
 * fires again. The block reason carries the cumulative-contract lesson.
 */

export interface ToolCall {
	toolName: string;
	input: unknown;
}

export interface Block {
	block: true;
	reason: string;
}

interface MessageLike {
	role?: string;
	content?: unknown;
}

export const PLAN_REASON =
	"[mellum-plan] Plan before you edit. First, in a message (not a tool call), write your plan: " +
	"(1) the files you will change, and (2) a checklist of EVERY requirement from the whole spec — " +
	"including data-model rules that no visible test checks, such as a unique, automatically-assigned " +
	"id, or a status that defaults to a specific value. Then make your edits. Keeping the whole " +
	"contract in view is what stops a later requirement from being dropped.";

const EDIT_TOOLS = new Set(["edit", "write"]);

/** A plan is a substantive assistant text turn — not thinking-only, not a tool call, not whitespace. */
export function isPlanTurn(message: MessageLike | undefined): boolean {
	if (!message || message.role !== "assistant") return false;
	const blocks = Array.isArray(message.content) ? (message.content as Record<string, unknown>[]) : [];
	return blocks.some((b) => b && b.type === "text" && typeof b.text === "string" && b.text.trim() !== "");
}

export interface PlanGate {
	toolCall(call: ToolCall): Block | undefined;
	turnEnd(event: { message?: MessageLike }): void;
}

/** Blocks the first edit/write until a plan turn has happened; then stays out of the way. */
export function createPlanGate(): PlanGate {
	let planned = false;
	return {
		toolCall(call) {
			if (!EDIT_TOOLS.has(call.toolName) || planned) return undefined;
			return { block: true, reason: PLAN_REASON };
		},
		turnEnd(event) {
			if (isPlanTurn(event?.message)) planned = true;
		},
	};
}

export default function (pi: { on: (event: string, handler: (event: any) => unknown) => void }): void {
	const gate = createPlanGate();
	pi.on("tool_call", (event) => gate.toolCall(event));
	pi.on("turn_end", (event) => gate.turnEnd(event));
}
