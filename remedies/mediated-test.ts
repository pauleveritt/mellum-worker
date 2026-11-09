/** The two halves of the mediated test, each installed by its own unit (remedies/check/mediated-test*.ts).
 *
 * The request arrives with an acceptance test the model did not write (named in MELLUM_MEDIATED_TEST,
 * one or more files joined by the path delimiter). Showing it and rerunning it at settle are separate
 * behaviours, so each can be measured alone.
 *
 * External, complete, unweakenable: the files are read once, when the unit loads, and every check
 * writes that copy into a fresh directory outside the project and runs it there (remedies/gate-run.ts),
 * with the project as the working directory and on the import path, and its dependencies as they were
 * at load. Editing or deleting the files the model was shown changes nothing. The copy is deleted when
 * each run ends and its location is taken out of what the model is told. Before each run, what this
 * session left running is stopped.
 *
 * Each check ends in a verdict: `green` (every test passed: settle), `red` (sent back with the
 * failures, at most MELLUM_MEDIATED_MAX times), `exhausted` (still red once the send-backs are used:
 * settle, unverified), `infrastructure` (our tooling gave no answer, even on one silent retry:
 * settle, unverified, and the model is never asked to repair it). Each verdict is appended to the file
 * named in MELLUM_GATE_LOG, so the harness can refuse to advance on an unverified exit. Nothing here
 * names a file, route or expected value; the test is the request's, written from the spec by whoever
 * hands the work over. See AGENTS.md, "Driving the worker". */
import { appendFileSync, mkdtempSync, readFileSync, rmdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, delimiter, dirname, join } from "node:path";
import { type Frozen, type GateFailure, type GateRun, freezeProject, runGate } from "./gate-run.ts";
import type { PiLike } from "./install.ts";
import { markSessionProcesses, stopSessionProcesses } from "./session-processes.ts";
import { installTaskPrompt } from "./task-prompt.ts";

export type { Frozen } from "./gate-run.ts";


/** Tests a harness handed over, kept for every unit in this process: once read they are deleted. */
const HANDED = Symbol.for("mellum.mediated");

/** The request's acceptance tests. When a harness handed them over (MELLUM_MEDIATED_HANDED=1), the
 * copies, their directory and both variables are removed as soon as they are read, before the model's
 * first turn, so no command can find them; the other half of the test, loaded as its own unit, gets the
 * same files from this process. A test a user named themselves is never deleted. */
