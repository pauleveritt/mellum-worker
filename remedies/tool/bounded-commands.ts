/** Remedy unit: give every bash call Pi's own timeout when the model set none.
 *
 * Pi's bash tool takes an optional `timeout` (seconds, "no default timeout"). When it fires, Pi
 * kills the call's whole process group and returns the output so far as an error, so a command
 * that never exits (a server started in the foreground) hands control back instead of hanging
 * the session. A shell `timeout N …` wrapper does not do this: it kills the parent and leaves the
 * reloader's children holding the pipe. No command is classified; an explicit timeout is kept.
 * See docs/superpowers/research/2026-11-05-pi-mechanisms-audit.md on `lc40-thin-worker`. */
import type { PiLike, UnitMeta } from "../install.ts";

export const DEFAULT_TIMEOUT_SECONDS = 30;
/** A chosen timeout is kept up to this, below the harness's 180 s stall cutoff: a model that set
 * 300 s on a foreground server still hung the session (overnight 2026-11-06, arm C). */
export const MAX_TIMEOUT_SECONDS = 120;

export const meta: UnitMeta = {
	pathology: "Starts a command that never exits, such as a foreground server, and hangs to the cutoff",
	does: `Sets Pi's bash timeout (${DEFAULT_TIMEOUT_SECONDS} s, or MELLUM_BOUND_SECONDS) when the model gave none; caps a chosen one at ${MAX_TIMEOUT_SECONDS} s`,
	lesson: "",
	evidence: "LC.41 overnight (n = 12): foreground stalls 10/12 to 1/12 on Easy; the 120 s cap, added for that one, is unit-tested only",
};

/** The bound for this run: `MELLUM_BOUND_SECONDS` when it is a positive number, else the default.
 * Every bounded call carries the value in its `tool_call` input, so a trace shows which ran. */
function boundSeconds(): number {
	const value = Number(process.env.MELLUM_BOUND_SECONDS);
	return Number.isFinite(value) && value > 0 ? value : DEFAULT_TIMEOUT_SECONDS;
}

export function install(pi: PiLike): void {
	const seconds = boundSeconds();
	pi.on("tool_call", (event) => {
		if (event?.toolName !== "bash" || !event.input || typeof event.input !== "object") return undefined;
		const chosen = event.input.timeout;
		if (chosen === undefined || chosen === null) {
			event.input.timeout = seconds;   // Pi: "mutate event.input in place"
		} else if (typeof chosen === "number" && chosen > MAX_TIMEOUT_SECONDS) {
			event.input.timeout = MAX_TIMEOUT_SECONDS;
		}
		return undefined;
	});
}

export default install;
