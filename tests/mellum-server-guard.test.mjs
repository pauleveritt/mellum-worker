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
