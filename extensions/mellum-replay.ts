/**
 * mellum-replay — replay a captured run's prompt to the model, with a slight
 * adjustment, inside Pi (a Pi extension; agnostic, like the feed and the gate).
 *
 * Reads the last prompt the feed captured (`mellum-feed.ts` writes `prompt`
 * events), applies an adjustment you pass, and re-drives the model through Pi:
 * it overrides the system prompt for the replayed run and resends the task. Use
 * it to retry a broken run with a tweaked prompt without re-staging anything.
 *
 *   /replay <adjustment>   replay the last captured prompt; the adjustment is
 *                          appended to the system prompt (empty = replay as-is)
 *
 * Self-contained: Node `fs` + Pi hooks only; loads with `-e` or `--pi-extension`.
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";

export interface CapturedPrompt {
	system: string;
	task: string;
}

/** Apply a slight adjustment to a captured prompt — appended to the system prompt. */
export function applyAdjustment(prompt: CapturedPrompt, adjustment: string): CapturedPrompt {
	const note = (adjustment || "").trim();
	if (!note) return prompt;
	return { system: `${prompt.system}\n\nReplay adjustment: ${note}`, task: prompt.task };
}

/** The most recent captured prompt in a feed's NDJSON text (last `prompt` event). */
export function lastPrompt(feedText: string): CapturedPrompt | undefined {
	const lines = feedText.split(/\r?\n/).filter(Boolean);
	for (let i = lines.length - 1; i >= 0; i--) {
		try {
			const e = JSON.parse(lines[i]);
			if (e.kind === "prompt") return { system: e.system || "", task: e.task || "" };
		} catch {
			// skip malformed lines
		}
	}
	return undefined;
}

function feedPath(): string {
	return process.env.MELLUM_FEED || `${process.env.HOME || homedir()}/.pi/agent/mellum-feed.ndjson`;
}

export default function (pi: any) {
	let replaySystem = "";
	let active = false;

	pi.registerCommand?.("replay", {
		description: "replay the last captured worker prompt to the model, with an optional slight adjustment",
		handler: async (args: string, ctx: any) => {
			let feed = "";
			try {
				feed = readFileSync(feedPath(), "utf8");
			} catch {
				// no feed yet
			}
			const base = lastPrompt(feed);
			if (!base) {
				ctx?.ui?.notify?.("mellum-replay: no captured prompt in the feed yet", "warning");
				return;
			}
			const adjusted = applyAdjustment(base, args || "");
			replaySystem = adjusted.system;
			active = true;
			pi.sendUserMessage?.(adjusted.task);
		},
	});

	// For the replayed run, swap the system prompt in and keep the resent task.
	pi.on("before_provider_request", (event: any) => {
		if (!active || !replaySystem) return undefined;
		const payload = event?.payload;
		if (payload && Array.isArray(payload.messages)) {
			payload.messages = [
				{ role: "system", content: replaySystem },
				...payload.messages.filter((m: any) => m?.role !== "system"),
			];
			return payload;
		}
		return undefined;
	});
	pi.on("agent_settled", () => {
		active = false;
		return undefined;
	});
}