export function loadMediated(): Frozen[] {
	const named = (process.env.MELLUM_MEDIATED_TEST ?? "").split(delimiter).map((p) => p.trim()).filter(Boolean);
	if (named.length === 0) return ((globalThis as any)[HANDED] as Frozen[] | undefined) ?? [];
	const files = named.map((path) => {
		try {
			return { name: basename(path), source: readFileSync(path, "utf8") };
		} catch {
			throw new Error(`mediated test: cannot read the acceptance test ${path}`);
		}
	});
	if (process.env.MELLUM_MEDIATED_HANDED === "1") {
		for (const path of named) rmSync(path, { force: true });
		for (const dir of new Set(named.map((path) => dirname(path)))) {
			try {
				rmdirSync(dir);
			} catch {
				// Not empty or already gone: the harness removes its directory at the end of the run.
			}
		}
		delete process.env.MELLUM_MEDIATED_TEST;
		delete process.env.MELLUM_MEDIATED_HANDED;
		(globalThis as any)[HANDED] = files;
	}
	return files;
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

const PER_FAILURE = 400;
const DETAILED = 6;
const DETAIL_TOTAL = 1500;

/** What the model is told after a red check: every failing test by name, then each one's assertion,
 * capped per failure and in total. Server output the test captured is never included. */
export function feedback(run: GateRun, dir: string, stopped: number): string {
	const names = run.failures.map((f) => f.test);
	if (run.running && !names.includes(run.running)) names.push(run.running);
	const failing = names.length ? names.join(", ") : "(see below)";
	const background = stopped > 0 ? "Processes you left running in the background were stopped before this run. " : "";
	const hang = run.timedOutSeconds === undefined ? "" :
		`The acceptance test was stopped after ${run.timedOutSeconds} s${run.running ? `, while ${run.running} was running` : ""}.\n`;
	// A collection error's message is a traceback whose last line is the error itself: keep its end.
	const capped = (f: GateFailure) => (f.test === "collection" ? f.message.slice(-PER_FAILURE) : f.message.slice(0, PER_FAILURE));
	const details = run.failures.slice(0, DETAILED).map((f) => `- ${f.test}: ${capped(f)}`).join("\n");
	return (
		"[mediated-test] The request's acceptance test still fails, so you are not done. " +
		`Failing: ${failing}. This test is not in the project and you cannot read, run or change it; ` +
		`change the code so each one passes, then stop. ${background}\n\n` +
		withoutLocation(hang + details, dir).slice(0, DETAIL_TOTAL)
	);
}

type Checked = { run: GateRun; dir: string };

function check(files: Frozen[], project: ReturnType<typeof freezeProject>, cwd: string): Checked {
	let dir = "";
	try {
		dir = mkdtempSync(join(tmpdir(), "mediated-"));
		return { run: runGate(dir, files, project, cwd), dir };
	} catch (error) {
		return { run: { status: "infrastructure", failures: [], missing: [], detail: `the check could not run: ${String(error)}`, execution: "workspace" }, dir };
	} finally {
		// Settle blocks the agent, so no model command can run while the copy exists.
		if (dir) rmSync(dir, { recursive: true, force: true });
	}
}

/** Read a variable the harness set for this unit alone, and take it out of what commands inherit. */
function take(name: string): string | undefined {
	const value = process.env[name];
	delete process.env[name];
	return value?.trim() || undefined;
}

function record(path: string | undefined, entry: Record<string, unknown>): void {
	if (!path) return;
	try {
		appendFileSync(path, JSON.stringify({ at: new Date().toISOString(), ...entry }) + "\n");
	} catch {
		// The log is the harness's evidence; failing to write it must not block settle.
	}
}

/** Show the test once, at the start of the task. */
export function showMediated(pi: PiLike, remedy: string, files: Frozen[]): void {
	installTaskPrompt(pi, remedy, showing(files));
}

/** Before the model may finish, run the frozen copy, record its verdict, and send the failures back
 * while it is red (at most MELLUM_MEDIATED_MAX times, default 5). Never blocks settle on its own error. */
export function settleMediated(pi: PiLike, files: Frozen[]): void {
	const max = Number.parseInt(process.env.MELLUM_MEDIATED_MAX ?? "5", 10);
	const log = take("MELLUM_GATE_LOG");
	const project = freezeProject(process.cwd());
	let used = 0;
	markSessionProcesses();
	pi.on("agent_before_settle", (event: any, ctx: any) => {
		const cwd = ctx && typeof ctx.cwd === "string" ? ctx.cwd : process.cwd();
		const stopped = stopSessionProcesses();
		let checked = check(files, project, cwd);
		// Bounded recovery: one silent retry, never a repair the model is asked to make.
		if (checked.run.status === "infrastructure") checked = check(files, project, cwd);
		const { run, dir } = checked;
		const status = run.status === "red" && !(used < max) ? "exhausted" : run.status;
		record(log, { status, sent_back: status === "red" ? used + 1 : used, failures: run.failures.map((f) => f.test), missing: run.missing, detail: run.detail, execution: run.execution });
		if (status !== "red") return undefined;
		used += 1;
		return {
			// Pi keeps the entries the last handler returns, so keep the earlier handlers' too.
			entries: [...(event?.entries ?? []), { type: "custom_message", customType: "mediated-test", content: feedback(run, dir, stopped), display: true }],
			continue: true,
		};
	});
}
