/** Remedy unit: refuse a server started in the foreground, which hangs the session. */
import { serverGuard } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Starts `python app.py` in the foreground and the session hangs until its deadline",
	does: "Blocks a foreground server start and shows the background form",
	lesson: "",
	evidence: "screen: the hang recurs in the vLLM baseline's web-app rungs; unmeasured as a remedy",
};

export function install(pi: PiLike): void {
	installGuard(pi, serverGuard);
}

export default install;
