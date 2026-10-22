/**
 * mellum-quality: a code-quality finish check for the Mellum worker.
 *
 * The recorded pathology is self-inflicted and silent: the model re-emits a
 * whole function instead of editing it (a second `def` that shadows the first,
 * pyflakes F811), strands an undefined name after a rename (F821), or leaves an
 * unused import (F401). None of these error at author time; the worker declares
 * done with broken code.
 *
 * At `agent_before_settle` — the same point the empty-final nudge uses — this
 * runs ruff over the worker's own changes and, if real errors remain, hands
 * them back with one bounded nudge to fix before finishing. The check is
 * deliberately agnostic to the task: it selects `F,E9` only (pyflakes plus
 * syntax, the real-error classes), never style (`RUF100`, `I001`, docstrings,
 * line length). So it never fails a working solution on cosmetics, and it knows
 * nothing about any particular suite. It degrades to silence when ruff cannot
 * run, so missing tooling never blocks the worker.
 *
 * F811 is the motivating case: it fires on a genuine shadow but stays quiet on
 * legitimate redefinitions (`@overload`, `@property`/`.setter`, `TYPE_CHECKING`),
 * which a hand-rolled "same name twice" scan would wreck — so the check leans on
 * the tool that already gets that right.
 */

import { spawnSync } from "node:child_process";

export interface Violation {
	file: string;
	line: number;
	col: number;
	code: string;
	message: string;
}

export interface Continuation {
	entries: { type: "custom_message"; customType: string; content: string; display: boolean }[];
	continue: true;
}

/** Runs ruff in `cwd` with the given select and returns its output, or null when it could not run. */
export type RuffRunner = (cwd: string, select: string) => string | null;

export interface Config {
	max: number;
	select: string;
}

const DEFAULTS: Config = { max: 2, select: "F,E9" };

const LINE = /^(.+?):(\d+):(\d+):\s+([A-Z]+\d+)\s+(.+)$/;

/** Parse ruff's `--output-format=concise` lines (`path:line:col: CODE message`); other lines are ignored. */
export function parseRuff(output: string): Violation[] {
	const violations: Violation[] = [];
	for (const raw of output.split("\n")) {
		const match = LINE.exec(raw.trim());
		if (!match) continue;
		violations.push({
			file: match[1],
			line: Number(match[2]),
			col: Number(match[3]),
			code: match[4],
			message: match[5],
		});
	}
	return violations;
}

/** The one nudge the worker sees: the exact violations, plus why a shadow is dangerous. */
export function qualityMessage(violations: Violation[]): string {
	const list = violations.map((v) => `  ${v.file}:${v.line}:${v.col} ${v.code} ${v.message}`).join("\n");
	const shadow = violations.some((v) => v.code === "F811")
		? "\n\nF811 means you defined a name more than once; in Python the later " +
			"definition silently replaces the earlier, so the first is dead code. " +
			"Edit the single definition instead of adding another."
		: "";
	return (
		"[mellum-quality] Before you finish: ruff found real errors in your own " +
		"changes (ruff --select F,E9). Fix each one, then finish:\n" +
		list +
		shadow
	);
}

/**
 * A finish check: at each settle, lint the worker's changes; while real errors
 * remain, return a continuation that hands them back, at most `max` times.
 */
export function createQualityCheck(
	max: number,
	run: RuffRunner,
	cwd: string,
	select: string = DEFAULTS.select,
): () => Continuation | undefined {
	let used = 0;
	return () => {
		if (used >= max) return undefined;
		let output: string | null;
		try {
			output = run(cwd, select);
		} catch {
			return undefined; // ruff threw (e.g. not installed): never block on tooling.
		}
		if (output == null) return undefined; // runner could not run ruff.
		const violations = parseRuff(output);
		if (violations.length === 0) return undefined;
		used += 1;
		return {
			continue: true,
			entries: [
				{
					type: "custom_message",
					customType: "mellum-quality",
					content: qualityMessage(violations),
					display: true,
				},
			],
		};
	};
}

/** MELLUM_QUALITY (JSON) overrides the defaults, for smokes such as {"max":1,"select":"F"}. */
export function resolveConfig(env: string | undefined): Config {
	if (!env) return { ...DEFAULTS };
	try {
		const parsed = JSON.parse(env);
		if (parsed && typeof parsed === "object") return { ...DEFAULTS, ...parsed };
	} catch {
		// fall through to defaults
	}
	return { ...DEFAULTS };
}

/** The shipped runner: `uvx ruff check` over the workspace, real-error rules only. */
export const defaultRuffRunner: RuffRunner = (cwd, select) => {
	const result = spawnSync(
		"uvx",
		[
			"ruff",
			"check",
			"--select",
			select,
			"--exclude",
			"tests",
			"--exclude",
			"grader_tests",
			"--output-format=concise",
			".",
		],
		{ cwd, encoding: "utf8" },
	);
	if (result.error || result.status === null) return null; // could not run ruff
	return (result.stdout || "") + (result.stderr || "");
};

export default function (
	pi: { on: (event: string, handler: (event: unknown) => unknown) => void },
	options: { run?: RuffRunner; cwd?: string } = {},
): void {
	const cfg = resolveConfig(process.env.MELLUM_QUALITY);
	const run = options.run ?? defaultRuffRunner;
	const cwd = options.cwd ?? process.cwd();
	const check = createQualityCheck(cfg.max, run, cwd, cfg.select);
	pi.on("agent_before_settle", () => check());
}
