/**
 * Mellum from the terminal, for Pi:
 *
 *   node scripts/mellum.mjs check [--host pi] [--json]
 *   node scripts/mellum.mjs learn [--n 10] [--file <jsonl>] [--json]
 *   node scripts/mellum.mjs last [--file <jsonl>] [--json]
 *
 * check confirms the local llama-server is up and serving the measured model at the measured
 * context window (GETs only), and that the host's provider entry points at it; it prints the
 * findings (fails first) or JSON, and exits 1 on any fail. It only reads: a fix is printed as
 * the command to run yourself.
 *
 * learn names what went wrong in the last n runs (default 10) under the current directory,
 * from $MELLUM_MODE_RUNS (or ~/.pi/agent/mellum-mode-runs.jsonl) and
 * ~/.pi/agent/mellum-worker-runs.jsonl, or only --file. It prints the suggested ## Mellum
 * lines that ./AGENTS.md lacks and any conflict with it, and never writes: /mellum learn in
 * Pi does that.
 *
 * last prints the newest run under the current directory (Mode or Worker, same files as learn,
 * or only --file) as a Markdown table, or the record as JSON; exit 1 when there is none.
 *
 * MELLUM_CHECK_FIXTURES=<dir> (tests) reads <dir>/health.json, props.json and
 * v1-models.json in place of the three GETs.
 */
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, renameSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PKG = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const USAGE = "usage: node scripts/mellum.mjs check [--host pi] [--json]\n       node scripts/mellum.mjs learn [--n 10] [--file <jsonl>] [--json]\n       node scripts/mellum.mjs last [--file <jsonl>] [--json]";

/**
 * Node refuses to strip types from .ts files under node_modules, where a git install puts this
 * package. There, copy the extensions and the templates they read to a mirror in the temp dir
 * (same layout) and import from that. Each file is written whole, then renamed into place.
 */
function codeRoot() {
	if (!PKG.split(sep).includes("node_modules")) return PKG;
	const version = JSON.parse(readFileSync(join(PKG, "package.json"), "utf8")).version;
	const mirror = join(tmpdir(), `mellum-worker-${version}`);
	const files = [
		"package.json",
		"templates/llama-model-settings.json",
		...readdirSync(join(PKG, "extensions"))
			.filter((f) => f.endsWith(".ts"))
			.map((f) => `extensions/${f}`),
	];
	for (const f of files) {
		const to = join(mirror, f);
		mkdirSync(dirname(to), { recursive: true });
		const partial = `${to}.${process.pid}.tmp`;
		copyFileSync(join(PKG, f), partial);
		renameSync(partial, to);
	}
	return mirror;
}

function fail(msg) {
	console.error(`${msg}\n${USAGE}`);
	process.exit(2);
}

function parseArgs(argv) {
	const [cmd, ...rest] = argv;
	const opts = { cmd, host: "pi", json: false, n: 10, file: undefined };
	for (let i = 0; i < rest.length; i++) {
		if (rest[i] === "--json") opts.json = true;
		else if (rest[i] === "--host" && cmd === "check") opts.host = rest[++i];
		else if (rest[i] === "--n" && cmd === "learn") opts.n = /^\d+$/.test(rest[++i] ?? "") ? Number(rest[i]) : 0;
		else if (rest[i] === "--file" && (cmd === "learn" || cmd === "last")) {
			opts.file = rest[++i];
			if (opts.file === undefined || opts.file.startsWith("--")) fail("--file needs a path");
		}
		else fail(`unknown argument: ${rest[i]}`);
	}
	if (opts.host !== "pi") fail(`unknown host: ${opts.host}`);
	if (!(opts.n >= 1)) fail("--n must be a whole number above 0");
	if ((cmd === "learn" || cmd === "last") && opts.file !== undefined && !existsSync(opts.file)) fail(`no such file: ${opts.file}`);
	return opts;
}

async function check(opts) {
	const m = await import(pathToFileURL(join(codeRoot(), "extensions/mellum-check.ts")).href);
	const fixtures = process.env.MELLUM_CHECK_FIXTURES;
	const fromFixture = async (url) => {
		const name = url.endsWith("/health") ? "health.json" : url.endsWith("/props") ? "props.json" : "v1-models.json";
		try {
			return { ok: true, value: JSON.parse(readFileSync(join(fixtures, name), "utf8")) };
		} catch (e) {
			return { ok: false, error: e.code ?? e.message };
		}
	};
	const inputs = await m.gatherInputs(opts.host, {
		home: process.env.HOME || homedir(),
		read: (p) => (existsSync(p) ? readFileSync(p, "utf8") : undefined),
		get: fixtures ? fromFixture : (url) => m.fetchJson(url, { timeoutMs: 3000 }),
	});
	const findings = m.checkSetup(inputs, m.loadExpected());
	console.log(opts.json ? JSON.stringify({ host: opts.host, baseUrl: inputs.baseUrl, findings }, null, 2) : m.formatFindings(findings));
	if (findings.some((f) => f.level === "fail")) process.exitCode = 1;
}

async function learn(opts) {
	const m = await import(pathToFileURL(join(codeRoot(), "extensions/mellum-learn.ts")).href);
	const cwd = process.cwd();
	const read = (p) => (existsSync(p) ? readFileSync(p, "utf8") : undefined);
	const files = opts.file !== undefined ? [opts.file] : m.recordFiles(process.env, process.env.HOME || homedir());
	const report = m.learnFromTexts(files.map(read), { cwd, n: opts.n });
	const merged = m.mergeSuggestion(read(join(cwd, "AGENTS.md")), report.suggestion);
	// The suggestion shown (text and JSON) is only what the merge with ./AGENTS.md would add.
	const out = { cwd, ...report, suggestion: merged.added, added: merged.added, conflicts: merged.conflicts, chars: merged.chars };
	console.log(opts.json ? JSON.stringify(out, null, 2) : m.formatReport(report, cwd, merged.added) + m.formatMerge(merged, report.suggestion));
}

async function last(opts) {
	const learnMod = await import(pathToFileURL(join(codeRoot(), "extensions/mellum-learn.ts")).href);
	const m = await import(pathToFileURL(join(codeRoot(), "extensions/mellum-last.ts")).href);
	const cwd = process.cwd();
	const files = opts.file !== undefined ? [opts.file] : learnMod.recordFiles(process.env, process.env.HOME || homedir());
	const none = (why) => {
		console.error(`mellum last: ${why}`);
		process.exitCode = 1;
	};
	if (files.length === 0) return none("run records are off (MELLUM_MODE_RUNS=0)");
	const { record } = m.pickLast(files.map((p) => (existsSync(p) ? readFileSync(p, "utf8") : undefined)), cwd);
	if (!record) return none(`no Mellum runs recorded under ${cwd} (read ${files.join(", ")})`);
	console.log(opts.json ? JSON.stringify(record, null, 2) : m.formatLast(record));
}

const opts = parseArgs(process.argv.slice(2));
if (opts.cmd === "check") await check(opts);
else if (opts.cmd === "learn") await learn(opts);
else if (opts.cmd === "last") await last(opts);
else fail(opts.cmd ? `unknown command: ${opts.cmd}` : "no command");
