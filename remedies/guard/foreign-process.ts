/** Remedy unit: refuse a kill aimed at a process the worker did not start - the model server, the
 * harness, anything whose working directory is outside the workspace - and any kill whose target
 * cannot be seen first (by name, by port, through a pipe). */
import { createForeignProcessGuard } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology:
		"Finds its chosen port busy and kills whatever holds it, including the model server the run depends on, ending its own run and every run queued after it",
	does: "Blocks kill/pkill/killall/fuser -k unless every target is an explicit pid whose working directory is inside the workspace, and never the harness's own pid chain",
	lesson: "",
	evidence:
		"recorded: 2026-11-11 on-policy sampling rung 7 r2 ran `kill <llama-server pid>` to free port 8001; 15 later runs got only connection errors (docs/superpowers/research/2026-11-10-mellum-adherence-finetune.md); a safety guard, not a pass-rate remedy",
};

export function install(pi: PiLike): void {
	installGuard(pi, createForeignProcessGuard(process.cwd()));
}

export default install;
