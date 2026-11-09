/** Remedy unit (check): the mediated test, both halves. Shows the request's own acceptance test once,
 * and reruns a frozen copy at settle, sending failures back. check/mediated-test-show and
 * check/mediated-test-settle are each half alone. See remedies/mediated-test.ts. */
import type { PiLike, UnitMeta } from "../install.ts";
import { loadMediated, settleMediated, showMediated } from "../mediated-test.ts";

export const meta: UnitMeta = {
	pathology: "Declares done while a spec requirement it never tested is unmet",
	does: "Shows the request's own acceptance test, reruns a frozen copy before finishing and sends the failures back",
	lesson: "",
	evidence: "dry-run: red on the Phase 4 id miss in 6 of 6 Base sessions, green on the complete build; screen pending",
};

export function install(pi: PiLike): void {
	const files = loadMediated();
	if (files.length === 0) return;
	showMediated(pi, "check/mediated-test", files);
	settleMediated(pi, files);
}

export default (pi: PiLike) => install(pi);
