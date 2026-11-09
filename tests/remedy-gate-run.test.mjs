import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const gate = await import("../remedies/gate-run.ts");

/** A pytest stand-in: writes the given report lines to $MELLUM_GATE_REPORT, prints `say`, then
 * sleeps `sleepMs` and exits with `exit`. Returned as a VERIFY_PYTEST command. */
function standIn({ lines = [], exit = 0, say = "", sleepMs = 0 }) {
	const dir = mkdtempSync(join(tmpdir(), "gate-standin-"));
	const script = join(dir, "pytest.mjs");
	writeFileSync(script, `
import { appendFileSync } from "node:fs";
for (const line of ${JSON.stringify(lines)}) appendFileSync(process.env.MELLUM_GATE_REPORT, JSON.stringify(line) + "\\n");
process.stdout.write(${JSON.stringify(say)});
setTimeout(() => process.exit(${exit}), ${sleepMs});
`);
	return `"${process.execPath}" ${script}`;
}

async function withPytest(command, fn) {
	const saved = process.env.VERIFY_PYTEST;
	process.env.VERIFY_PYTEST = command;
	try { return await fn(); } finally {
		if (saved === undefined) delete process.env.VERIFY_PYTEST; else process.env.VERIFY_PYTEST = saved;
	}
}

const TWO = [{ name: "test_x.py", source: "def test_a():\n    assert True\n\ndef test_b():\n    assert True\n" }];

function run(files, opts = {}) {
	const dir = mkdtempSync(join(tmpdir(), "gate-copy-"));
	const cwd = opts.cwd ?? mkdtempSync(join(tmpdir(), "gate-ws-"));
	try {
		return gate.runGate(dir, files, opts.project ?? null, cwd, opts.timeoutMs);
	} finally {
		rmSync(dir, { recursive: true, force: true });
	}
}

const outcome = (test, outcome, message = "", when = "call") => ({ event: "outcome", test, when, outcome, message });
const finished = (exit) => ({ event: "finished", exit });

test("expectedTests finds every test function, inside classes too, by file", () => {
	const files = [{ name: "test_x.py", source: "import pytest\n\nclass TestBoard:\n    def test_card(self):\n        pass\n\nasync def test_async():\n    pass\n\ndef helper():\n    pass\n" }, ...TWO];
	assert.deepEqual(gate.expectedTests(files).sort(), ["test_x.py::test_a", "test_x.py::test_async", "test_x.py::test_b", "test_x.py::test_card"]);
});

test("exit 0 with no report is not green", async () => {
	const r = await withPytest(standIn({ exit: 0, say: "2 passed" }), () => run(TWO));
	assert.equal(r.status, "infrastructure");
	assert.match(r.detail, /no report/);
});

test("exit 0 missing one expected function is infrastructure", async () => {
	const lines = [{ event: "collected", tests: ["test_x.py::test_a"] }, outcome("test_x.py::test_a", "passed"), finished(0)];
	const r = await withPytest(standIn({ lines }), () => run(TWO));
	assert.equal(r.status, "infrastructure");
	assert.deepEqual(r.missing, ["test_x.py::test_b"]);
});

test("a skipped expected function is not green", async () => {
	const lines = [outcome("test_x.py::test_a", "passed"), outcome("test_x.py::test_b", "skipped", "", "setup"), finished(0)];
	const r = await withPytest(standIn({ lines }), () => run(TWO));
	assert.equal(r.status, "infrastructure");
	assert.deepEqual(r.missing, ["test_x.py::test_b"]);
});

test("every expected function passing with exit 0 is green", async () => {
	const lines = [outcome("test_x.py::test_a", "passed"), outcome("test_x.py::test_b", "passed"), finished(0)];
	const r = await withPytest(standIn({ lines }), () => run(TWO));
	assert.equal(r.status, "green");
	assert.equal(r.execution, "workspace", "a VERIFY_PYTEST override is recorded as the workspace's own run");
});

