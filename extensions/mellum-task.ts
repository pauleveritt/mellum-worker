/** Read-only worker lifecycle protocol for optional task-scoped remedies. */
import { textOf } from "./mellum-record.ts";

export const WORKER_TASK_QUERY = "mellum-worker:task-query";
export const INJECTED_REMEDY_PREFIX = "[Injected remedy: ";

export interface TaskBus {
	emit(channel: string, data: unknown): void;
	on(channel: string, handler: (data: any) => void): unknown;
}

/** undefined: no worker installed; null: worker off; object: the current span. */
export function workerTask(pi: { events?: TaskBus }): object | null | undefined {
	let task: object | null | undefined;
	pi.events?.emit(WORKER_TASK_QUERY, (value: object | null) => { task = value; });
	return task;
}

/** Custom instructions become user messages in provider payloads, but aren't task briefs. */
export function isInjectedRemedy(message: any): boolean {
	return textOf(message).startsWith(INJECTED_REMEDY_PREFIX);
}
