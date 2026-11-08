/** Remedy unit (check): never settle on code that does not compile or import.
 *
 * On `tool_result` for a successful `write` or `edit` of a `.py` file inside the workspace, the
 * file is compiled; a `SyntaxError` turns the result into a failed write carrying the compiler's
 * message, so the model sees it in the very next request. At settle, every module the session
 * wrote is imported, each in its own process with the workspace on the import path, under a
 * timeout that stops the whole process group; failures send the model back, at most 3 times.
 *
 * Agnostic: it keys on the `.py` extension and the model's own writes, and names no suite file.
 * The workspace's interpreter runs through `uv run --offline`. A compile or import step that
 * cannot start (no uv) is our tooling and never blocks. */
import { existsSync } from "node:fs";
import { isAbsolute, join, normalize, relative, resolve, sep } from "node:path";
import { runBounded } from "../../extensions/bounded.ts";
import type { PiLike, UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Settles on code that does not compile or import",
	does: "Fails a .py write that does not compile; at settle, imports each module written and sends failures back (at most 3)",
	lesson: "",
	evidence: "unit-tested; R.1 measures it on Base",
};

export interface Options {
	uv?: string;
	compileTimeoutMs?: number;
	importTimeoutMs?: number;
	max?: number;
}

/** `pkg/mod.py` → `pkg.mod`, `pkg/__init__.py` → `pkg`; null for anything not a .py inside the workspace. */
export function moduleName(rel: string): string | null {
	if (isAbsolute(rel) || !rel.endsWith(".py")) return null;
	const clean = normalize(rel);
	if (clean.startsWith("..")) return null;
	const parts = clean.slice(0, -3).split(sep);
	if (parts.at(-1) === "__init__") parts.pop();
	if (parts.length === 0 || parts.some((p) => !/^[A-Za-z_][A-Za-z0-9_]*$/.test(p))) return null;
	return parts.join(".");
}

/** The workspace-relative path of a tool's target, or null when it is outside the workspace. */
function inWorkspace(path: unknown, cwd: string): string | null {
	if (typeof path !== "string" || path === "") return null;
	const rel = relative(cwd, resolve(cwd, path));
	return rel === "" || rel.startsWith("..") || isAbsolute(rel) ? null : rel;
}

function pythonEnv(cwd: string): NodeJS.ProcessEnv {
	const env: NodeJS.ProcessEnv = { ...process.env, PYTHONPATH: cwd, PYTHONDONTWRITEBYTECODE: "1" };
	delete env.VIRTUAL_ENV;
	return env;
}

/** The compiler's message for `rel`, or null when it compiles or the compiler could not run. */
export function compileCheck(rel: string, cwd: string, opts: Options = {}): string | null {
	// Compile in memory: the check leaves no .pyc behind in the model's workspace.
	const code = "import sys; p = sys.argv[1]; compile(open(p, encoding='utf-8').read(), p, 'exec')";
	const r = runBounded(opts.uv ?? "uv", ["run", "--offline", "python", "-c", code, rel],
		{ cwd, env: pythonEnv(cwd), timeoutMs: opts.compileTimeoutMs ?? 30_000 });
	if (!r.started || r.timedOut || r.code === 0 || r.code === null) return null;
	if (!/Error/.test(r.out)) return null; // uv itself failed (not a compile error): ours, not the model's
	return r.out.trim().slice(-1500);
}

/** Import each module in its own process; the modules that failed, with their error. */
export function importCheck(modules: string[], cwd: string, opts: Options = {}): { module: string; error: string }[] {
	const timeoutMs = opts.importTimeoutMs ?? 60_000;
	const failed: { module: string; error: string }[] = [];
	for (const module of modules) {
		const r = runBounded(opts.uv ?? "uv",
			["run", "--offline", "python", "-c", "import importlib, sys; importlib.import_module(sys.argv[1])", module],
			{ cwd, env: pythonEnv(cwd), timeoutMs });
		if (!r.started) return []; // no uv: our tooling, never the model's
		if (r.timedOut) {
			failed.push({ module, error: `importing it timed out after ${Math.round(timeoutMs / 1000)} s and was stopped (does importing it start a server or wait on something?)` });
		} else if (r.code !== 0) {
			failed.push({ module, error: r.out.trim().slice(-1200) });
		}
	}
	return failed;
}

function importMessage(failed: { module: string; error: string }[]): string {
	return (
		"[compile-import] These modules you wrote do not import, so you are not done. " +
		"Fix each so that `import <module>` succeeds, then stop.\n\n" +
		failed.map((f) => `# ${f.module}\n${f.error}`).join("\n\n")
	);
}

export function install(pi: PiLike, opts: Options = {}): void {
	const written = new Set<string>();
	const max = opts.max ?? 3;
	let used = 0;
	const cwdOf = (ctx: any) => (ctx && typeof ctx.cwd === "string" ? ctx.cwd : process.cwd());
	pi.on("tool_result", (event: any, ctx: any) => {
		if ((event?.toolName !== "write" && event?.toolName !== "edit") || event.isError) return undefined;
		const cwd = cwdOf(ctx);
		const rel = inWorkspace(event.input?.path, cwd);
		if (rel === null || moduleName(rel) === null) return undefined;
		written.add(rel);
		const error = compileCheck(rel, cwd, opts);
		if (error === null) return undefined;
		return {
			isError: true,
			content: [...(event.content ?? []),
				{ type: "text", text: `\n[compile-import] ${rel} does not compile; fix it before going on:\n${error}` }],
		};
	});
	pi.on("agent_before_settle", (event: any, ctx: any) => {
		if (!(used < max) || written.size === 0) return undefined;
		const cwd = cwdOf(ctx);
		const modules = [...written].filter((rel) => existsSync(join(cwd, rel))).map((rel) => moduleName(rel) as string);
		let failed: { module: string; error: string }[];
		try {
			failed = importCheck(modules, cwd, opts);
		} catch {
			return undefined; // never block settle on our own error
		}
		if (failed.length === 0) return undefined;
		used += 1;
		return {
			// Pi keeps the entries the last handler returns, so keep the earlier handlers' too.
			entries: [...(event?.entries ?? []), { type: "custom_message", customType: "compile-import", content: importMessage(failed), display: true }],
			continue: true,
		};
	});
}

export default (pi: PiLike) => install(pi);
