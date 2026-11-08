/** Remedy unit (check): the mediated test. The request arrives with an acceptance test the model
 * did not write (named in MELLUM_MEDIATED_TEST, one or more files joined by the path delimiter).
 * The unit shows the test once at the start of the task, and before the model may finish it runs
 * the test and sends the failures back while it is red (at most MELLUM_MEDIATED_MAX times,
 * default 5).
 *
 * External, complete, unweakenable: the files are read once, when the unit loads, and every check
 * writes that copy into a fresh directory outside the project and runs it there, with the project
 * as the working directory and on the import path. Editing or deleting the files the model was
 * shown changes nothing. The unit names no file, route or expected value; the test is the
 * request's, written from the spec by whoever hands the work over. It never blocks settle on its
 * own error. See AGENTS.md, "Driving the worker". */
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, delimiter, join } from "node:path";
import { gateConfig, runTest, type Verdict } from "../../extensions/mellum-verify.ts";
import type { PiLike, UnitMeta } from "../install.ts";
import { installTaskPrompt } from "../task-prompt.ts";

export const meta: UnitMeta = {
	pathology: "Declares done while a spec requirement it never tested is unmet",
	does: "Shows the request's own acceptance test, reruns a frozen copy before finishing and sends the failures back",
	lesson: "",
	evidence: "dry-run: red on the Phase 4 id miss in 6 of 6 Base sessions, green on the complete build; screen pending",
};

type Frozen = { name: string; source: string };

function load(spec: string): Frozen[] {
	return spec.split(delimiter).map((p) => p.trim()).filter(Boolean).map((path) => {
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

function redispatch(v: Verdict): string {
	const failing = v.failures.length ? v.failures.join(", ") : "(see output below)";
	return (
		"[mediated-test] The request's acceptance test still fails, so you are not done. " +
		`Failing: ${failing}. You cannot change this test; change the code so each one passes, then stop.\n\n` +
		v.output.slice(-1500)
	);
}

export function install(pi: PiLike): void {
	const files = load(process.env.MELLUM_MEDIATED_TEST ?? "");
	if (files.length === 0) return;
	installTaskPrompt(pi, "check/mediated-test", showing(files));
	const max = Number.parseInt(process.env.MELLUM_MEDIATED_MAX ?? "5", 10);
	let used = 0;
	pi.on("agent_before_settle", (event: any, ctx: any) => {
		if (!(used < max)) return undefined;
		const cwd = ctx && typeof ctx.cwd === "string" ? ctx.cwd : process.cwd();
		let verdict: Verdict;
		try {
			const dir = mkdtempSync(join(tmpdir(), "mediated-"));
			for (const f of files) writeFileSync(join(dir, f.name), f.source);
			verdict = runTest(dir, gateConfig().pytest, cwd);
		} catch {
			return undefined;
		}
		if (verdict.passed) return undefined;
		used += 1;
		return {
			// Pi keeps the entries the last handler returns, so keep the earlier handlers' too.
			entries: [...(event?.entries ?? []), { type: "custom_message", customType: "mediated-test", content: redispatch(verdict), display: true }],
			continue: true,
		};
	});
}

export default (pi: PiLike) => install(pi);
