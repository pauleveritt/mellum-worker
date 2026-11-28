/**
 * The setup check: confirms the local llama-server is up and serving the measured model at the
 * measured context window. llama-server has no admin API and no mutable settings — sampling is
 * per-request from the Pi profile and the server's settings are fixed at launch — so the check only
 * reads: `GET /health` (up), `GET /v1/models` (the model is served), and `GET /props` (the launched
 * context window), against the one measured reference templates/llama-model-settings.json.
 * checkSetup is pure. The front ends (Mode's /mellum check and activation check, scripts/mellum.mjs)
 * pass gatherInputs their own reader and GET, usually fetchJson; this module only ever GETs and never
 * writes. The fix for a mismatch is a command to show, never to run.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export type Level = "ok" | "info" | "warn" | "fail";

export interface Finding {
	id: "server" | "model" | "context";
	level: Level;
	message: string;
	fix?: string;
}

/** The measured settings the check compares against (templates/llama-model-settings.json). */
export interface Expected {
	modelId: string;
	nCtxMin: number;
}

export type Fetched<T> = { ok: true; value: T } | { ok: false; status?: number; error: string };

export type Host = "pi";

export interface CheckInputs {
	baseUrl: string;
	health: Fetched<unknown>;
	props: Fetched<unknown>;
	models: Fetched<unknown>;
}

export interface Diff {
	key: string;
	expected: unknown;
	actual: unknown;
}

export const DEFAULT_BASE_URL = "http://127.0.0.1:8001/v1";

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);

export function loadExpected(read: (p: string) => string = (p) => readFileSync(p, "utf8")): Expected {
	return JSON.parse(read(fileURLToPath(new URL("../templates/llama-model-settings.json", import.meta.url))));
}

/** The server root, `baseUrl` without a trailing `/` and `/v1`, so /health and /props hang off it. */
export const serverRootOf = (baseUrl: string) => baseUrl.replace(/\/+$/, "").replace(/\/v1$/, "");
/** Kept for callers that still import the old name; llama-server has no admin API. */
export const adminBaseOf = serverRootOf;

// ---- the check -----------------------------------------------------------------------

function modelListed(models: unknown, id: string): boolean {
	const data = isObj(models) ? models.data : undefined;
	return Array.isArray(data) && data.some((m) => isObj(m) && m.id === id);
}

/** The launched context window: llama-server reports it at /props.default_generation_settings.n_ctx. */
export function serverNCtx(props: unknown): number | undefined {
	const gen = isObj(props) ? props.default_generation_settings : undefined;
	const n = isObj(gen) ? gen.n_ctx : undefined;
	return typeof n === "number" ? n : undefined;
}

export function checkSetup(inputs: CheckInputs, expected: Expected): Finding[] {
	const out: Finding[] = [];
	const healthOk = inputs.health.ok && isObj(inputs.health.value) && (inputs.health.value as Obj).status === "ok";

	if (healthOk) {
		out.push({ id: "server", level: "ok", message: `llama-server answers at ${inputs.baseUrl}` });
	} else {
		const why = inputs.health.ok ? "it did not report status ok" : inputs.health.error;
		out.push({
			id: "server",
			level: "fail",
			message: `llama-server did not answer at ${serverRootOf(inputs.baseUrl)}/health: ${why}`,
			fix: "start it: uv run scripts/backend.py start",
		});
	}

	// With the server down, the model and context are not checked (never reported ok).
	if (healthOk) {
		const id = expected.modelId;
		if (inputs.models.ok && modelListed(inputs.models.value, id)) {
			out.push({ id: "model", level: "ok", message: `${id} is served` });
		} else {
			out.push({
				id: "model",
				level: "fail",
				message: `${id} is not served (it is not in /v1/models)`,
				fix: "start the server on the Mellum weights: uv run scripts/backend.py start",
			});
		}

		const nCtx = inputs.props.ok ? serverNCtx(inputs.props.value) : undefined;
		if (nCtx === undefined) {
			out.push({ id: "context", level: "warn", message: "could not read the context window from /props" });
		} else if (nCtx >= expected.nCtxMin) {
			out.push({ id: "context", level: "ok", message: `context window ${nCtx} (at least ${expected.nCtxMin})` });
		} else {
			out.push({
				id: "context",
				level: "fail",
				message: `context window ${nCtx} is below the measured ${expected.nCtxMin}`,
				fix: `relaunch with a ${expected.nCtxMin}-token context (uv run scripts/backend.py start reads [tool.mellum] context)`,
			});
		}
	}

	return out;
}

// ---- reading the host config for the base URL ------------------------------------------

/** The `llamacpp` provider object of Pi's config (`providers.llamacpp`). */
function providerEntry(config: unknown): Obj | undefined {
	if (!isObj(config)) return undefined;
	const providers = config.providers;
	const entry = isObj(providers) ? providers.llamacpp : undefined;
	return isObj(entry) ? entry : undefined;
}