test("a failing outcome is red and keeps its assertion, not the server log", async () => {
	const lines = [outcome("test_x.py::test_a", "passed"), outcome("test_x.py::test_b", "failed", "AssertionError: expected the Open badge"), finished(1)];
	const say = "INFO:     Uvicorn running on http://127.0.0.1:8000\nINFO:     127.0.0.1 - GET / 200\n";
	const r = await withPytest(standIn({ lines, exit: 1, say }), () => run(TWO));
	assert.equal(r.status, "red");
	assert.deepEqual(r.failures, [{ test: "test_b", message: "AssertionError: expected the Open badge" }]);
	assert.doesNotMatch(JSON.stringify(r), /Uvicorn/);
});

test("a collection error is red with its message", async () => {
	const lines = [{ event: "collect_error", message: "ModuleNotFoundError: No module named 'app'" }, finished(2)];
	const r = await withPytest(standIn({ lines, exit: 2 }), () => run(TWO));
	assert.equal(r.status, "red");
	assert.match(r.failures[0].message, /No module named 'app'/);
});

test("a hang is red, names the test that was running and its seconds", async () => {
	const lines = [outcome("test_x.py::test_a", "passed"), { event: "start", test: "test_x.py::test_b" }];
	const r = await withPytest(standIn({ lines, sleepMs: 20000 }), () => run(TWO, { timeoutMs: 1500 }));
	assert.equal(r.status, "red");
	assert.equal(r.running, "test_b");
	assert.equal(r.timedOutSeconds, 2);
});

test("parametrized and class tests count by base function", async () => {
	const files = [{ name: "test_x.py", source: "import pytest\n\nclass TestBoard:\n    def test_card(self):\n        pass\n\n@pytest.mark.parametrize('n', [1, 2])\ndef test_p(n):\n    pass\n" }];
	const lines = [outcome("test_x.py::TestBoard::test_card", "passed"), outcome("test_x.py::test_p[1]", "passed"), outcome("test_x.py::test_p[2]", "passed"), finished(0)];
	const r = await withPytest(standIn({ lines }), () => run(files));
	assert.equal(r.status, "green");
});

test("one failing parameter fails its function", async () => {
	const files = [{ name: "test_x.py", source: "def test_p(n):\n    pass\n" }];
	const lines = [outcome("test_x.py::test_p[1]", "passed"), outcome("test_x.py::test_p[2]", "failed", "assert 2 == 1"), finished(1)];
	const r = await withPytest(standIn({ lines, exit: 1 }), () => run(files));
	assert.equal(r.status, "red");
	assert.equal(r.failures[0].test, "test_p[2]");
});

test("a pytest command that cannot start is infrastructure", async () => {
	const r = await withPytest("/no/such/pytest-binary", () => run(TWO));
	assert.equal(r.status, "infrastructure");
});

test("freezeProject is null without a pyproject.toml", () => {
	assert.equal(gate.freezeProject(mkdtempSync(join(tmpdir(), "gate-ws-"))), null);
});

// Real pytest under uv, with the dependencies frozen at load. The Easy suite's locked project is
// synced online first, so the gate's `--offline` run finds its packages in uv's cache on CI too.
const BASE = new URL("../learn/code/suites/easy/base/", import.meta.url).pathname;

function realWorkspace() {
	const cwd = mkdtempSync(join(tmpdir(), "gate-real-ws-"));
	for (const name of ["pyproject.toml", "uv.lock"]) copyFileSync(join(BASE, name), join(cwd, name));
	writeFileSync(join(cwd, "app.py"), "def answer():\n    return 42\n");
	const warm = spawnSync("uv", ["sync", "--frozen", "--project", cwd], { encoding: "utf8", env: { ...process.env, UV_PROJECT_ENVIRONMENT: join(cwd, ".warm-venv") } });
	assert.equal(warm.status, 0, warm.stderr);
	return cwd;
}

test("a real pytest run under uv is green on a passing project and red with its assertion", () => {
	const cwd = realWorkspace();
	const project = gate.freezeProject(cwd);
	assert.ok(project);
	const pass = [{ name: "test_01_x.py", source: "from app import answer\n\ndef test_answer():\n    assert answer() == 42\n" }];
	const fail = [{ name: "test_01_x.py", source: "from app import answer\n\ndef test_answer():\n    assert answer() == 43\n" }];
	const green = run(pass, { cwd, project });
	assert.equal(green.status, "green", green.detail);
	assert.equal(green.execution, "frozen");
	const red = run(fail, { cwd, project });
	assert.equal(red.status, "red", red.detail);
	assert.match(red.failures[0].message, /assert 42 == 43/);
});

