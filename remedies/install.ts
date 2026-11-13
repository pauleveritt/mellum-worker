/**
 * Shared wiring for remedy units: one unit installs one behaviour on Pi's hooks.
 * A guard unit is a `ToolCall -> Decision` function on `tool_call`; nothing else.
 */
import type { Guard } from "../extensions/mellum-guards.ts";

export interface PiLike {
	on: (event: string, handler: (event: any, ctx?: any) => unknown) => void;
}

/** What the remedies list shows for a unit, read from each unit's `meta` export. */
export interface UnitMeta {
	pathology: string;
	does: string;
	lesson: string;
	evidence: string;
}

export function installGuard(pi: PiLike, guard: Guard): void {
	pi.on("tool_call", (event) => guard({ toolName: event.toolName, input: event.input }));
}

/** Tools that `context/narrow-tools` must keep besides the seven worker tools: anything a tool
 * unit or a learner's extension registered. Held on globalThis so every extension Pi loads in the
 * process sees the same list, however its modules are instantiated. */
const KEEP = ((globalThis as any).__mellumKeepTools ??= new Set<string>()) as Set<string>;

export function keepTool(name: string): void {
	KEEP.add(name);
}

export function keptTools(): ReadonlySet<string> {
	return KEEP;
}

/** Wrap a Pi so every tool an extension registers through it is also kept by narrow-tools. */
export function keepingTools<P extends object>(pi: P): P {
	return new Proxy(pi, {
		get(target: any, prop, receiver) {
			const value = Reflect.get(target, prop, receiver);
			if (prop !== "registerTool" || typeof value !== "function") return value;
			return (first: any, ...rest: unknown[]) => {
				const name = typeof first === "string" ? first : first?.name;
				if (typeof name === "string") keepTool(name);
				return value.call(target, first, ...rest);
			};
		},
	});
}
