/**
 * mellum-knowledge: a `lookup` tool grounded in the INSTALLED venv packages.
 *
 * The model fails exact-API contracts it cannot know — FastAPI's `RedirectResponse` default
 * (307, so a POST redirect loops; the spec needs 303), a migration API — and, decisively,
 * anything past its training cutoff (the ladder runs on Python 3.15, which the model was never
 * trained on). The truth is in the venv that is running, so `docs_lookup.py` builds a BM25 index
 * over that venv's package source (every class/function with its signature and docstring) and
 * answers a query with the top matches. This extension exposes that as a tool the model can call
 * whenever it is unsure of an API or hits an API-shaped failure.
 *
 * It grounds on library docs a developer would have, never the task solution or the hidden grader.
 * The index is built on the initial call (and warmed on session start) and cached, so a later call
 * — whenever the model makes it — returns fast.
 */

import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = join(HERE, "..", "learn", "code", "docs_lookup.py");

/** Run the BM25 lookup over the workspace venv (cwd); it builds+caches the index on first use. */
function runLookup(query: string, k: number, cwd: string, rebuild = false): Promise<string> {
	const args = [DOCS, "--k", String(k), ...(rebuild ? ["--rebuild"] : []), query];
	return new Promise((resolve) => {
		const child = spawn("python3", args, { cwd, env: process.env, stdio: ["ignore", "pipe", "pipe"] });
		let out = "";
		child.stdout.on("data", (c: Buffer) => (out += c.toString()));
		child.stderr.on("data", () => {}); // drain (an unread pipe would deadlock the child)
		child.on("close", () => resolve(out.trim() || "(no matches in the installed packages)"));
		child.on("error", (e) => resolve(`(lookup unavailable: ${e.message})`));
	});
}

export default function (pi: any): void {
	// Warm the index on session start so the first real call is fast (index on initial run).
	// Best-effort: if the venv is not created yet, this no-ops and the first lookup builds it.
	pi.on("session_start", () => {
		const child = spawn("python3", [DOCS, "--k", "1", "warmup"], {
			cwd: process.cwd(), env: process.env, stdio: ["ignore", "ignore", "ignore"],
		});
		child.on("error", () => {});
	});

	pi.registerTool({
		name: "lookup",
		label: "Docs lookup",
		description:
			"Look up a library API in the INSTALLED packages (BM25 over the venv source): exact " +
			"signatures, DEFAULT values, and behavior for the exact versions running — including ones " +
			"newer than your training. Use it BEFORE guessing an unfamiliar API, and whenever a failure " +
			"looks API-shaped (e.g. `TooManyRedirects` -> look up the redirect status default). Returns " +
			"the top matching class/function source and docstring. The index auto-rebuilds when the " +
			"installed packages change; after you install a NEW package, pass `rebuild: true` to index " +
			"it right away.",
		parameters: {
			type: "object",
			properties: {
				query: { type: "string", description: "the API/library question, e.g. 'RedirectResponse status code default 303'" },
				k: { type: "number", description: "how many results to return (default 4)" },
				rebuild: { type: "boolean", description: "force a re-index first (use after installing a new package)" },
			},
			required: ["query"],
			additionalProperties: false,
		},
		async execute(_id: string, params: any) {
			const k = Number(params?.k) > 0 ? Math.min(Number(params.k), 8) : 4;
			const text = await runLookup(String(params?.query ?? ""), k, process.cwd(), params?.rebuild === true);
			return { content: [{ type: "text", text }] };
		},
	});
}
