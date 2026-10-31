/** Remedy unit: keep tree-walking searches inside the workspace. Writes by absolute path are
 * not covered yet (an escaped write was recorded on 2026-10-29; extending it is a guard change). */
import { confineSearch } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Searches the whole machine (`grep -rl x /Users /var`) and hangs the run",
	does: "Blocks a recursive search that names a path outside the workspace",
	lesson: "E4",
	evidence: "screen: recorded hangs; searches only, writes are not covered",
};

export function install(pi: PiLike, opts: { cwd?: string } = {}): void {
	installGuard(pi, confineSearch(opts.cwd ?? process.cwd()));
}

export default (pi: PiLike) => install(pi);
