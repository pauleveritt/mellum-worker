import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, renameSync, rmSync, symlinkSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join } from "node:path";

const unit = await import("../remedies/guard/supplied-tests.ts");
const ORIGINAL = "def test_home():\n    assert ORIGINAL\n";

function fakePi() {
	const handlers = {};
	return {
		handlers,
		on(event, handler) { (handlers[event] ??= []).push(handler); },
		names() { return Object.keys(handlers).sort(); },
	};
}

function workspace() {
	const cwd = mkdtempSync(join(tmpdir(), "supplied-ws-"));
	mkdirSync(join(cwd, "tests"));
	writeFileSync(join(cwd, "tests", "test_home.py"), ORIGINAL);
	writeFileSync(join(cwd, "conftest.py"), "# supplied\n");
	return cwd;
}

function installed(cwd, list = `tests/test_home.py${delimiter}conftest.py`) {
	const saved = process.env.MELLUM_SUPPLIED_TESTS;
	process.env.MELLUM_SUPPLIED_TESTS = list;
	const pi = fakePi();
	try {
		unit.install(pi, { cwd });
	} finally {
		if (saved === undefined) delete process.env.MELLUM_SUPPLIED_TESTS; else process.env.MELLUM_SUPPLIED_TESTS = saved;
	}
	return pi;
}

const call = (pi, toolName, input) => pi.handlers.tool_call[0]({ toolName, input }, {});
const result = (pi, toolName = "bash") => pi.handlers.tool_result[0]({ toolName, content: [{ type: "text", text: "done" }], isError: false }, {});
const home = (cwd) => join(cwd, "tests", "test_home.py");

test("guard/supplied-tests installs nothing when no supplied test is named", () => {
	const saved = process.env.MELLUM_SUPPLIED_TESTS;
	delete process.env.MELLUM_SUPPLIED_TESTS;
	const pi = fakePi();
	unit.install(pi, { cwd: workspace() });
	assert.deepEqual(pi.names(), []);
	if (saved !== undefined) process.env.MELLUM_SUPPLIED_TESTS = saved;
});

test("guard/supplied-tests takes the list out of the environment when it loads", () => {
	process.env.MELLUM_SUPPLIED_TESTS = "tests/test_home.py";
	unit.install(fakePi(), { cwd: workspace() });
	assert.equal(process.env.MELLUM_SUPPLIED_TESTS, undefined);
});

test("guard/supplied-tests refuses edit and write on a supplied test, by any spelling of its path", () => {
	const cwd = workspace();
	const pi = installed(cwd);
	for (const path of ["tests/test_home.py", "./tests/../tests/test_home.py", home(cwd)]) {
		for (const tool of ["edit", "write"]) {
			const decision = call(pi, tool, { path, content: "x" });
			assert.equal(decision?.block, true, `${tool} ${path}`);
			assert.match(decision.reason, /supplied/);
			assert.match(decision.reason, /new test file/);
		}
	}
});

test("guard/supplied-tests lets the model write a new test file and edit the code", () => {
	const cwd = workspace();
	const pi = installed(cwd);
	assert.equal(call(pi, "write", { path: "tests/test_board.py", content: "x" }), undefined);
	assert.equal(call(pi, "edit", { path: "app.py" }), undefined);
	assert.equal(call(pi, "bash", { command: "sed -i '' s/a/b/ tests/test_home.py" }), undefined, "bash is answered after it runs");
});

const routes = {
	"an overwrite (sed -i, a redirect)": (cwd) => writeFileSync(home(cwd), "def test_home():\n    assert True\n"),
	"a delete (rm)": (cwd) => unlinkSync(home(cwd)),
	"a move (mv)": (cwd) => renameSync(home(cwd), join(cwd, "tests", "moved.py")),
	"a symlink with the same bytes": (cwd) => {
		writeFileSync(join(cwd, "elsewhere.py"), ORIGINAL);
		unlinkSync(home(cwd));
		symlinkSync(join(cwd, "elsewhere.py"), home(cwd));
	},
	"a directory in its place": (cwd) => {
		unlinkSync(home(cwd));
		mkdirSync(home(cwd));
		writeFileSync(join(home(cwd), "x.py"), "");
	},
	"the whole tests directory removed": (cwd) => rmSync(join(cwd, "tests"), { recursive: true }),
};

for (const [route, mutate] of Object.entries(routes)) {
	test(`guard/supplied-tests restores a supplied test after ${route}`, () => {
		const cwd = workspace();
		const pi = installed(cwd);
		mutate(cwd);
		const out = result(pi);
		assert.ok(lstatSync(home(cwd)).isFile(), "a regular file again");
		assert.equal(readFileSync(home(cwd), "utf8"), ORIGINAL);
		assert.equal(out.content[0].text, "done", "the tool's own result is kept");
		assert.match(out.content.at(-1).text, /tests\/test_home\.py/);
		assert.match(out.content.at(-1).text, /new test file/);
	});
}

test("guard/supplied-tests leaves a new test file alone and says nothing when nothing changed", () => {
	const cwd = workspace();
	const pi = installed(cwd);
	writeFileSync(join(cwd, "tests", "test_board.py"), "def test_board():\n    pass\n");
	assert.equal(result(pi), undefined);
	assert.ok(existsSync(join(cwd, "tests", "test_board.py")));
});

test("guard/supplied-tests carries the metadata the remedies list is generated from", () => {
	for (const key of ["pathology", "does", "lesson", "evidence"]) assert.equal(typeof unit.meta[key], "string");
	for (const key of ["pathology", "does", "evidence"]) assert.ok(unit.meta[key].length > 0, key);
});
