/** Run frozen acceptance tests once and say, from evidence, whether they passed.
 *
 * Exit code 0 is not evidence: a pytest the project supplies, a skip, or a test that never ran all
 * exit 0. So a small plugin, written beside the frozen copy, reports every collected test, every
 * outcome and the finish to a file, and green needs a pass for every test function in the frozen
 * source. Dependencies come from the project's `pyproject.toml` and `uv.lock` as they were when the
 * session began, in an environment of their own; the project's conftest, pytest config and
 * environment overrides take no part. This is not a sandbox: the model's code still runs in-process,
 * and the harness grades the result again on a trusted copy. Nothing here names a file or a value.
 *
 * Three answers: `green` (every expected function passed), `red` (the model's code failed, errored at
 * collection, or hung), `infrastructure` (our tooling could not give an answer). */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, delimiter, join } from "node:path";
import { runBounded } from "../extensions/bounded.ts";

export type Frozen = { name: string; source: string };
export type FrozenProject = { pyproject: string; lock: string | null };
export type GateFailure = { test: string; message: string };
export type GateRun = {
	status: "green" | "red" | "infrastructure";
	failures: GateFailure[];
	/** Expected functions (`file::name`) with no pass. */
	missing: string[];
	detail: string;
	timedOutSeconds?: number;
	/** The test that was running when a hang was stopped. */
	running?: string;
	/** `frozen`: our pinned environment; `workspace`: a VERIFY_PYTEST override or no project file. */
	execution: "frozen" | "workspace";
};

/** Below the harness's 180 s stall cutoff, so a hung test cannot stall the session. */
export const GATE_TIMEOUT_MS = 150_000;
const PLUGIN = "_mellum_gate_report";

const PLUGIN_SOURCE = `"""Reports each collected test and outcome for the settle gate. Written by remedies/gate-run.ts."""
import json
import os

_PATH = os.environ.get("MELLUM_GATE_REPORT")


def _emit(record):
    if _PATH:
        with open(_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\\n")


def pytest_collection_finish(session):
    _emit({"event": "collected", "tests": [item.nodeid for item in session.items]})


def pytest_collectreport(report):
    if report.failed:
        _emit({"event": "collect_error", "message": str(report.longrepr)[-2000:]})


def pytest_runtest_logstart(nodeid, location):
    _emit({"event": "start", "test": nodeid})


def pytest_runtest_logreport(report):
    crash = getattr(report.longrepr, "reprcrash", None)
    message = crash.message if crash is not None else (str(report.longrepr) if report.failed else "")
    _emit({"event": "outcome", "test": report.nodeid, "when": report.when,
           "outcome": report.outcome, "message": message[:2000]})


def pytest_sessionfinish(session, exitstatus):
    _emit({"event": "finished", "exit": int(exitstatus)})
`;

