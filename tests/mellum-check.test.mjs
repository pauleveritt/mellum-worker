import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import test from "node:test";
import {
	adminBaseOf,
	checkSetup,
	DEFAULT_BASE_URL,
	fetchJson,
	formatFindings,
	gatherInputs,
	loadExpected,
	parseJsonc,
	readProvider,
	serverCheck,
	serverNCtx,
	serverRootOf,
} from "../extensions/mellum-check.ts";

const ROOT = resolve(import.meta.dirname, "..");
const FIX = join(ROOT, "tests/fixtures/check");
const fixture = (name) => readFileSync(join(FIX, name), "utf8");
const json = (name) => JSON.parse(fixture(name));
const ok = (value) => ({ ok: true, value });
const expected = loadExpected();
const BASE = "http://127.0.0.1:8001/v1";
const ROOT_URL = "http://127.0.0.1:8001";

const inputs = (over = {}) => ({
	baseUrl: BASE,
	health: ok(json("health.json")),
	props: ok(json("props.json")),
	models: ok(json("v1-models.json")),
	...over,
});
const byId = (findings, id) => findings.find((f) => f.id === id);

test("loadExpected reads the shipped llama-model-settings.json", () => {
	assert.equal(expected.modelId, "Mellum2.1-12B-A2.5B-Thinking");
	assert.equal(expected.nCtxMin, 50000);
});

test("the ids are only server, model and context", () => {
	const ids = new Set(checkSetup(inputs(), expected).map((f) => f.id));
	assert.deepEqual([...ids].sort(), ["context", "model", "server"]);
});

test("a full match: server, model and context are all ok, no fail or warn", () => {
	const f = checkSetup(inputs(), expected);
	assert.equal(byId(f, "server").level, "ok");
	assert.equal(byId(f, "model").level, "ok");
	assert.equal(byId(f, "context").level, "ok");
	assert.deepEqual(f.filter((x) => x.level === "fail" || x.level === "warn"), []);
});

test("server down: only the server fail finding, with the start fix; model and context are not reported", () => {
	const f = checkSetup(inputs({ health: { ok: false, error: "ECONNREFUSED" } }), expected);
	assert.deepEqual(
		f.map((x) => x.id),
		["server"],
	);
	const server = byId(f, "server");
	assert.equal(server.level, "fail");
	assert.match(server.message, /ECONNREFUSED/);
	assert.match(server.message, new RegExp(`${ROOT_URL}/health`));
	assert.equal(server.fix, "start it: uv run scripts/backend.py start");
	assert.equal(byId(f, "model"), undefined);
	assert.equal(byId(f, "context"), undefined);
});

test("health that does not report status ok fails the server check", () => {
	const f = checkSetup(inputs({ health: ok({ status: "loading" }) }), expected);
	assert.equal(byId(f, "server").level, "fail");
	assert.match(byId(f, "server").message, /did not report status ok/);
	assert.equal(byId(f, "model"), undefined);
});

test("the model missing from /v1/models fails, while server and context stay ok", () => {
	const f = checkSetup(inputs({ models: ok({ object: "list", data: [{ id: "other" }] }) }), expected);
	const model = byId(f, "model");
	assert.equal(model.level, "fail");
	assert.match(model.message, /is not served/);
	assert.ok(model.fix);
	assert.equal(byId(f, "server").level, "ok");
	assert.equal(byId(f, "context").level, "ok");
});

test("a context window below the measured minimum fails with the relaunch fix", () => {
	const f = checkSetup(inputs({ props: ok(json("props-low.json")) }), expected);
	const context = byId(f, "context");
	assert.equal(context.level, "fail");
	assert.match(context.message, /context window 32768 is below the measured 50000/);
	assert.match(context.fix, /relaunch/);
	assert.doesNotMatch(context.fix, /curl -X PUT/);
	assert.equal(byId(f, "server").level, "ok");
	assert.equal(byId(f, "model").level, "ok");
});

test("props that cannot be read warns, it does not fail", () => {
	const unreadable = checkSetup(inputs({ props: { ok: false, status: 500, error: "HTTP 500" } }), expected);
	assert.equal(byId(unreadable, "context").level, "warn");
	assert.match(byId(unreadable, "context").message, /could not read the context window from \/props/);
	const noField = checkSetup(inputs({ props: ok({ default_generation_settings: {} }) }), expected);
	assert.equal(byId(noField, "context").level, "warn");
});

test("serverNCtx reads default_generation_settings.n_ctx, undefined when absent", () => {
	assert.equal(serverNCtx(json("props.json")), 50176);
	assert.equal(serverNCtx(json("props-low.json")), 32768);
	assert.equal(serverNCtx({ default_generation_settings: {} }), undefined);
	assert.equal(serverNCtx({}), undefined);
	assert.equal(serverNCtx("nonsense"), undefined);
});

test("readProvider pi: the llamacpp baseUrl comes from the file", () => {
	const reads = [];
	const r = readProvider("pi", "/home/user", (p) => (reads.push(p), fixture("pi-models.json")));
	assert.deepEqual(reads, [join("/home/user", ".pi", "agent", "models.json")]);
	assert.equal(r.baseUrl, BASE);
	assert.equal(r.error, undefined);
});

