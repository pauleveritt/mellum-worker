/** Explicit remedy: refuse foreground tail-follow in a bounded coding task. */
import { logFollowGuard } from "../../extensions/mellum-log-follow.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Waits on foreground log-follow after backgrounding a server",
	does: "Blocks foreground tail-follow and requests a finite log snapshot",
	lesson: "",
	evidence: "LC.37 G4 stalled on tail-follow; unit-tested, pending a fresh screen",
};

export function install(pi: PiLike): void {
	installGuard(pi, logFollowGuard);
}
export default install;
