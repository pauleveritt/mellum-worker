/** Remedy unit (prompt): make the model finish only after it has checked every requirement the
 * spec lists and actually run the project's own tests — not after reading files or starting a
 * server. Agnostic: it names no requirement, route, file or expected value; the model reads the
 * requirements from the spec itself. Injects one visible instruction per task. Coding effect under test
 * (easy-ladder, 2026-11-02). */
import type { PiLike, UnitMeta } from "../install.ts";
import { installTaskPrompt } from "../task-prompt.ts";

const LINE =
	"Before you finish, check that every requirement the spec lists is present in your code, and " +
	"run the project's own tests to confirm — do not finish while a requirement is unimplemented " +
	"or a test you can run is failing. Reading the files is not verification; run them.";

export const meta: UnitMeta = {
	pathology: "Declares done with a spec requirement unimplemented or unverified",
	does: "Injects the requirement-and-test verification instruction once per task",
	lesson: "",
	evidence: "new unit; unmeasured (easy-ladder, 2026-11-02)",
};

export function install(pi: PiLike): void {
 installTaskPrompt(pi, "prompt/verify-the-spec", LINE);
}

export default (pi: PiLike) => install(pi);
