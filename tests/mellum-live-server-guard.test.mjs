import { test } from "node:test";
import assert from "node:assert/strict";

import {
	isServerStart,
	isLocalHttpProbe,
	liveServerGuard,
	serverGuard,
} from "../extensions/mellum-guards.ts";

// The recorded pathology (2026-11-08 one-pass note): 2 of 3 gated reps never reached the
// exit-gate because the worker, confused by an HTTP behaviour, debugged by spinning up a live
// server and curling localhost — forking a server that disagrees with the in-process TestClient,
// thrashing to the stall guard before settle. The foreground-server guard does not stop it: it
// allows (and even suggests) the background form, which is itself the spiral's fuel.

test("isServerStart: a server start in ANY form — foreground or backgrounded", () => {
	// foreground forms the old guard already catches
	assert.equal(isServerStart("uvicorn app:app --reload"), true);
	assert.equal(isServerStart("uv run python app.py"), true);
	assert.equal(isServerStart("python -m http.server"), true);
	// the background forms the foreground guard deliberately LETS THROUGH — the evasions the note records
	assert.equal(isServerStart("nohup uvicorn app:app >/tmp/s.log 2>&1 &"), true);
	assert.equal(isServerStart("uvicorn app:app &"), true);
	assert.equal(isServerStart(".venv/bin/python app.py &"), true);
	assert.equal(isServerStart("nohup uv run python app.py & echo $!"), true);
});

test("isServerStart: naming a server, running tests, or reading is never a start", () => {
	assert.equal(isServerStart('uv run python -c "import uvicorn"'), false);
	assert.equal(isServerStart("pip show uvicorn"), false);
	assert.equal(isServerStart("grep uvicorn app.py"), false);
	assert.equal(isServerStart("uv run python -m pytest tests"), false);
	assert.equal(isServerStart("cat app.py"), false);
	assert.equal(isServerStart(undefined), false);
});

test("isLocalHttpProbe: curl/wget/httpie against a loopback address — the other half of the spiral", () => {
	assert.equal(isLocalHttpProbe("curl http://localhost:8000/complaints"), true);
	assert.equal(isLocalHttpProbe("curl -s 127.0.0.1:8001/health"), true);
	assert.equal(isLocalHttpProbe("curl http://0.0.0.0:8000/"), true);
	assert.equal(isLocalHttpProbe("wget -qO- http://localhost:5000"), true);
	assert.equal(isLocalHttpProbe("http GET localhost:8000/board"), true); // httpie
	assert.equal(isLocalHttpProbe("curl -X POST http://[::1]:8000/complaints"), true);
	assert.equal(isLocalHttpProbe("nohup curl localhost:8000 &"), true);
});

test("isLocalHttpProbe: a remote fetch, or a read/search that merely mentions a url, is not a probe", () => {
	assert.equal(isLocalHttpProbe("curl https://pypi.org/simple/starlette/"), false);
	assert.equal(isLocalHttpProbe("echo 'curl http://localhost:8000'"), false);
	assert.equal(isLocalHttpProbe("grep localhost app.py"), false);
	assert.equal(isLocalHttpProbe("cat notes_about_localhost.txt"), false);
	assert.equal(isLocalHttpProbe(undefined), false);
});

test("liveServerGuard: blocks a server start in any form and points at the in-process TestClient", () => {
	for (const command of ["uvicorn app:app --reload", "nohup uvicorn app:app &", ".venv/bin/python app.py &"]) {
		const blocked = liveServerGuard({ toolName: "bash", input: { command } });
		assert.equal(blocked?.block, true, command);
		assert.match(blocked.reason, /TestClient/);
		assert.match(blocked.reason, /follow_redirects/);
	}
});

test("liveServerGuard: blocks a loopback HTTP probe and points at the in-process TestClient", () => {
	const blocked = liveServerGuard({ toolName: "bash", input: { command: "curl -s 127.0.0.1:8001/complaints" } });
	assert.equal(blocked?.block, true);
	assert.match(blocked.reason, /TestClient/);
});

test("liveServerGuard: allows tests, reads, a remote fetch, and non-bash tools", () => {
	assert.equal(liveServerGuard({ toolName: "bash", input: { command: "uv run python -m pytest -q" } }), undefined);
	assert.equal(liveServerGuard({ toolName: "bash", input: { command: "grep uvicorn app.py" } }), undefined);
	assert.equal(liveServerGuard({ toolName: "bash", input: { command: "curl https://pypi.org/simple/" } }), undefined);
	assert.equal(liveServerGuard({ toolName: "edit", input: { path: "app.py" } }), undefined);
});

test("contrast: the foreground-server guard lets the spiral's fuel through — why a stricter guard is owed", () => {
	// The background server start the note names as an evasion:
	assert.equal(serverGuard({ toolName: "bash", input: { command: "nohup uvicorn app:app &" } }), undefined);
	// and a curl of localhost is not its concern at all:
	assert.equal(serverGuard({ toolName: "bash", input: { command: "curl 127.0.0.1:8001/health" } }), undefined);
	// the stricter guard catches both:
	assert.equal(liveServerGuard({ toolName: "bash", input: { command: "nohup uvicorn app:app &" } })?.block, true);
	assert.equal(liveServerGuard({ toolName: "bash", input: { command: "curl 127.0.0.1:8001/health" } })?.block, true);
});
