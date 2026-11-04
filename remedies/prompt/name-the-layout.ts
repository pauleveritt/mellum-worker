/** Remedy unit (prompt): tell the model to take the file layout from the project's own spec,
 * instead of inventing one. Agnostic — it names no path, file or route of any suite; the model
 * reads the layout from the spec itself. One explicit instruction per task. */
import { randomUUID } from "node:crypto";
import { INJECTED_REMEDY_PREFIX, workerTask } from "../../extensions/mellum-task.ts";
import type { PiLike, UnitMeta } from "../install.ts";

const LINE =
	"Read the project's own spec or notes for where each file and route belongs, and create " +
	"files at exactly those paths — do not invent your own layout.";

export const meta: UnitMeta = {
	pathology: "Invents its own file layout instead of the one the spec names",
	does: "Injects the spec-layout instruction once per task",
	lesson: "",
	evidence: "task-scoped delivery verified locally; coding effect unmeasured",
};

export function install(pi: PiLike): void {
	let vanillaTask: object | null = null;
	let injection: { task: object; message: any; published: boolean } | undefined;
	const enabled = () => pi.isRemedyEnabled?.() ?? true;
	const task = () => {
		const worker = workerTask(pi);
		return worker === undefined ? vanillaTask : worker;
	};
	const own = (m: any) => m.role === "custom" && m.customType === "Injected" && m.details?.remedy === "prompt/name-the-layout";
	const messageFor = (scope: object) => {
		if (injection?.task !== scope) {
			injection = {
				task: scope,
				published: false,
				message: {
					role: "custom", customType: "Injected", display: true,
					content: `${INJECTED_REMEDY_PREFIX}prompt/name-the-layout]\n${LINE}`,
					details: { remedy: "prompt/name-the-layout", taskId: randomUUID() },
					timestamp: Date.now(),
				},
			};
		}
		return injection.message;
	};
	// Lifecycle and cleanup must run while disabled too, so toggling cannot leak
	// an old instruction or lose the boundary of a task already in progress.
	const lifecycle = { whileDisabled: true };
	pi.on("session_start", () => { vanillaTask = null; injection = undefined; }, lifecycle);
	pi.on("before_agent_start", (event) => {
		if (event.messageType !== "custom" || !vanillaTask) vanillaTask = {};
		const scope = task();
		if (!enabled() || !scope || injection?.task === scope) return undefined;
		const message = messageFor(scope);
		injection!.published = true;
		return { message };
	}, lifecycle);
	pi.on("agent_settled", () => { vanillaTask = null; }, lifecycle);
	pi.on("context", (event) => {
		if (!Array.isArray(event.messages)) return undefined;
		const scope = enabled() ? task() : null;
		const current = scope ? messageFor(scope) : undefined;
		let present = false;
		const messages = event.messages.filter((m: any) => {
			if (!own(m)) return true;
			if (!current || present || m.details.taskId !== current.details.taskId) return false;
			present = true;
			return true;
		});
		// Mid-task enable or compaction: restore the same instruction in context,
		// publishing a late first injection once, without triggering another turn.
		if (current && !present) {
			messages.push(current);
			if (!injection!.published && pi.sendMessage) {
				pi.sendMessage(current, { triggerTurn: false });
				injection!.published = true;
			}
		}
		return { messages };
	}, lifecycle);
}

export default (pi: PiLike) => install(pi);
