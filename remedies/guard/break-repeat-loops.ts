/** Remedy unit: block the same tool call repeated with nothing changed in between. */
import { createLoopBreaker } from "../../extensions/mellum-guards.ts";
import { installGuard, type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Repeats the same call over and over (245 identical `ls -R` calls in one run)",
	does: "Blocks a call made 5 times in a row with nothing changed in between",
	lesson: "E3",
	evidence: "ladder: part of the guard set behind phase 2b's 15/15",
};

export function install(pi: PiLike, opts: { window?: number; threshold?: number } = {}): void {
	installGuard(pi, createLoopBreaker(opts.window, opts.threshold));
}

export default (pi: PiLike) => install(pi);
