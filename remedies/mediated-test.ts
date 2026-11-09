/** The two halves of the mediated test, each installed by its own unit (remedies/check/mediated-test*.ts).
 *
 * The request arrives with an acceptance test the model did not write (named in MELLUM_MEDIATED_TEST,
 * one or more files joined by the path delimiter). Showing it and rerunning it at settle are separate
 * behaviours, so each can be measured alone.
 *
 * External, complete, unweakenable: the files are read once, when the unit loads, and every check
 * writes that copy into a fresh directory outside the project and runs it there, with the project as
 * the working directory and on the import path. Editing or deleting the files the model was shown
 * changes nothing. The copy is deleted when each run ends and its location is taken out of what the
 * model is told. Before each run, what this session left running is stopped. Nothing here names a file, route or expected value; the test is the request's,
 * written from the spec by whoever hands the work over. See AGENTS.md, "Driving the worker". */
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, delimiter, join } from "node:path";
import { gateConfig, runTest, type Verdict } from "../extensions/mellum-verify.ts";
import type { PiLike } from "./install.ts";
import { markSessionProcesses, stopSessionProcesses } from "./session-processes.ts";
import { installTaskPrompt } from "./task-prompt.ts";

export type Frozen = { name: string; source: string };

export function loadMediated(): Frozen[] {
	return (process.env.MELLUM_MEDIATED_TEST ?? "").split(delimiter).map((p) => p.trim()).filter(Boolean).map((path) => {
		try {
			return { name: basename(path), source: readFileSync(path, "utf8") };
		} catch {
			throw new Error(`mediated test: cannot read the acceptance test ${path}`);
		}
	});
}

function showing(files: Frozen[]): string {
	return (
		"This request comes with an acceptance test that you did not write. Your work is done when it " +
		"passes. It runs from outside the project, with the project on the import path, and you cannot " +
		"change it: change the code, not the test.\n\n" +
		files.map((f) => `# ${f.name}\n${f.source}`).join("\n\n")
	);
}

/** The run's output with every form of the copy's location replaced: absolute, or relative to the project. */
function withoutLocation(output: string, dir: string): string {
	const name = basename(dir).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	return output.replace(new RegExp(`[^\\s:'"]*${name}`, "g"), "<hidden>");
}

function redispatch(v: Verdict, dir: string, stopped: number): string {
	const failing = v.failures.length ? v.failures.join(", ") : "(see output below)";
	const background = stopped > 0 ? "Processes you left running in the background were stopped before this run. " : "";
	return (
		"[mediated-test] The request's acceptance test still fails, so you are not done. " +
		`Failing: ${failing}. This test is not in the project and you cannot read, run or change it; ` +
		`change the code so each one passes, then stop. ${background}\n\n` +
		withoutLocation(v.output, dir).slice(-1500)
	);
}

/** Show the test once, at the start of the task. */
export function showMediated(pi: PiLike, remedy: string, files: Frozen[]): void {
	installTaskPrompt(pi, remedy, showing(files));
}

/** Before the model may finish, run the frozen copy and send the failures back while it is red
 * (at most MELLUM_MEDIATED_MAX times, default 5). Never blocks settle on its own error. */
export function settleMediated(pi: PiLike, files: Frozen[]): void {
	const max = Number.parseInt(process.env.MELLUM_MEDIATED_MAX ?? "5", 10);
	let used = 0;
	markSessionProcesses();
	pi.on("agent_before_settle", (event: any, ctx: any) => {
		if (!(used < max)) return undefined;
		const cwd = ctx && typeof ctx.cwd === "string" ? ctx.cwd : process.cwd();
		const stopped = stopSessionProcesses();
		let verdict: Verdict;
		let dir = "";
		try {
			dir = mkdtempSync(join(tmpdir(), "mediated-"));
			for (const f of files) writeFileSync(join(dir, f.name), f.source);
			verdict = runTest(dir, gateConfig().pytest, cwd);
		} catch {
			return undefined;
		} finally {
			// Settle blocks the agent, so no model command can run while the copy exists.
			if (dir) rmSync(dir, { recursive: true, force: true });
		}
		if (verdict.passed) return undefined;
		used += 1;
		return {
			// Pi keeps the entries the last handler returns, so keep the earlier handlers' too.
			entries: [...(event?.entries ?? []), { type: "custom_message", customType: "mediated-test", content: redispatch(verdict, dir, stopped), display: true }],
			continue: true,
		};
	});
}
