/** Remedy unit (opt-in, unmeasured as a remedy): Adds a lookup tool over the installed packages' signatures and docs. Re-exports extensions/mellum-knowledge.ts unchanged. */
import ext from "../../extensions/mellum-knowledge.ts";
import { keepingTools, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Guesses an API it never saw (a post-cutoff library, a redirect status)",
	does: "Adds a lookup tool over the installed packages' signatures and docs",
	lesson: "M5",
	evidence: "unit-tested; not measured on the suites",
};

/** Loads the extension unchanged; any tool it registers is kept by `context/narrow-tools`. */
export default (pi: any) => ext(keepingTools(pi));
