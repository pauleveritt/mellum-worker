/**
 * mellum-ncm — a next-concept-modelling verify gate (a Pi extension).
 *
 * The worker's own "done" is not trusted. When it tries to settle, this re-runs
 * the named acceptance test and, while it is red, sends the worker back with the
 * **unmet concepts** — the specific failing test functions — up to NCM_MAX
 * times. It brings the ladder's direct-only verify/re-dispatch into any Pi
 * session (Mellum Mode included) at the concept grain, reusing the
 * `agent_before_settle -> continue` pattern proven by the empty-final nudge in
 * `mellum-guards.ts`.
 *
 * Self-contained: Node + Pi hooks only (no Pi-internal imports), so it loads
 * with `-e extensions/mellum-ncm.ts` directly — no patch into a Pi checkout.
 *
 * Config (env):
 *   NCM_TEST    a named acceptance test to re-run (e.g. tests/test_phase4.py),
 *               relative to the worker's cwd — the mediation grain.
 *   NCM_ALL     set (1/true/yes) to verify the WHOLE visible suite instead of a
 *               named test — the agnostic developer-loop gate (run everything,
 *               refuse to settle until green). Inert unless NCM_TEST or NCM_ALL.
 *   NCM_MAX     how many times to send the worker back (default 5).
 *   NCM_PYTEST  the pytest command (default: uv run --offline python -m pytest).
 */
import { execSync } from "node:child_process";

export interface Verdict {
	passed: boolean;
	/** The failing test functions — the concepts still unmet. */
	failures: string[];
	output: string;
}

/** Parse `pytest -q` output: passed? and the failing `test_*` names (unmet concepts). */
export function parsePytest(code: number, output: string): Verdict {
	const failures = [...output.matchAll(/^FAILED\s+\S+::(\S+?)(?:\s|$)/gm)].map((m) => m[1]);
	return { passed: code === 0, failures, output };
}

/** The message handed back to the worker naming the concepts it has not met. */
export function gateMessage(v: Verdict): string {
	const concepts = v.failures.length ? v.failures.join(", ") : "(see output below)";
	const tail = v.output.slice(-1200);
	return (
		"[mellum-ncm] The tests still fail, so you are not done. " +
		`Unmet concepts (failing tests): ${concepts}. ` +
		"Change the code so each of these passes — one concept at a time — then stop.\n\n" +
		tail
	);
}

/** The pytest command: a named test runs just that file; an empty test runs the whole visible suite. */
export function verifyCommand(test: string, pytest: string): string {
	const path = (test || "").trim();
	return `${pytest}${path ? ` ${path}` : ""} -q -p no:warnings --tb=short`;
}

/** The verify subprocess environment: the worker cwd on PYTHONPATH, so a held-out
 * acceptance test (which lives beside the workspace) can still `from app import app`,
 * and VIRTUAL_ENV stripped so uv does not warn. Mirrors the harness grader's grade_env.
 * Without the PYTHONPATH the contract errors at collection (ModuleNotFoundError: app),
 * the gate cannot read unmet concepts, and it silently never redispatches. */
export function verifyEnv(cwd: string): NodeJS.ProcessEnv {
	const env: NodeJS.ProcessEnv = { ...process.env, PYTHONPATH: cwd };
	delete env.VIRTUAL_ENV;
	return env;
}

/** Run the verification (a named test, or the whole suite when `test` is empty) in `cwd`; never throws. */
export function runTest(test: string, pytest: string, cwd: string): Verdict {
	try {
		const out = execSync(verifyCommand(test, pytest), {
			cwd,
			env: verifyEnv(cwd),
			encoding: "utf8",
			stdio: ["ignore", "pipe", "pipe"],
		});
		return parsePytest(0, out);
	} catch (e: any) {
		const code = typeof e?.status === "number" ? e.status : 1;
		return parsePytest(code, `${e?.stdout ?? ""}${e?.stderr ?? ""}`);
	}
}

/** Read the gate config from the environment. Read AT SETTLE TIME, never at load:
 * mellum-acceptance sets NCM_TEST in its session_start handler, which runs after
 * every extension has loaded. Reading it at extension-init (the old bug) captured an
 * empty NCM_TEST and left the gate silently inert for the whole session. */
export function gateConfig() {
	return {
		test: (process.env.NCM_TEST ?? "").trim(),
		all: /^(1|true|yes)$/i.test(process.env.NCM_ALL ?? ""),
		max: Number.parseInt(process.env.NCM_MAX ?? "5", 10),
		pytest: process.env.NCM_PYTEST ?? "uv run --offline python -m pytest",
	};
}

export default function (pi: { on: (event: string, handler: (ev: any, ctx?: any) => unknown) => void }) {
	let used = 0;
	pi.on("agent_before_settle", (_event: any, ctx: any) => {
		const { test, all, max, pytest } = gateConfig();
		// Active when a named acceptance test is set (mediation) OR whole-suite verify is on (NCM_ALL).
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
			entries: [{ type: "custom_message", customType: "mellum-ncm", content: gateMessage(v), display: true }],
			continue: true,
		};
	});
}