test("a workspace pyproject edited after load changes nothing", () => {
	const cwd = realWorkspace();
	const project = gate.freezeProject(cwd);
	writeFileSync(join(cwd, "pyproject.toml"), "this is not toml [[[\n");
	rmSync(join(cwd, "uv.lock"));
	const pass = [{ name: "test_01_x.py", source: "from app import answer\n\ndef test_answer():\n    assert answer() == 42\n" }];
	const r = run(pass, { cwd, project });
	assert.equal(r.status, "green", r.detail);
});

// --- Review fixes -----------------------------------------------------------------------------------

test("the gate keeps where uv's cache and Python live, and drops what changes resolution", async () => {
	const lines = [{ event: "outcome", test: "test_x.py::test_a", when: "call", outcome: "failed", message: "ENV" }, { event: "finished", exit: 1 }];
	const dir = mkdtempSync(join(tmpdir(), "gate-standin-"));
	const script = join(dir, "pytest.mjs");
	writeFileSync(script, `
import { appendFileSync } from "node:fs";
const seen = ["UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_PYTHON_BIN_DIR", "UV_PYTHON_DOWNLOADS", "UV_INDEX_URL", "UV_PROJECT_ENVIRONMENT", "PYTEST_ADDOPTS"].map((k) => k + "=" + (process.env[k] ?? "-")).join(" ");
for (const line of ${JSON.stringify(lines)}) appendFileSync(process.env.MELLUM_GATE_REPORT, JSON.stringify({ ...line, message: line.message === "ENV" ? seen : line.message }) + "\\n");
process.exit(1);
`);
	const saved = Object.fromEntries(["UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "UV_PYTHON_BIN_DIR", "UV_PYTHON_DOWNLOADS", "UV_INDEX_URL", "UV_PROJECT_ENVIRONMENT", "PYTEST_ADDOPTS"].map((k) => [k, process.env[k]]));
	Object.assign(process.env, { UV_CACHE_DIR: "/c", UV_PYTHON_INSTALL_DIR: "/p", UV_PYTHON_BIN_DIR: "/b", UV_PYTHON_DOWNLOADS: "never", UV_INDEX_URL: "http://evil", UV_PROJECT_ENVIRONMENT: "/venv", PYTEST_ADDOPTS: "-p evil" });
	try {
		const r = await withPytest(`"${process.execPath}" ${script}`, () => run(TWO));
		assert.equal(r.failures[0].message, "UV_CACHE_DIR=/c UV_PYTHON_INSTALL_DIR=/p UV_PYTHON_BIN_DIR=/b UV_PYTHON_DOWNLOADS=never UV_INDEX_URL=- UV_PROJECT_ENVIRONMENT=- PYTEST_ADDOPTS=-");
	} finally {
		for (const [k, v] of Object.entries(saved)) v === undefined ? delete process.env[k] : (process.env[k] = v);
	}
});

test("a packaged src-layout project is not built, and its package imports", () => {
	realWorkspace(); // warms uv's cache with the pinned pytest
	const cwd = mkdtempSync(join(tmpdir(), "gate-pkg-ws-"));
	writeFileSync(join(cwd, "pyproject.toml"), '[project]\nname = "pkgapp"\nversion = "0.1.0"\nrequires-python = ">=3.12"\ndependencies = []\n\n[dependency-groups]\ndev = ["pytest==8.3.4"]\n\n[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n');
	mkdirSync(join(cwd, "src", "pkgapp"), { recursive: true });
	writeFileSync(join(cwd, "src", "pkgapp", "__init__.py"), "ANSWER = 42\n");
	const project = gate.freezeProject(cwd);
	const r = run([{ name: "test_01_x.py", source: "from pkgapp import ANSWER\n\ndef test_answer():\n    assert ANSWER == 42\n" }], { cwd, project });
	assert.equal(r.status, "green", r.detail + JSON.stringify(r.failures));
});
