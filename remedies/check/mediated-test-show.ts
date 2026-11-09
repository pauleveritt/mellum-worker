/** Remedy unit (check): the mediated test's first half alone. Shows the request's own acceptance test
 * once at the start of the task and never reruns it. See remedies/mediated-test.ts. */
import type { PiLike, UnitMeta } from "../install.ts";
import { loadMediated, showMediated } from "../mediated-test.ts";

export const meta: UnitMeta = {
	pathology: "Declares done while a spec requirement it never tested is unmet",
	does: "Shows the request's own acceptance test at the start of the task; never reruns it",
	lesson: "",
	evidence: "split from check/mediated-test to learn which half pays its cost; screen in F.6",
};

export function install(pi: PiLike): void {
	const files = loadMediated();
	if (files.length > 0) showMediated(pi, "check/mediated-test-show", files);
}

export default (pi: PiLike) => install(pi);
