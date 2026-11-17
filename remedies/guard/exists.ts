/** Remedy unit: don't act on a path that isn't there. Blocks a read or edit of a missing
 * file, and a command that will only open a missing path (e.g. running tests in a directory
 * that doesn't exist), so a worker can't burn turns retrying things that aren't there. */
import { createExistsGuard } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Reruns commands against files or directories that do not exist",
	does: "Blocks a read/edit of a missing file, or a command that only opens a missing path",
	lesson: "E7",
	evidence: "screen: recorded a 100+ call thrash rerunning tests against a missing dir; unmeasured on the ladder",
};

export function install(pi: PiLike): void {
	installGuard(pi, createExistsGuard());
}

export default (pi: PiLike) => install(pi);
