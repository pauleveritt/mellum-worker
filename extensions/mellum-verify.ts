/**
 * mellum-verify — a verify-until-green gate (a Pi extension).
 *
 * (Formerly mellum-verify. The name borrowed "next-concept modelling" from an
 * unrelated generation-architecture paper; this gate just re-runs tests, so it
 * is named for what it does. "Concepts" below means the failing test functions.)
 *
 * The worker's own "done" is not trusted. When it tries to settle, this re-runs
 * the named acceptance test and, while it is red, sends the worker back with the
 * **unmet concepts** — the specific failing test functions — up to VERIFY_MAX
 * times. It brings the ladder's direct-only verify/re-dispatch into any Pi
 * session (Mellum Mode included) at the concept grain, reusing the
 * `agent_before_settle -> continue` pattern proven by the empty-final nudge in
 * `mellum-guards.ts`.
 *
 * Self-contained: Node + Pi hooks only (no Pi-internal imports), so it loads
 * with `-e extensions/mellum-verify.ts` directly — no patch into a Pi checkout.
 *
 * Config (env):
 *   VERIFY_TEST    a named acceptance test to re-run (e.g. tests/test_phase4.py),
 *               relative to the worker's cwd — the mediation grain.
 *   VERIFY_ALL     set (1/true/yes) to verify the WHOLE visible suite instead of a
 *               named test — the agnostic developer-loop gate (run everything,
 *               refuse to settle until green). Inert unless VERIFY_TEST or VERIFY_ALL.
 *   VERIFY_MAX     how many times to send the worker back (default 5).
 *   VERIFY_PYTEST  the pytest command (default: uv run --offline python -m pytest).
 *
 * Green needs evidence, not exit 0: every test function in a named test's source must
 * show a pass, because a workspace conftest, pytest config or PYTEST_ADDOPTS can skip or
 * deselect tests and still exit 0. A hung test is stopped with its process group at
 * VERIFY_TIMEOUT_MS and reads red. The gate keeps earlier settle handlers' entries, and
 * its message never names where the held-out test lives. (Proposals 17 and 18 in Paul's
 * 2026-11-09 handover; `bounded.ts` is his.)
 */
