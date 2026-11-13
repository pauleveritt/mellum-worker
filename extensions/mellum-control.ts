/**
 * mellum-control — play/pause a worker run between turns, in Pi (a Pi
 * extension; agnostic, like the feed, the gate and replay).
 *
 * Reads a control file (`$MELLUM_CONTROL`, default
 * `~/.pi/agent/mellum-control.json`, shape `{"state":"play"|"pause"}`). At each
 * turn boundary (`before_provider_request`) it holds while the state is
 * `pause` and resumes the moment it flips to `play`. The dashboard writes the
 * file; any Pi run that loads this extension obeys it.
 *
 * Self-contained: Node `fs` + Pi hooks only.
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";

/** The control state from the file's text; anything unparseable or absent is `play`. */
export function parseState(text: string): "play" | "pause" {
	try {
		return JSON.parse(text)?.state === "pause" ? "pause" : "play";
	} catch {
		return "play";
	}
}

function controlPath(): string {
	return process.env.MELLUM_CONTROL || `${process.env.HOME || homedir()}/.pi/agent/mellum-control.json`;
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export default function (pi: any) {
	const readState = (): "play" | "pause" => {
		try {
			return parseState(readFileSync(controlPath(), "utf8"));
		} catch {
			return "play";
		}
	};
	// Hold the loop between turns while paused; resume when the control flips to play.
	pi.on("before_provider_request", async (_event: any, ctx: any) => {
		let notified = false;
		while (readState() === "pause") {
			if (!notified) {
				ctx?.ui?.notify?.("mellum-control: paused (play to resume)", "info");
				notified = true;
			}
			await sleep(400);
		}
		return undefined;
	});
}
