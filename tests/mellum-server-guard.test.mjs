import { test } from "node:test";
import assert from "node:assert/strict";

import {
	isBackgrounded,
	isForegroundServer,
	backgroundForm,
	serverGuard,
} from "../extensions/mellum-guards.ts";

test("isForegroundServer: foreground server commands that would block", () => {
	assert.equal(isForegroundServer("uvicorn app:app --port 8001 --reload"), true);
	assert.equal(isForegroundServer("gunicorn app:app"), true);
	assert.equal(isForegroundServer("python -m http.server"), true);
	assert.equal(isForegroundServer("flask run"), true);
	assert.equal(isForegroundServer("python manage.py runserver"), true);
});

test("serverGuard limits help exemptions to known terminating queries", () => {
	for (const command of [
		"uv run --frozen uvicorn --help",
		"uvicorn --version",
		"uv run --offline --frozen python -m uvicorn --help",
		"python3 -m http.server -h",
		"gunicorn --help",
	]) {
		assert.equal(serverGuard({ toolName: "bash", input: { command } }), undefined, command);
	}
	for (const command of [
		"uvicorn --help && uvicorn app:app",
		"uvicorn --version; uvicorn app:app",
		"uvicorn --help\nuvicorn app:app",
		"uvicorn $(touch marker) --help",
		"uv run python app.py --help",
	]) {
		assert.equal(serverGuard({ toolName: "bash", input: { command } })?.block, true, command);
	}
});

test("isForegroundServer: the python-script forms the ladder-era pattern missed", () => {
	// LC.19's attempt 1 hung on exactly this shape, which the first pattern did not match.
	assert.equal(isForegroundServer("uv run --frozen python app.py"), true);
	assert.equal(isForegroundServer("python app.py"), true);
	assert.equal(isForegroundServer("python3 server.py"), true);
	assert.equal(isForegroundServer("uv run python scripts/serve.py --reload"), true);
	// ... and these must not be caught.
	assert.equal(isForegroundServer("uv run --frozen python -m pytest tests"), false);
	assert.equal(isForegroundServer("python tests/test_app.py"), false);
	assert.equal(isForegroundServer("python -c 'import app'"), false);
});

test("isForegroundServer: a backgrounded server is not blocking", () => {
	assert.equal(isForegroundServer("uvicorn app:app &"), false);
	assert.equal(isForegroundServer("nohup uvicorn app:app >/tmp/s.log 2>&1 &"), false);
	assert.equal(isForegroundServer("uvicorn app:app > log 2>&1 & echo $!"), false);
});

test("isForegroundServer: tests, reads and searches are never servers", () => {
	assert.equal(isForegroundServer("pytest -v test_board.py"), false);
	assert.equal(isForegroundServer("grep -r uvicorn ."), false);
	assert.equal(isForegroundServer("cat app.py"), false);
	assert.equal(isForegroundServer("echo 'start uvicorn'"), false);
	assert.equal(isForegroundServer(undefined), false);
});

test("isBackgrounded: & operator vs redirects and &&", () => {
	assert.equal(isBackgrounded("uvicorn app:app &"), true);
	assert.equal(isBackgrounded("nohup uvicorn app:app &"), true);
	assert.equal(isBackgrounded("python x.py 2>&1"), false); // redirect, not background
	assert.equal(isBackgrounded("a && b"), false); // logical AND, not background
});

test("backgroundForm: detached, logged, prints the pid", () => {
	const bg = backgroundForm("uvicorn app:app --port 8001");
	assert.match(bg, /^nohup uvicorn app:app --port 8001 /);
	assert.match(bg, /&\s*echo "server pid \$!"$/);
});

test("serverGuard: blocks a foreground bash server, allows everything else", () => {
	const blocked = serverGuard({ toolName: "bash", input: { command: "uvicorn app:app --reload" } });
	assert.equal(blocked?.block, true);
	assert.match(blocked.reason, /TestClient/);
	assert.match(blocked.reason, /pid you can kill/);
	assert.equal(serverGuard({ toolName: "bash", input: { command: "pytest -v test_x.py" } }), undefined);
	assert.equal(serverGuard({ toolName: "bash", input: { command: "uvicorn app:app &" } }), undefined);
	assert.equal(serverGuard({ toolName: "edit", input: { path: "app.py" } }), undefined);
});

test("serverGuard permits Python diagnostics that only mention server libraries", () => {
	for (const command of [
		'python -c "import uvicorn, sys; print(uvicorn.__file__)"',
		"uv run --frozen python -c 'import uvicorn; print(uvicorn.__version__)'",
		"python3 -c 'from importlib.metadata import version; print(version(\"uvicorn\"))'",
		"python -c 'from starlette.testclient import TestClient; import app; print(TestClient(app.app).get(\"/\"))'",
		"uv run python -m pip show uvicorn",
		"python -c 'print(\"uvicorn app:app &\")'",
	]) assert.equal(serverGuard({ toolName: "bash", input: { command } }), undefined, command);
});

test("serverGuard checks launches after read commands and background jobs", () => {
	for (const command of [
		"echo ready; uvicorn app:app",
		"cat app.py && uv run python app.py",
		"uvicorn one:app & uvicorn two:app",
		"nohup echo ready; python -m http.server",
		'uvicorn app:app --log-config "a& b.json"',
	]) assert.equal(serverGuard({ toolName: "bash", input: { command } })?.block, true, command);
});

test("serverGuard permits quoted launch descriptions in ordinary commands", () => {
	for (const command of [
		"uv run python -m pytest -k uvicorn",
		"cd project && rg 'uvicorn app:app' .",
		"printf '%s' 'uvicorn app:app; python main.py'",
	]) assert.equal(serverGuard({ toolName: "bash", input: { command } }), undefined, command);
});

test("serverGuard preserves background allowance for pipelines and subshell groups", () => {
	for (const command of [
		"uvicorn app:app | cat &",
		"(uvicorn app:app > /tmp/s.log 2>&1) &",
		"(echo ready; uvicorn app:app) & echo $!",
	]) assert.equal(serverGuard({ toolName: "bash", input: { command } }), undefined, command);
});

test("serverGuard recognizes launches continued across shell lines", () => {
	for (const command of ["python \\\n app.py", "uv run --frozen \\\n python app.py"])
		assert.equal(serverGuard({ toolName: "bash", input: { command } })?.block, true, command);
});