import { existsSync, readFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";
import { runBounded } from "./bounded.ts";

export interface Verdict {
	passed: boolean;
	/** The failing test functions — the concepts still unmet. */
	failures: string[];
	output: string;
}

/** Every `test*` function defined in a test file's source (methods count by their own name). */
export function expectedTests(source: string): string[] {
	return [...new Set([...source.matchAll(/^[ \t]*(?:async[ \t]+)?def[ \t]+(test\w*)[ \t]*\(/gm)].map((m) => m[1]))];
}

/** Parse `pytest -q -rA` output: passed? and the unmet concepts. With `expected` (the named test's
 * functions), green also needs a PASSED line for each one: exit 0 alone is not evidence. */
export function parsePytest(code: number, output: string, expected: string[] = []): Verdict {
	const failed = [...output.matchAll(/^(?:FAILED|ERROR)\s+\S+::(\S+?)(?:\[|\s|$)/gm)].map((m) => m[1]);
	const passedNames = new Set([...output.matchAll(/^PASSED\s+\S+::(\S+?)(?:\[|\s|$)/gm)].map((m) => m[1]));
	const missing = expected.filter((n) => !passedNames.has(n));
	return { passed: code === 0 && missing.length === 0, failures: [...new Set([...failed, ...missing])], output };
}

/** Strip where a held-out test lives from text the worker will read: its path, folder and file name. */
export function redactTestPath(text: string, test: string, cwd: string): string {
	const path = (test || "").trim();
	if (!path) return text;
	const abs = resolve(cwd, path);
	let out = text;
	for (const s of [abs, path, dirname(abs), basename(abs)]) {
		if (s && s !== "." && s !== "/" && s !== cwd) out = out.split(s).join("<acceptance test>");
	}
	// The module name shows up in object reprs (`<test_x.Tree object>`). Only where it stands alone,
	// so a test function sharing its prefix (`test_x_distinct`) keeps its name.
	const stem = basename(abs).replace(/\.py$/, "");
	if (stem) out = out.replace(new RegExp(`(?<![\\w.])${stem.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?!\\w)`, "g"), "<acceptance test>");
	return out;
}

/** Per-test reason caps: enough for an assertion and its diff, never one test crowding out the rest. */
const REASON_LINES = 12;
const REASON_CHARS = 600;

/** Each failing test's reason from `--tb=short` output: the `E` lines of its section (or the
 * section's last lines when it has none), capped. Empty when no section matches, so the caller
 * falls back to the output tail (a collection error, a timeout). */
export function failureReasons(output: string, failures: string[]): string {
	const lines = output.split("\n");
	const header = /^_{3,} (?:\S+::)?(\S+?)(?:\[.*\])? _{3,}$/;
	const sections = new Map<string, string[]>();
	let current: string[] | undefined;
	for (const line of lines) {
		const h = line.match(header);
		if (h) {
			current = [];
			if (!sections.has(h[1])) sections.set(h[1], current);
			continue;
		}
		if (/^={3,}/.test(line)) current = undefined;
		else current?.push(line);
	}
	const parts: string[] = [];
	for (const name of failures) {
		const body = sections.get(name);
		if (!body) continue;
		const e = body.filter((l) => l.startsWith("E "));
		const picked = (e.length ? e : body.filter((l) => l.trim()).slice(-6)).slice(0, REASON_LINES);
		let text = picked.join("\n");
		if (text.length > REASON_CHARS) text = `${text.slice(0, REASON_CHARS)} …`;
		parts.push(`- ${name}:\n${text}`);
	}
	return parts.join("\n");
}

/** The message handed back to the worker naming the concepts it has not met. */
export function gateMessage(v: Verdict): string {
	const concepts = v.failures.length ? v.failures.join(", ") : "(see output below)";
	const reasons = failureReasons(v.output, v.failures);
	const timedOut = v.output.match(/\[verify\] the test command timed out[^\n]*/)?.[0];
	const tail = reasons ? `Why each one fails:\n${reasons}${timedOut ? `\n${timedOut}` : ""}` : v.output.slice(-1200);
	return (
		"[mellum-verify] The tests still fail, so you are not done. " +
		`Unmet concepts (failing tests): ${concepts}. ` +
		"This acceptance test is held out — it is NOT a file in your workspace, so do not search for " +
		"it or its file (no `find`, no listing other directories). Each name above is a behaviour to " +
		"satisfy: read what the name describes, change the code so that behaviour holds, and check with " +
		"your own tests in this directory. Fix one concept at a time, then stop.\n\n" +
		tail
	);
}

/** The pytest command: a named test runs just that file; an empty test runs the whole visible suite. */
export function verifyCommand(test: string, pytest: string): string {
	const path = (test || "").trim();
	return `${pytest}${path ? ` ${path}` : ""} -q -rA -p no:warnings --tb=short`;
}

/** The verify subprocess environment: the worker cwd on PYTHONPATH, so a held-out
 * acceptance test (which lives beside the workspace) can still `from app import app`,
 * and VIRTUAL_ENV stripped so uv does not warn. Mirrors the harness grader's grade_env.
 * Without the PYTHONPATH the contract errors at collection (ModuleNotFoundError: app),
 * the gate cannot read unmet concepts, and it silently never redispatches. */
export function verifyEnv(cwd: string): NodeJS.ProcessEnv {
	const env: NodeJS.ProcessEnv = { ...process.env, PYTHONPATH: cwd };
	delete env.VIRTUAL_ENV;
	delete env.PYTEST_ADDOPTS; // could deselect the acceptance test from outside the run
	return env;
}

/** The verify timeout: below the harness's 180 s stall cutoff, so a hung test cannot stall settle. */
export const VERIFY_TIMEOUT_MS = 150_000;

/** Run the verification (a named test, or the whole suite when `test` is empty) in `cwd`. A hung
 * command is stopped with its process group and reads red. Throws only when the command could not
 * start (exit 127), which is our tooling, not the worker's code. */
export function runTest(test: string, pytest: string, cwd: string, timeoutMs = VERIFY_TIMEOUT_MS): Verdict {
	const named = test.trim();
	const abs = named ? resolve(cwd, named) : "";
	const expected = abs && existsSync(abs) ? expectedTests(readFileSync(abs, "utf8")) : [];
	const r = runBounded("sh", ["-c", verifyCommand(test, pytest)], { cwd, env: verifyEnv(cwd), timeoutMs });
	if (!r.started || r.code === 127) throw new Error(`verify: the test command could not start: ${r.out.trim()}`);
	const raw = r.timedOut
		? `${r.out}\n[verify] the test command timed out after ${Math.round(timeoutMs / 1000)} s and was stopped.`
		: r.out;
	const v = parsePytest(r.timedOut ? 1 : (r.code ?? 1), raw, expected);
	return { ...v, output: redactTestPath(raw, test, cwd) };
}

/** Read the gate config from the environment. Read AT SETTLE TIME, never at load:
 * mellum-acceptance sets VERIFY_TEST in its session_start handler, which runs after
 * every extension has loaded. Reading it at extension-init (the old bug) captured an
 * empty VERIFY_TEST and left the gate silently inert for the whole session. */
export function gateConfig() {
	return {
		test: (process.env.VERIFY_TEST ?? "").trim(),
		all: /^(1|true|yes)$/i.test(process.env.VERIFY_ALL ?? ""),
		max: Number.parseInt(process.env.VERIFY_MAX ?? "5", 10),
		pytest: process.env.VERIFY_PYTEST ?? "uv run --offline python -m pytest",
	};
}

export default function (pi: { on: (event: string, handler: (ev: any, ctx?: any) => unknown) => void }) {
	let used = 0;
	pi.on("agent_before_settle", (event: any, ctx: any) => {
		const { test, all, max, pytest } = gateConfig();
		// Active when a named acceptance test is set (mediation) OR whole-suite verify is on (VERIFY_ALL).
		if ((test === "" && !all) || !(used < max)) return undefined;
		const cwd = ctx && typeof ctx.cwd === "string" ? ctx.cwd : process.cwd();
		let v: Verdict;
		try {
			v = runTest(test, pytest, cwd);
		} catch {
			return undefined; // never block settle on our own error
		}
		if (v.passed) return undefined; // every concept met — let it settle
		used += 1;
		return {
			// Pi keeps the entries the last handler returns, so carry the earlier handlers' forward.
			entries: [...(event?.entries ?? []), { type: "custom_message", customType: "mellum-verify", content: gateMessage(v), display: true }],
			continue: true,
		};
	});
}