/** Every `test*` function in the frozen source, as `file::name`; methods count by their own name. */
export function expectedTests(files: Frozen[]): string[] {
	const found = new Set<string>();
	for (const f of files) {
		for (const m of f.source.matchAll(/^[ \t]*(?:async[ \t]+)?def[ \t]+(test\w*)[ \t]*\(/gm)) found.add(`${f.name}::${m[1]}`);
	}
	return [...found];
}

/** The project's dependency files, read now; null when there is no pyproject.toml. */
export function freezeProject(cwd: string): FrozenProject | null {
	const pyproject = join(cwd, "pyproject.toml");
	if (!existsSync(pyproject)) return null;
	const lock = join(cwd, "uv.lock");
	return { pyproject: readFileSync(pyproject, "utf8"), lock: existsSync(lock) ? readFileSync(lock, "utf8") : null };
}

/** `file::name` for a node id `path/file.py::Class::name[param]`. */
function functionKey(nodeid: string): string {
	const parts = nodeid.split("::");
	return `${basename(parts[0])}::${parts[parts.length - 1].replace(/\[.*$/, "")}`;
}

/** What the model is told a test is called: the node id without the copy's path. */
function shown(nodeid: string): string {
	return nodeid.split("::").slice(1).join("::") || basename(nodeid);
}

/** Where uv keeps its cache and its Pythons: kept, so a warmed host (a pod's session user) stays warm.
 * Every other `UV_*` variable can change what is resolved or installed, so it is dropped. */
const UV_LOCATIONS = new Set(["UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_PYTHON_BIN_DIR", "UV_PYTHON_DOWNLOADS", "UV_TOOL_DIR"]);

function gateEnv(cwd: string, dir: string, report: string, extra: Record<string, string>): NodeJS.ProcessEnv {
	const env: NodeJS.ProcessEnv = {};
	for (const [key, value] of Object.entries(process.env)) {
		if (/^(PYTEST|PYTHON)/.test(key) || key === "VIRTUAL_ENV" || key === "CONDA_PREFIX") continue;
		if (key.startsWith("UV_") && !UV_LOCATIONS.has(key)) continue;
		env[key] = value;
	}
	// A src-layout project's package imports from the project as it is; the project itself is never built.
	const src = join(cwd, "src");
	const path = [cwd, ...(existsSync(src) ? [src] : []), dir];
	return { ...env, ...extra, PYTHONPATH: path.join(delimiter), PYTEST_DISABLE_PLUGIN_AUTOLOAD: "1", PYTHONUTF8: "1", PYTHONDONTWRITEBYTECODE: "1", MELLUM_GATE_REPORT: report };
}

function quote(s: string): string {
	return `'${s.replace(/'/g, `'\\''`)}'`;
}

type Line = { event: string; test?: string; tests?: string[]; when?: string; outcome?: string; message?: string; exit?: number };

function readReport(path: string): Line[] | null {
	if (!existsSync(path)) return null;
	const lines: Line[] = [];
	for (const raw of readFileSync(path, "utf8").split("\n")) {
		if (!raw.trim()) continue;
		try {
			lines.push(JSON.parse(raw));
		} catch {
			// A line cut short by a killed run says nothing.
		}
	}
	return lines;
}

/** Run the frozen files from `dir` (a fresh directory outside the project) against the project in `cwd`. */
export function runGate(dir: string, files: Frozen[], project: FrozenProject | null, cwd: string, timeoutMs = GATE_TIMEOUT_MS): GateRun {
	for (const f of files) writeFileSync(join(dir, f.name), f.source);
	writeFileSync(join(dir, `${PLUGIN}.py`), PLUGIN_SOURCE);
	writeFileSync(join(dir, "pytest.ini"), "[pytest]\n");
	const report = join(dir, ".report.jsonl");
	const pytestArgs = [dir, "-q", "-p", PLUGIN, "-p", "no:cacheprovider", "-p", "no:warnings", "--tb=short", "-c", join(dir, "pytest.ini"), "--rootdir", dir, "--confcutdir", dir, "--noconftest", "--import-mode=importlib"];
	const override = process.env.VERIFY_PYTEST;
	const execution: GateRun["execution"] = override === undefined && project ? "frozen" : "workspace";
	let result;
	if (execution === "frozen" && project) {
		const envDir = join(dir, "env");
		mkdirSync(envDir);
		writeFileSync(join(envDir, "pyproject.toml"), project.pyproject);
		if (project.lock !== null) writeFileSync(join(envDir, "uv.lock"), project.lock);
		// Keyed by the frozen inputs, and never the grader's environment: a session's user owns this one.
		const digest = createHash("sha256").update(project.pyproject + (project.lock ?? "")).digest("hex");
		const venv = join(tmpdir(), "mellum-gate-envs", digest);
		// Sync without the project (uv run cannot skip it): a packaged project is never built from a
		// folder that holds only its config. Then run from that environment as it stands.
		const locked = project.lock !== null ? ["--frozen"] : [];
		const sync = ["uv", "--no-config", "sync", "--offline", ...locked, "--project", envDir, "--no-install-project", "--quiet"];
		const test = ["uv", "--no-config", "run", "--offline", "--no-sync", "--project", envDir, "python", "-m", "pytest", ...pytestArgs];
		const command = `${sync.map(quote).join(" ")} && exec ${test.map(quote).join(" ")}`;
		result = runBounded("sh", ["-c", command], { cwd, env: gateEnv(cwd, dir, report, { UV_PROJECT_ENVIRONMENT: venv }), timeoutMs });
	} else {
		const command = `${override ?? "uv run --offline python -m pytest"} ${pytestArgs.map(quote).join(" ")}`;
		result = runBounded("sh", ["-c", command], { cwd, env: gateEnv(cwd, dir, report, {}), timeoutMs });
	}
	const lines = readReport(report) ?? [];
	const expected = expectedTests(files);
	const failures: GateFailure[] = [];
	const passed = new Set<string>();
	const failedKeys = new Set<string>();
	let running: string | undefined;
	for (const line of lines) {
		if (line.event === "start" && line.test) running = line.test;
		if (line.event === "collect_error") failures.push({ test: "collection", message: line.message ?? "" });
		if (line.event !== "outcome" || !line.test) continue;
		if (line.when === "teardown" && running === line.test) running = undefined;
		if (line.outcome === "failed") {
			failures.push({ test: shown(line.test), message: line.message ?? "" });
			failedKeys.add(functionKey(line.test));
		} else if (line.outcome === "passed" && line.when === "call") {
			passed.add(functionKey(line.test));
		}
	}
	const missing = expected.filter((key) => !passed.has(key) || failedKeys.has(key));
	const base = { failures, missing, execution };
	if (result.timedOut) {
		return { ...base, status: "red", detail: "timed out", timedOutSeconds: Math.round(timeoutMs / 1000), running: running ? shown(running) : undefined };
	}
	const tail = result.out.trim().slice(-600);
	if (!result.started || result.code === 127) return { ...base, status: "infrastructure", detail: `the test command could not start: ${tail}` };
	if (lines.length === 0) return { ...base, status: "infrastructure", detail: `no report (exit ${result.code}): ${tail}` };
	if (failures.length > 0) return { ...base, status: "red", detail: `exit ${result.code}` };
	const finish = lines.find((line) => line.event === "finished");
	if (finish?.exit === 0 && result.code === 0 && missing.length === 0) return { ...base, status: "green", detail: "" };
	return { ...base, status: "infrastructure", detail: missing.length ? `no pass for ${missing.join(", ")} (exit ${result.code})` : `exit ${result.code}: ${tail}` };
}
