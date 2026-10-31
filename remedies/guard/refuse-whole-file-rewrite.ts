/** Remedy unit: refuse `write` over an existing file; the model must `edit` it instead. */
import { existsSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { newFileOnlyWrite } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Rewrites a whole file to change a few lines (942 lines became 2)",
	does: "Blocks `write` to an existing file and asks for `edit`",
	lesson: "E5",
	evidence: "recorded once; dormant in the worker (its column never went non-zero)",
};

export function install(pi: PiLike, opts: { cwd?: string } = {}): void {
	const cwd = opts.cwd ?? process.cwd();
	installGuard(pi, newFileOnlyWrite((p) => existsSync(isAbsolute(p) ? p : resolve(cwd, p))));
}

export default (pi: PiLike) => install(pi);
