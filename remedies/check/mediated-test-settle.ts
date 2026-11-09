/** Remedy unit (check): the mediated test's second half alone. The model never sees the test; before
 * it may finish, a frozen copy runs and the failures go back. See remedies/mediated-test.ts. */
import type { PiLike, UnitMeta } from "../install.ts";
import { loadMediated, settleMediated } from "../mediated-test.ts";

export const meta: UnitMeta = {
	pathology: "Declares done while a spec requirement it never tested is unmet",
	does: "Reruns the request's own acceptance test before finishing and sends the failures back; never shows it first",
	lesson: "",
	evidence: "split from check/mediated-test to learn which half pays its cost; screen in F.6",
};

export function install(pi: PiLike): void {
	const files = loadMediated();
	if (files.length > 0) settleMediated(pi, files);
}

export default (pi: PiLike) => install(pi);
