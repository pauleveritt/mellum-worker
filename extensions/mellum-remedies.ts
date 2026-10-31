/**
 * mellum-remedies: switch remedy units on and off in a live Pi session.
 *
 * Every unit under remedies/<kind>/ is installed at session start behind its own switch, and all
 * start off, so the session is bare Pi until the learner turns something on:
 *
 *   /remedy                          a picker of every unit, marked on or off
 *   /remedy on guard/break-repeat-loops
 *   /remedy off guard/break-repeat-loops
 *   /remedy preset:easy              every unit in a preset
 *
 * A switch takes effect at the next tool call or request. A tool a unit adds is registered the
 * first time the unit is switched on; Pi cannot unregister a tool, so it stays offered after
 * `off` until the session restarts (its hooks do stop).
 */
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REMEDIES = join(dirname(fileURLToPath(import.meta.url)), "..", "remedies");
const KINDS = ["guard", "nudge", "context", "tool", "check", "workflow"];

interface Unit {
	name: string;
	pathology: string;
}

/** Every unit name under remedies/, in kind order. */
export function unitNames(): string[] {
	const names: string[] = [];
	for (const kind of KINDS) {
		let files: string[] = [];
		try {
			files = readdirSync(join(REMEDIES, kind)).filter((f) => f.endsWith(".ts")).sort();
		} catch {
			continue;
		}
		names.push(...files.map((f) => `${kind}/${f.replace(/\.ts$/, "")}`));
	}
	return names;
}

export function presetUnits(name: string): string[] | undefined {
	try {
		return JSON.parse(readFileSync(join(REMEDIES, "presets", `${name}.json`), "utf8"));
	} catch {
		return undefined;
	}
}

function presetNames(): string[] {
	try {
		return readdirSync(join(REMEDIES, "presets")).filter((f) => f.endsWith(".json")).map((f) => `preset:${f.replace(/\.json$/, "")}`).sort();
	} catch {
		return [];
	}
}

/** A copy of `pi` whose hooks only run while `isOn()`, and whose tools wait for the first switch-on. */
function gated(pi: any, isOn: () => boolean, pendingTools: unknown[][]): any {
	return new Proxy(pi, {
		get(target, prop, receiver) {
			if (prop === "on") {
				return (event: string, handler: (e: any, ctx?: any) => unknown) =>
					target.on(event, (e: any, ctx?: any) => (isOn() ? handler(e, ctx) : undefined));
			}
			if (prop === "registerTool") return (...args: unknown[]) => { pendingTools.push(args); };
			return Reflect.get(target, prop, receiver);
		},
	});
}

export default async function (pi: any): Promise<void> {
	const on = new Set<string>();
	const units: Unit[] = [];
	const pending = new Map<string, unknown[][]>();

	for (const name of unitNames()) {
		const mod = await import(pathToFileURL(join(REMEDIES, `${name}.ts`)).href);
		const tools: unknown[][] = [];
		pending.set(name, tools);
		mod.default(gated(pi, () => on.has(name), tools));
		units.push({ name, pathology: mod.meta?.pathology ?? "" });
	}
	const known = new Set(units.map((u) => u.name));

	const refresh = (ctx: any) => ctx?.ui?.setStatus?.("remedies", on.size ? `remedies: ${on.size} on` : undefined);

	const switchOn = (name: string) => {
		on.add(name);
		for (const args of pending.get(name)?.splice(0) ?? []) pi.registerTool?.(...args);
	};

	const apply = (args: string, ctx: any): void => {
		const [verb, target] = args.includes(" ") ? args.trim().split(/\s+/, 2) : ["on", args.trim()];
		if (target.startsWith("preset:")) {
			const list = presetUnits(target.slice("preset:".length));
			if (!list) return ctx.ui.notify(`no ${target}; known: ${presetNames().join(", ")}`, "error");
			for (const name of list) verb === "off" ? on.delete(name) : switchOn(name);
			ctx.ui.notify(`${verb === "off" ? "off" : "on"}: ${target} (${list.length} units)`, "info");
			return refresh(ctx);
		}
		if (!known.has(target)) return ctx.ui.notify(`no remedy unit ${target}; type /remedy to pick one`, "error");
		if (verb === "off") on.delete(target);
		else switchOn(target);
		ctx.ui.notify(`${on.has(target) ? "on" : "off"}: ${target}`, "info");
		refresh(ctx);
	};

	pi.registerCommand("remedy", {
		description: "Switch remedy units on or off: /remedy, /remedy on <unit>, /remedy off <unit>, /remedy preset:<name>",
		getArgumentCompletions: (prefix: string) => {
			const choices = [
				...units.flatMap((u) => [`on ${u.name}`, `off ${u.name}`]),
				...presetNames(),
			];
			const items = choices.filter((c) => c.startsWith(prefix)).map((c) => ({ value: c, label: c }));
			return items.length ? items : null;
		},
		handler: async (args: string, ctx: any) => {
			if (args.trim()) return apply(args, ctx);
			const options = units.map((u) => `${on.has(u.name) ? "●" : "○"} ${u.name}  ${u.pathology}`);
			const picked = await ctx.ui.select("Remedies: pick one to switch on or off", options);
			if (!picked) return;
			const name = units.find((u) => picked.includes(` ${u.name} `))?.name;
			if (name) apply(`${on.has(name) ? "off" : "on"} ${name}`, ctx);
		},
	});
}