test("readProvider pi: without a llamacpp provider, or unreadable or invalid files, falls back to the default", () => {
	assert.equal(readProvider("pi", "/home/user", () => fixture("pi-models-no-omlx.json")).baseUrl, DEFAULT_BASE_URL);
	assert.equal(readProvider("pi", "/h", () => undefined).baseUrl, DEFAULT_BASE_URL);
	assert.equal(
		readProvider("pi", "/h", () => {
			throw new Error("EACCES");
		}).baseUrl,
		DEFAULT_BASE_URL,
	);
	assert.equal(readProvider("pi", "/h", () => "{nope").baseUrl, DEFAULT_BASE_URL);
});

test("parseJsonc reads JSON with comments and trailing commas; empty text is undefined", () => {
	assert.deepEqual(parseJsonc('{ "a": 1, /* c */ "b": [2, 3,], } // tail'), { a: 1, b: [2, 3] });
	assert.equal(parseJsonc("   "), undefined);
});

test("formatFindings: fails first, then warns, then info; oks collapse into a count", () => {
	const out = formatFindings([
		{ id: "server", level: "ok", message: "answers" },
		{ id: "context", level: "warn", message: "could not read" },
		{ id: "model", level: "fail", message: "not served", fix: "start the server" },
	]);
	const at = (s) => out.indexOf(s);
	assert.ok(at("not served") >= 0 && at("not served") < at("could not read"));
	assert.ok(out.includes("start the server"));
	assert.ok(out.includes("1 checks ok"));
	assert.ok(!out.includes("answers"));
	assert.equal(formatFindings([{ id: "server", level: "ok", message: "a" }, { id: "model", level: "ok", message: "b" }]).trim(), "2 checks ok");
});

test("serverRootOf and adminBaseOf strip a trailing slash and /v1", () => {
	assert.equal(serverRootOf("http://127.0.0.1:8001/v1"), ROOT_URL);
	assert.equal(serverRootOf("http://127.0.0.1:8001/v1/"), ROOT_URL);
	assert.equal(serverRootOf("http://h:9/"), "http://h:9");
	assert.equal(adminBaseOf("http://127.0.0.1:8001/v1"), ROOT_URL);
});

test("fetchJson: a JSON body, an HTTP error status, and a rejected fetch", async () => {
	const seen = [];
	const fake = (status, body) => async (url, init) => {
		seen.push({ url, method: init?.method ?? "GET", signal: init?.signal instanceof AbortSignal });
		return { ok: status < 300, status, json: async () => body };
	};
	assert.deepEqual(await fetchJson(`${ROOT_URL}/health`, { timeoutMs: 1000, fetch: fake(200, { status: "ok" }) }), { ok: true, value: { status: "ok" } });
	assert.deepEqual(seen, [{ url: `${ROOT_URL}/health`, method: "GET", signal: true }]);
	assert.deepEqual(await fetchJson(ROOT_URL, { timeoutMs: 1000, fetch: fake(401, {}) }), { ok: false, status: 401, error: "HTTP 401" });
	const refused = async () => {
		throw Object.assign(new TypeError("fetch failed"), { cause: { code: "ECONNREFUSED" } });
	};
	assert.deepEqual(await fetchJson(ROOT_URL, { timeoutMs: 1000, fetch: refused }), { ok: false, error: "ECONNREFUSED" });
});

test("fetchJson gives up at the timeout even when the fetch ignores its abort signal", async () => {
	const t0 = Date.now();
	const r = await fetchJson(ROOT_URL, { timeoutMs: 50, fetch: () => new Promise(() => {}) });
	assert.deepEqual(r, { ok: false, error: "timeout" });
	assert.ok(Date.now() - t0 < 1000, `took ${Date.now() - t0} ms`);
});

test("serverCheck: GETs /health then /props and returns up with the context window; unreachable is up null", async () => {
	const seen = [];
	const get = (health, props) => async (url) => {
		const u = String(url);
		seen.push(u);
		if (u.endsWith("/health")) return { ok: true, status: 200, json: async () => health };
		if (u.endsWith("/props")) return { ok: true, status: 200, json: async () => props };
		return { ok: false, status: 404, json: async () => ({}) };
	};
	assert.deepEqual(await serverCheck(ROOT_URL, { timeoutMs: 1000, fetch: get({ status: "ok" }, json("props.json")) }), { up: true, nCtx: 50176 });
	assert.deepEqual(seen, [`${ROOT_URL}/health`, `${ROOT_URL}/props`]);
	assert.deepEqual(await serverCheck(ROOT_URL, { timeoutMs: 1000, fetch: get({ status: "loading" }, json("props-low.json")) }), { up: false, nCtx: 32768 });
	const refused = async () => {
		throw new TypeError("fetch failed");
	};
	assert.deepEqual(await serverCheck(ROOT_URL, { timeoutMs: 1000, fetch: refused }), { up: null });
	const notOk = async () => ({ ok: false, status: 500, json: async () => ({}) });
	assert.deepEqual(await serverCheck(ROOT_URL, { timeoutMs: 1000, fetch: notOk }), { up: null });
});

test("gatherInputs reads the host config and GETs /health, /props and /models from its baseUrl", async () => {
	const urls = [];
	const config = { providers: { llamacpp: { baseUrl: "http://h:9/v1" } } };
	const files = { [join("/home/u", ".pi", "agent", "models.json")]: JSON.stringify(config) };
	const got = await gatherInputs("pi", {
		home: "/home/u",
		read: (p) => files[p],
		get: async (url) => {
			urls.push(url);
			return { ok: false, error: "x" };
		},
	});
	assert.deepEqual(urls.sort(), ["http://h:9/health", "http://h:9/props", "http://h:9/v1/models"]);
	assert.equal(got.baseUrl, "http://h:9/v1");
});
