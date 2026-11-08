/** Shared lifecycle for optional, individually enabled task instructions. */
import { randomUUID } from "node:crypto";
import { INJECTED_REMEDY_PREFIX, workerTask } from "../extensions/mellum-task.ts";
import type { PiLike } from "./install.ts";

export function installTaskPrompt(pi: PiLike, remedy: string, line: string): void {
	let vanillaTask: object | null = null;
	let injection: { task: object; message: any; published: boolean } | undefined;
	const enabled = () => pi.isRemedyEnabled?.() ?? true;
	const task = () => {
		const worker = workerTask(pi);
		return worker === undefined ? vanillaTask : worker;
	};
	const own = (m: any) => m.role === "custom" && m.customType === "Injected" && m.details?.remedy === remedy;
	const messageFor = (scope: object) => {
		if (injection?.task !== scope) {
			injection = {
				task: scope,
				published: false,
				message: {
					role: "custom", customType: "Injected", display: true,
					content: `${INJECTED_REMEDY_PREFIX}${remedy}]\n${line}`,
					details: { remedy: remedy, taskId: randomUUID() },
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

