/** Remedy unit (prompt): tell the model to take the file layout from the project's own spec,
 * instead of inventing one. Agnostic — it names no path, file or route of any suite; the model
 * reads the layout from the spec itself. One explicit instruction per task. */
import { installTaskPrompt } from "../task-prompt.ts";
import type { PiLike, UnitMeta } from "../install.ts";

const LINE =
	"Read the project's own spec or notes for where each file and route belongs, and create " +
	"files at exactly those paths — do not invent your own layout.";

export const meta: UnitMeta = {
	pathology: "Invents its own file layout instead of the one the spec names",
	does: "Injects the spec-layout instruction once per task",
	lesson: "",
	evidence: "task-scoped delivery verified locally; coding effect unmeasured",
};

export function install(pi: PiLike): void {
 installTaskPrompt(pi, "prompt/name-the-layout", LINE);
}

export default (pi: PiLike) => install(pi);