/** JSON with `//` and `/* *\/` comments and trailing commas. Empty text gives undefined; bad text throws. */
export function parseJsonc(text: string): unknown {
	let noComments = "";
	for (let i = 0; i < text.length; i++) {
		const c = text[i];
		if (c === '"') {
			let j = i + 1;
			while (j < text.length && text[j] !== '"') j += text[j] === "\\" ? 2 : 1;
			noComments += text.slice(i, j + 1);
			i = j;
		} else if (c === "/" && text[i + 1] === "/") {
			while (i < text.length && text[i] !== "\n") i++;
			noComments += "\n";
		} else if (c === "/" && text[i + 1] === "*") {
			const end = text.indexOf("*/", i + 2);
			i = end < 0 ? text.length : end + 1;
			noComments += " ";
		} else {
			noComments += c;
		}
	}
	let out = "";
	for (let i = 0; i < noComments.length; i++) {
		const c = noComments[i];
		if (c === '"') {
			let j = i + 1;
			while (j < noComments.length && noComments[j] !== '"') j += noComments[j] === "\\" ? 2 : 1;
			out += noComments.slice(i, j + 1);
			i = j;
		} else if (c === ",") {
			let j = i + 1;
			while (j < noComments.length && /\s/.test(noComments[j])) j++;
			if (noComments[j] !== "}" && noComments[j] !== "]") out += c;
		} else {
			out += c;
		}
	}
	return out.trim() === "" ? undefined : JSON.parse(out);
}

/** The base URL to probe: the host's llamacpp provider baseUrl, else the default. */
export function readProvider(host: Host, home: string, read: (p: string) => string | undefined): { baseUrl: string; error?: string } {
	let text: string | undefined;
	const path = join(home, ".pi/agent/models.json");
	try {
		text = read(path);
	} catch {
		text = undefined;
	}
	if (text === undefined) return { baseUrl: DEFAULT_BASE_URL };
	let config: unknown;
	try {
		config = parseJsonc(text);
	} catch {
		return { baseUrl: DEFAULT_BASE_URL };
	}
	const entry = providerEntry(config);
	const base = entry?.baseUrl;
	return { baseUrl: typeof base === "string" && base ? base : DEFAULT_BASE_URL };
}

// ---- fetching -------------------------------------------------------------------------

/**
 * GET `url` and parse JSON. Never throws. Races its own timer as well as passing an abort
 * signal, so a fetch that ignores the signal still gives `{ ok: false, error: "timeout" }`.
 */
export async function fetchJson(url: string, opts: { timeoutMs: number; fetch?: typeof fetch }): Promise<Fetched<unknown>> {
	const get = opts.fetch ?? globalThis.fetch;
	let timer: ReturnType<typeof setTimeout> | undefined;
	const timedOut = new Promise<Fetched<unknown>>((done) => {
		timer = setTimeout(() => done({ ok: false, error: "timeout" }), opts.timeoutMs);
	});
	const attempt = (async (): Promise<Fetched<unknown>> => {
		try {
			const res = await get(url, { method: "GET", signal: AbortSignal.timeout(opts.timeoutMs) });
			if (!res.ok) return { ok: false, status: res.status, error: `HTTP ${res.status}` };
			return { ok: true, value: await res.json() };
		} catch (e) {
			const err = e as { name?: string; message?: string; cause?: { code?: string } };
			if (err?.name === "TimeoutError" || err?.name === "AbortError") return { ok: false, error: "timeout" };
			return { ok: false, error: err?.cause?.code ?? err?.message ?? String(e) };
		}
	})();
	try {
		return await Promise.race([attempt, timedOut]);
	} finally {
		clearTimeout(timer);
	}
}

/** The activation probe: is the server up, and at what context window. `up` null when unreachable. */
export interface ServerCheck {
	up: boolean | null;
	nCtx?: number;
}

/** One /health GET (and /props for the context window); never throws, unreachable gives up null. */
export async function serverCheck(serverRoot: string, opts: { timeoutMs: number; fetch?: typeof fetch }): Promise<ServerCheck> {
	try {
		const health = await fetchJson(`${serverRoot}/health`, opts);
		if (!health.ok) return { up: null };
		const up = isObj(health.value) && (health.value as Obj).status === "ok";
		const props = await fetchJson(`${serverRoot}/props`, opts);
		const nCtx = props.ok ? serverNCtx(props.value) : undefined;
		return nCtx === undefined ? { up } : { up, nCtx };
	} catch {
		return { up: null };
	}
}

/** Everything checkSetup needs: the host config via `read` (for the base URL), the GETs via `get`. */
export async function gatherInputs(
	host: Host,
	io: { home: string; read: (p: string) => string | undefined; get: (url: string) => Promise<Fetched<unknown>> },
): Promise<CheckInputs> {
	const { baseUrl } = readProvider(host, io.home, io.read);
	const root = serverRootOf(baseUrl);
	const [health, props, models] = await Promise.all([
		io.get(`${root}/health`),
		io.get(`${root}/props`),
		io.get(`${baseUrl.replace(/\/+$/, "")}/models`),
	]);
	return { baseUrl, health, props, models };
}

// ---- output ----------------------------------------------------------------------------

export function formatFindings(findings: Finding[]): string {
	const rank: Level[] = ["fail", "warn", "info"];
	const out: string[] = [];
	for (const level of rank) {
		for (const f of findings.filter((x) => x.level === level)) {
			const [first, ...rest] = f.message.split("\n");
			out.push(`${level.toUpperCase()} ${f.id}: ${first}`, ...rest);
			if (f.fix) out.push(`  fix: ${f.fix}`);
		}
	}
	const oks = findings.filter((x) => x.level === "ok").length;
	if (oks > 0) out.push(`${oks} checks ok`);
	return out.join("\n");
}
