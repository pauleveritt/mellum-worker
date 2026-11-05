/**
 * Mellum mode: run the small model inside the main session with the worker's prompt
 * and tools, and show it nothing from before the mode began.
 *
 *   /mellum <task>  – (in the primary) the full delegation loop: an architect pass writes the
 *                     handover — a failing acceptance test + a brief — then the bare worker runs
 *                     it to pass, and the frozen acceptance test is the verdict. In a spawned
 *                     worker child (MELLUM_WORKER_CHILD=1) it is instead the in-session one shot:
 *                     switch to Mellum, run the task, switch back when settled.
 *   /mellum on      – stay on for several turns (switch model, tools, mark the start)
 *   /mellum off     – restore the previous model and tools
 *   /mellum check   – compare the oMLX server and the Pi provider entry with the measured
 *                     settings and print the findings; never switches, never writes
 *   /mellum learn [n] – name what went wrong in the last n runs (default 10) in this directory
 *                     and suggest a ## Mellum section; AGENTS.md is written only on a yes
 *   /mellum last    – the newest run in this directory (Mode or Worker) as a Markdown table;
 *                     a notification while Mode is on, so the table stays out of Mellum's context
 *
 * Each activation GETs the server's model settings (1 s at most) and warns once when they
 * differ from the measured profile; the run record keeps the result as `server`.
 *
 * While on, before_provider_request keeps only the messages after the on-marker (minus
 * Superpowers' bootstrap message) — the pre-marker history drop, so Mellum never sees the
 * parent's earlier turns. It swaps nothing else: not the system prompt, not the tool list.
 * Earlier turns' reasoning_content is left in place: removing it made runs 60% slower
 * (ladder A12). The session keeps everything.
 *
 * This is the thin worker: mode machinery and the /mellum commands only — it bundles NOTHING
 * into the worker's own span. The prompt, tool-narrowing, project facts, the loop breaker and
 * empty-turn nudge and the rest, and the handoff collapse, are all remedy units under remedies/
 * now, combined through a preset; the worker adds none of them itself. It keeps only the
 * pre-marker history drop, which protects the mode's own on-marker (mode-integrity, not remediation).
 *
 * It also registers one PRIMARY-side tool, `delegate`: load this extension and the primary model
 * can hand a bounded, generic implementation brief to a fresh local worker (this same file,
 * spawned headless with `/mellum <brief>`) without the human typing /mellum. The primary explores
 * and decides; the worker implements. The tool and its nudge are present only in the primary — a
 * spawned child sets MELLUM_WORKER_CHILD=1 and gets neither, so the worker cannot delegate again.
 *
 * Headless: MELLUM_MODE=1 activates at session start (the ladder's "mode" runner).
 * Installed as a Pi package extension it loads in every parent session and stays dormant until /mellum.
 */
import { spawn } from "node:child_process";
import { appendFileSync, chmodSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, isAbsolute, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { adminBaseOf, checkSetup, fetchJson, formatFindings, gatherInputs, loadExpected, readProvider, serverCheck, type ServerCheck } from "./mellum-check.ts";
import { type ProjectFacts } from "./mellum-facts.ts";
import { type Activation, type Msg, runRecord, textOf, spanStats, type SpanStats } from "./mellum-record.ts";
import { formatMerge, formatReport, learnFromTexts, mergeSuggestion, modeRunsFile, overCap, recordFiles } from "./mellum-learn.ts";
import { formatLast, pickLast } from "./mellum-last.ts";

export const MARK_ON = "[mellum-worker on]";
export const MARK_OFF = "[mellum-worker off]";
export const BOOTSTRAP_MARKER = "superpowers:using-superpowers bootstrap for pi";
export const WORKER_TOOLS = ["read", "grep", "find", "ls", "bash", "edit", "write"];
const DEFAULT_MODEL = { provider: "llamacpp", id: "Mellum2.1-12B-A2.5B-Thinking" };

// Set in the environment of a worker this extension spawns for `delegate`, so the spawned
// child does not offer `delegate` itself (no recursion) and does not append the primary nudge.
const CHILD_ENV = "MELLUM_WORKER_CHILD";
// This file, re-loaded by the spawned worker with `-e <self> /mellum <brief>`.
const SELF = fileURLToPath(import.meta.url);
// The remedy units live beside the extensions, as remedies/<kind>/<name>.ts and presets/<name>.json.
const REMEDIES_DIR = resolve(dirname(SELF), "..", "remedies");

/**
 * Resolve a remedy spec — a comma list of unit names (`prompt/python-developer`) and/or
 * `preset:<name>` references — to the unit files to load, in order. A preset is the JSON name
 * list under remedies/presets/. Unknown names are skipped (best-effort), so a spawned worker
 * never fails to start over a typo; a run script names a known preset. This mirrors the harness's
 * resolve_extras: a remedy unit is a .ts file loaded with `-e`, nothing more.
 */
export function resolveRemedyFiles(spec: string | undefined, dir = REMEDIES_DIR): string[] {
	const names: string[] = [];
	for (const item of (spec ?? "").split(",").map((s) => s.trim()).filter(Boolean)) {
		if (item.startsWith("preset:")) {
			try { names.push(...JSON.parse(readFileSync(resolve(dir, "presets", `${item.slice("preset:".length)}.json`), "utf8"))); } catch {}
		} else {
			names.push(item);
		}
	}
	const files: string[] = [];
	for (const name of names) {
		const p = resolve(dir, `${name}.ts`);
		if (existsSync(p)) files.push(p);
	}
	return files;
}

/** The `-e <file>` arguments for the code-eval remedies applied to a spawned delegation worker,
 * from MELLUM_DELEGATE_REMEDY (e.g. `preset:medium`). Empty when unset — the bare, measured
 * default — so remedies are added explicitly for a code-eval run, never on by surprise. */
export function remedyArgs(spec = process.env.MELLUM_DELEGATE_REMEDY): string[] {
	return resolveRemedyFiles(spec).flatMap((p) => ["-e", p]);
}

// Just the guard units from a remedy spec. Guards are role-agnostic safety bounds — a turn
// cap, a loop breaker, no foreground servers, no writing outside the workspace — so EVERY
// spawned sub-agent loads them, the architect passes included (without them an architect or
// worker can thrash a debug loop for a hundred-plus turns). The implementer PROMPT fragments
// are deliberately NOT given to the architect: they frame the model as a developer who writes
// and runs code, which fights the architect's one rule — plan, never code.
export function guardArgs(spec = process.env.MELLUM_DELEGATE_REMEDY): string[] {
	// turn-cap is worker-tuned — a low per-step budget (MELLUM_TURN_CAP) that would cut the
	// architect off before it finishes writing a many-step plan — so the architect gets every
	// other guard but not that one.
	return resolveRemedyFiles(spec)
		.filter((p) => /\/guard\//.test(p) && !/\/guard\/turn-cap\.ts$/.test(p))
		.flatMap((p) => ["-e", p]);
}

// The primary nudge, appended to each user message so the model delegates the implementation
// instead of writing it. Agnostic: it names no suite, file or command — the brief is the primary's.
const DELEGATE_NUDGE =
	"You are the primary. Explore, decide the layout, and pin the goal with a check or a failing " +
	"test yourself — but hand the implementation to the `delegate` tool, do not write it. The brief " +
	"must stand on its own: what to build, which files, and the exact command that proves it done. " +
	"Then read the worker's report and verify by running that command; delegate a fix if it is not done yet.";

/** A copy of `payload` with the delegate nudge appended to every user message. Never mutates. */
export function withDelegateNudge(payload: any): any {
	if (!payload || !Array.isArray(payload.messages)) return payload;
	const add = (c: any): any =>
		typeof c === "string"
			? `${c}\n\n${DELEGATE_NUDGE}`
			: Array.isArray(c)
				? [...c, { type: "text", text: `\n\n${DELEGATE_NUDGE}` }]
				: c;
	return { ...payload, messages: payload.messages.map((m: any) => (m.role === "user" ? { ...m, content: add(m.content) } : m)) };
}

/**
 * The `delegate` tool: the primary hands ONE bounded, generic implementation task to a fresh
 * local worker — this same extension, spawned headless with `/mellum <brief>`. The worker edits
 * files in this project, runs the tests, and returns its report. It is absent from a spawned
 * child (CHILD_ENV), so the worker cannot delegate to itself.
 */
export function registerDelegate(pi: any, run: typeof spawnWorker = spawnWorker): void {
	pi.registerTool({
		name: "delegate",
		label: "Delegate to the worker",
		description:
			"Hand ONE bounded, test-driven implementation task to the local coding worker. It edits " +
			"files in THIS project, runs the tests, and returns a report. Use it for implementation " +
			"grunt-work AFTER you have decided the layout and pinned the goal with a check or failing " +
			"test: the brief must name what to build, which files, and the exact command to make pass. " +
			"Do NOT use it for exploration, design, or deciding the layout — that is your job as the " +
			"primary. One narrow task per call; read the report, verify, and delegate the next piece or a fix.",
		parameters: {
			type: "object",
			properties: {
				brief: {
					type: "string",
					description: "the narrow implementation task: what to build, which files, and the command to make pass",
				},
			},
			required: ["brief"],
			additionalProperties: false,
		},
		async execute(_id: string, params: any) {
			const brief = String(params?.brief ?? "").trim();
			if (!brief) return { content: [{ type: "text", text: "delegate: the brief was empty" }] };
			return { content: [{ type: "text", text: await run(brief) }] };
		},
	});
}

// The frozen oracle the author writes and the worker must make pass. One fixed path and command
// so the orchestration can author it, freeze it, and run it without guessing — agnostic to the task.
export const ACCEPTANCE_TEST = "tests/test_acceptance.py";
export const ACCEPTANCE_CMD = "uv run --with pytest python -m pytest tests/test_acceptance.py -q";

/** Keep the authored test valid Python: the model's recurring bug is nested double-quotes. */
export const QUOTING_RULE =
	"Write valid Python: when a string literal you assert contains a double-quote (for example an " +
	`HTML attribute like class="card" or charset="UTF-8"), make that Python string SINGLE-quoted ` +
	`('...') so the inner double-quotes need no escaping. Never nest unescaped double-quotes inside a ` +
	"double-quoted string — that is a syntax error.";

/** The architect prompt: write the handover (a COMPLETE failing acceptance test + a brief), never the code. */
export function authorPrompt(task: string): string {
	return (
		"You are the ARCHITECT, not the implementer. Do NOT write any implementation code.\n" +
		"Read the task below AND every spec or notes file already in this directory (for example a " +
		"specs/ folder and AGENTS.md). Enumerate EVERY concrete requirement the spec states — every " +
		"bullet, attribute, exact value, route, element, header and behaviour it calls for. Then write " +
		"EXACTLY two files and nothing else:\n" +
		`1. ${ACCEPTANCE_TEST} — a COMPLETE acceptance test that defines "done". Assert EVERY requirement ` +
		"you enumerated, each as its own explicit check, so the test cannot pass while any stated " +
		"requirement is missing or wrong. Be exhaustive, not representative — do NOT settle for one or two " +
		"smoke checks (a 200 and a bit of text is not enough). It must FAIL now, because the implementation " +
		"does not exist yet.\n" +
		"Pin EXACT NAMED CONTRACTS, not just behaviour. Wherever the spec names something concrete — a " +
		"module, a module-level variable or attribute, a class, a function, a collection or field name, an " +
		"exact count, or a verbatim seed string or literal — assert that named thing DIRECTLY (import the " +
		"module and check the attribute, its type, its length/count, and the exact seed values), in addition " +
		"to probing behaviour through any route or output. A behaviour that looks right through a route can " +
		"still be built on the wrong name or shape; the named contract is what a stricter grader checks, so " +
		"assert the spec's literal names, counts and strings exactly as written.\n" +
		QUOTING_RULE + "\n" +
		`2. BRIEF.md — 2 to 4 sentences: what to build, which files, and this exact command to make pass:\n` +
		`   ${ACCEPTANCE_CMD}\n` +
		"Before you stop, re-read the spec and confirm every requirement has a matching assertion; add any " +
		"you missed. Do NOT create, edit or stub any implementation file. Stop only once both files are " +
		"written and the test covers the whole spec.\n\n" +
		`Task: ${task}`
	);
}

/** Repair prompt: an authored oracle does not parse. The architect fixes ONLY the syntax, keeping
 * every assertion, so an authored-but-broken test (finding 1) can't block the whole run. */
export function repairPrompt(error: string, path: string = ACCEPTANCE_TEST): string {
	return (
		`The acceptance test ${path} you just wrote does not parse — Python reports a syntax ` +
		"error, so pytest cannot even collect it. Fix ONLY the syntax so the file compiles cleanly. Do " +
		"NOT remove, weaken or change the meaning of any assertion — keep every check exactly as it is, " +
		"just make it valid Python. A common cause is nested double-quotes inside a double-quoted string " +
		`(for example asserting a literal that itself contains "): fix it by making the OUTER string a ` +
		"single-quoted Python string, so the inner double-quotes need no escaping — do NOT turn the " +
		"checked value into a string that is always true. Use the WRITE tool to replace the ENTIRE file " +
		"with one corrected version in a single write; do NOT make piecemeal edits (they are slow and " +
		"error-prone here). Then stop.\n\n" +
		`Syntax error:\n${error}`
	);
}

// ── Per-phase delegation (MELLUM_DELEGATE_PHASED=1) ─────────────────────────────
// The throughput wall on a multi-phase spec is one worker invocation spending a finite
// turn budget on edit churn. Per-phase gives each phase its OWN fresh worker (fresh budget)
// against a smaller, cumulative-safe oracle, and git-checkpoints a passing phase so a later
// phase cannot silently break an earlier one. The architect derives the phases from the
// spec (it names no suite phase), so this stays agnostic.

/** Phase test files the architect writes, ordered: tests/test_phase1_*.py, test_phase2_*.py, … */
export const PHASE_TEST_DIR = "tests";
export const PHASE_TEST_RE = /^test_phase(\d+)[_.].*\.py$/;
/** One fresh-budget retry per phase before it is declared failed. */
export const MAX_PHASE_RETRIES = 1;

/** The phased architect prompt: decompose the spec into ordered phases and write one cumulative,
 * complete acceptance test per phase, each pinning exact named contracts. Never the code. */
export function authorPhasesPrompt(task: string): string {
	return (
		"You are the ARCHITECT, not the implementer. Do NOT write any implementation code.\n" +
		"Read the task below AND every spec or notes file already in this directory (a specs/ folder, " +
		"AGENTS.md, a roadmap). The spec is built in MILESTONES that build on each other. Break it into " +
		"ORDERED PHASES (phase 1 is the first working slice; each later phase adds the next milestone). " +
		"For each phase N, write ONE test file:\n" +
		`  ${PHASE_TEST_DIR}/test_phaseN_<slug>.py  (N starts at 1, contiguous — 1, 2, 3, …)\n` +
		"Each phase file is a COMPLETE acceptance test for THAT phase's requirements — assert every " +
		"requirement the phase adds, each as its own explicit check — and it must stay green once later " +
		"phases are built (test only what exists by the end of its own phase, never a later phase). It " +
		"must FAIL now, before any implementation.\n" +
		"Pin EXACT NAMED CONTRACTS, not just behaviour. Wherever the spec names something concrete — a " +
		"module, a module-level variable or attribute, a class, a function, a collection or field name, an " +
		"exact count, or a verbatim seed string or literal — assert that named thing DIRECTLY (import the " +
		"module and check the attribute, its type, its length/count, and the exact seed values), as well as " +
		"probing behaviour through any route or output.\n" +
		QUOTING_RULE + "\n" +
		"Then write BRIEF.md — 2 to 4 sentences on what to build overall and which files. Write ONLY the " +
		"phase test files and BRIEF.md, nothing else; do NOT create, edit or stub any implementation file. " +
		"Before you stop, confirm the phases are contiguous from 1 and together cover the whole spec.\n\n" +
		`Task: ${task}`
	);
}

/** What the worker is told: make the frozen acceptance test pass, without touching it. */
export const WORKER_BRIEF =
	`Read BRIEF.md and ${ACCEPTANCE_TEST} in this directory, then implement the solution until the ` +
	`command \`${ACCEPTANCE_CMD}\` passes. Do NOT edit ${ACCEPTANCE_TEST} — it is the frozen oracle. ` +
	"Work only inside this directory — do NOT read, search for, or copy files outside it. " +
	"Run the command yourself until every test passes, then stop.";

/** Verbose when MELLUM_DELEGATE_VERBOSE=1: each stage is labelled and its child output streamed. */
const verbose = () => process.env.MELLUM_DELEGATE_VERBOSE === "1";

/** When verbose, stream one assistant turn — a thinking snippet, its tool calls, any reply text —
 * to stdout, so a spawned architect/worker child shows its work live through the parent's tee. */
export function streamTurn(message: any): void {
	if (!verbose() || !message || message.role !== "assistant") return;
	const one = (s: any) => String(s ?? "").replace(/\s+/g, " ").trim();
	const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n) + "…" : s);
	let printed = false;
	const line = (s: string) => { process.stdout.write(s + "\n"); printed = true; };
	// Thinking carried on the message itself (string form).
	const think = one(message.reasoning_content ?? message.reasoning);
	if (think) line(`  💭 ${clip(think, 220)}`);
	// Pi carries tool calls, text and thinking as CONTENT BLOCKS on the assistant message
	// ({type:"toolCall", name, arguments}, {type:"text", text}, {type:"thinking"/"reasoning"}).
	const blocks: any[] = Array.isArray(message.content) ? message.content : [];
	for (const b of blocks) {
		if (!b || typeof b !== "object") continue;
		const type = String(b.type ?? "").toLowerCase();
		if (type.includes("toolcall")) {
			const name = b.name ?? b.function?.name ?? "tool";
			const a = b.arguments ?? b.input ?? {};
			const detail = a?.path ?? a?.command ?? (typeof a === "string" ? a : Object.values(a ?? {})[0] ?? "");
			line(`  → ${name} ${clip(one(detail), 100)}`);
		} else if (type.includes("think") || type.includes("reason")) {
			const t = one(b.text ?? b.thinking ?? b.content);
			if (t) line(`  💭 ${clip(t, 220)}`);
		} else if (type === "text" && typeof b.text === "string") {
			const t = one(b.text);
			if (t) line(`  ${clip(t, 240)}`);
		}
	}
	if (!blocks.length && typeof message.content === "string") {
		const t = one(message.content);
		if (t) line(`  ${clip(t, 240)}`);
	}
	if (!printed) line("  · (turn)");
}

/** Spawn `pi` headless as a worker child (no nested delegation).
 * Default: capture the child's output (piped) and return its trimmed tail.
 * Verbose: the child INHERITS this process's stdout/stderr (the terminal), so its per-turn
 * streaming flushes live instead of block-buffering behind a pipe; the report then comes from
 * the run records and the acceptance test, not captured text. */
function runPi(argv: string[], label = ""): Promise<string> {
	return new Promise((resolve) => {
		const v = verbose();
		if (v && label) process.stdout.write(`\n━━━ ${label} ━━━\n`);
		let child;
		try {
			child = spawn("pi", argv, {
				cwd: process.cwd(),
				env: { ...process.env, [CHILD_ENV]: "1" },
				stdio: v ? ["ignore", "inherit", "inherit"] : ["ignore", "pipe", "pipe"],
			});
		} catch (e) {
			return resolve(`could not start pi — ${(e as Error).message}`);
		}
		let out = "";
		if (!v) {
			child.stdout?.on("data", (b) => { out += b.toString(); });
			child.stderr?.on("data", (b) => { out += b.toString(); });
		}
		child.on("error", (e) => resolve(`could not start pi — ${e.message}`));
		child.on("close", () => resolve(v ? "(streamed live to the terminal above)" : (out.trim().slice(-4000) || "(pi finished but produced no output)")));
	});
}

/** The architect pass: this extension headless running `/mellum <architect prompt>`, so its span is
 * recorded (turns, wall) like the worker's. It still only writes the handover, never the code. */
export function spawnAuthor(task: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...guardArgs(), "-e", SELF, `/mellum ${authorPrompt(task)}`], "architect: writing the handover (failing test + brief)");
}

/** The worker pass: this extension headless, running `/mellum <brief>` to implement to green.
 * Any code-eval remedies named in MELLUM_DELEGATE_REMEDY load first (so their prompt fragments and
 * guards are installed before the worker extension), then this extension, then the brief. */
export function spawnWorker(brief: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...remedyArgs(), "-e", SELF, `/mellum ${brief}`], "worker: implementing to pass");
}

/** The repair pass: the architect fixes the syntax of the oracle it just wrote. */
export function spawnRepair(error: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...guardArgs(), "-e", SELF, `/mellum ${repairPrompt(error)}`], "architect: repairing the oracle's syntax");
}

/** The phased architect pass: decompose the spec and write one cumulative test per phase. */
export function spawnAuthorPhases(task: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...guardArgs(), "-e", SELF, `/mellum ${authorPhasesPrompt(task)}`], "architect: decomposing the spec into phases");
}

/** Check that a Python file parses. Resolves undefined when it compiles, else the syntax error.
 * A pure syntax check needs only a parser, so bare python3 is fine here (the uv rule is for
 * reproducible measured runs, not a lint) and it works for a generic task with no uv project. */
export function compileTest(path: string): Promise<string | undefined> {
	return new Promise((resolve) => {
		let out = "";
		let child;
		try {
			child = spawn("python3", ["-m", "py_compile", path], { cwd: process.cwd(), env: process.env, stdio: ["ignore", "pipe", "pipe"] });
		} catch (e) {
			return resolve(undefined); // no python3 to check with — don't block the loop
		}
		child.stdout?.on("data", (b) => { out += b.toString(); });
		child.stderr?.on("data", (b) => { out += b.toString(); });
		child.on("error", () => resolve(undefined));
		child.on("close", (code) => resolve(code === 0 ? undefined : (out.trim().slice(-1500) || "py_compile failed")));
	});
}

/** Run a shell command in the cwd; resolve whether it exited 0 and its trimmed output. */
export function runAcceptance(cmd: string): Promise<{ passed: boolean; output: string }> {
	return new Promise((resolve) => {
		let out = "";
		let child;
		try {
			child = spawn("bash", ["-lc", cmd], { cwd: process.cwd(), env: process.env, stdio: ["ignore", "pipe", "pipe"] });
		} catch (e) {
			return resolve({ passed: false, output: `could not run the acceptance test — ${(e as Error).message}` });
		}
		child.stdout?.on("data", (b) => { out += b.toString(); });
		child.stderr?.on("data", (b) => { out += b.toString(); });
		child.on("error", (e) => resolve({ passed: false, output: `could not run the acceptance test — ${e.message}` }));
		child.on("close", (code) => resolve({ passed: code === 0, output: out.trim() }));
	});
}

export interface DoTaskDeps {
	author?: (task: string) => Promise<string>;
	worker?: (brief: string) => Promise<string>;
	acceptance?: (cmd: string) => Promise<{ passed: boolean; output: string }>;
	compile?: (path: string) => Promise<string | undefined>;
	repair?: (error: string) => Promise<string>;
}

/** How many times the architect is asked to repair an oracle that does not parse before giving up. */
export const MAX_ORACLE_REPAIRS = 2;

/** The newest worker/architect run record for `cwd` (turns = requests, wall seconds, and an id to
 * tell two spans apart), read from the mode-runs file. Best-effort: undefined if none was written. */
function latestRunStats(cwd: string): { turns: number; wall?: number; id: string } | undefined {
	try {
		const file = modeRunsFile(process.env, process.env.HOME || homedir());
		if (!file || !existsSync(file)) return undefined;
		const lines = readFileSync(file, "utf8").trim().split("\n");
		for (let i = lines.length - 1; i >= 0; i--) {
			let r: any;
			try { r = JSON.parse(lines[i]); } catch { continue; }
			if (r?.cwd && resolve(r.cwd) === resolve(cwd)) {
				const wall = r.wallSeconds ?? (r.endedAt && r.startedAt ? Math.round((r.endedAt - r.startedAt) / 1000) : undefined);
				return { turns: r.requests, wall, id: String(r.startedAt ?? r.endedAt ?? i) };
			}
		}
	} catch {}
	return undefined;
}

/**
 * The delegation loop for a whole task: the architect writes the handover (a failing acceptance
 * test + a brief), the oracle is frozen read-only so the worker cannot weaken it, the bare worker
 * implements to pass, and the acceptance test is the verdict. This is `/mellum <task>` for a
 * primary — it ADDS the handover-writing the bare `delegate` tool leaves to the caller.
 */
export async function doTask(task: string, deps: DoTaskDeps = {}): Promise<string> {
	const author = deps.author ?? spawnAuthor;
	const worker = deps.worker ?? spawnWorker;
	const acceptance = deps.acceptance ?? runAcceptance;
	const compile = deps.compile ?? compileTest;
	const repair = deps.repair ?? spawnRepair;
	const cwd = process.cwd();
	const testPath = resolve(cwd, ACCEPTANCE_TEST);
	const secs = (from: number) => Math.round((Date.now() - from) / 1000);

	const t0 = Date.now();
	let authorReport = await author(task);
	if (!existsSync(testPath)) {
		const authorWall = secs(t0);
		return `delegate: the architect did not write ${ACCEPTANCE_TEST}, so there is no handover to run.\n\n--- architect output (tail) ---\n${authorReport.slice(-1500)}`;
	}
	// A handover whose test does not even parse blocks the whole run (the worker can't make a
	// non-compiling, frozen test pass). Validate it and re-dispatch to the architect to fix the
	// SYNTAX — keeping every assertion — before freezing. Agnostic: it names no suite value.
	let compileErr = await compile(testPath);
	for (let i = 0; compileErr && i < MAX_ORACLE_REPAIRS; i++) {
		if (verbose()) process.stdout.write(`\n[handover] the authored ${ACCEPTANCE_TEST} does not parse — asking the architect to fix the syntax (attempt ${i + 1}/${MAX_ORACLE_REPAIRS}):\n${compileErr}\n`);
		authorReport = await repair(compileErr);
		if (!existsSync(testPath)) break;
		compileErr = await compile(testPath);
	}
	const authorWall = secs(t0);
	const authorStats = latestRunStats(cwd);
	if (compileErr || !existsSync(testPath)) {
		return `delegate: the architect's ${ACCEPTANCE_TEST} does not parse after ${MAX_ORACLE_REPAIRS} repair attempts, so it cannot be frozen or run.\n\n--- syntax error ---\n${compileErr ?? "(test missing)"}\n\n--- architect output (tail) ---\n${authorReport.slice(-1200)}`;
	}
	// When verbose, show the handover the architect wrote — the test and the brief it hands over.
	if (verbose()) {
		const show = (p: string, title: string) => { try { process.stdout.write(`\n──── ${title} ────\n${readFileSync(resolve(cwd, p), "utf8")}\n`); } catch {} };
		show(ACCEPTANCE_TEST, ACCEPTANCE_TEST);
		show("BRIEF.md", "BRIEF.md");
	}
	// Freeze the oracle: the worker must not edit or weaken the acceptance test.
	let froze = false;
	try { chmodSync(testPath, 0o444); froze = true; } catch {}
	const t1 = Date.now();
	let workerReport: string;
	try {
		workerReport = await worker(WORKER_BRIEF);
	} finally {
		if (froze) try { chmodSync(testPath, 0o644); } catch {}
	}
	const workerWall = secs(t1);
	// The worker's record is the newest for cwd only if it differs from the architect's span.
	const ws = latestRunStats(cwd);
	const workerStats = ws && ws.id !== authorStats?.id ? ws : undefined;
	const t2 = Date.now();
	const { passed, output } = await acceptance(ACCEPTANCE_CMD);
	const acceptWall = secs(t2);
	const totalWall = secs(t0);

	const stage = (name: string, stats: { turns: number } | undefined, wall: number) =>
		`${name} ${stats?.turns != null ? `${stats.turns} turns` : "turns n/a"}/${wall}s`;
	const clip = verbose() ? (s: string) => s : (s: string) => s.slice(-1200);
	return [
		`handover: ${ACCEPTANCE_TEST} + BRIEF.md written by the architect (the worker did not author the test).`,
		`acceptance: ${passed ? "PASS ✅" : "FAIL ❌"}  (${ACCEPTANCE_CMD})`,
		`turns/wall: ${stage("architect", authorStats, authorWall)} · ${stage("worker", workerStats, workerWall)} · acceptance ${acceptWall}s · total ${totalWall}s`,
		passed && !verbose() ? "" : `--- acceptance output ---\n${clip(output)}`,
		`--- worker report ---\n${clip(workerReport)}`,
	].filter(Boolean).join("\n");
}

export interface DoTaskPhasedDeps extends DoTaskDeps {
	authorPhases?: (task: string) => Promise<string>;
	shell?: (cmd: string) => Promise<{ passed: boolean; output: string }>;
}

/** The phase test files the architect wrote, ordered by phase number: tests/test_phase1_*.py … */
export function listPhaseTests(cwd: string): string[] {
	let files: string[] = [];
	try { files = readdirSync(resolve(cwd, PHASE_TEST_DIR)); } catch { return []; }
	return files
		.map((f) => ({ f, m: PHASE_TEST_RE.exec(f) }))
		.filter((x) => x.m)
		.sort((a, b) => Number(a.m![1]) - Number(b.m![1]) || a.f.localeCompare(b.f))
		.map((x) => `${PHASE_TEST_DIR}/${x.f}`);
}

/** The cumulative pytest command for phases 0..i (every phase so far must stay green). */
export function phaseCmd(paths: string[], upto: number): string {
	return `uv run --with pytest python -m pytest ${paths.slice(0, upto + 1).join(" ")} -q`;
}

/** What the per-phase worker is told: pass THIS phase's test without breaking earlier phases. */
export function phaseWorkerBrief(paths: string[], i: number): string {
	return (
		`This is phase ${i + 1} of ${paths.length}. Read BRIEF.md for the overall goal, then implement the ` +
		`solution so this phase's acceptance test passes:\n  ${paths[i]}\n` +
		(i > 0 ? "Earlier phases are already built and their tests pass — do NOT break them. " : "") +
		`Do NOT edit any ${PHASE_TEST_DIR}/test_phase*.py file; they are the frozen oracle. ` +
		"Work only inside this directory — do NOT read, search for, or copy files outside it. " +
		`Run this exact command until every test passes, then stop:\n  ${phaseCmd(paths, i)}`
	);
}

/**
 * Per-phase delegation (MELLUM_DELEGATE_PHASED=1): the architect decomposes the spec into ordered
 * phases (one cumulative test file each); then each phase gets its OWN fresh worker against the
 * cumulative test, and a passing phase is git-checkpointed so a later phase cannot silently break
 * an earlier one. Fresh budget per phase is what single-shot lacked.
 */
export async function doTaskPhased(task: string, deps: DoTaskPhasedDeps = {}): Promise<string> {
	const authorPhases = deps.authorPhases ?? spawnAuthorPhases;
	const worker = deps.worker ?? spawnWorker;
	const acceptance = deps.acceptance ?? runAcceptance;
	const compile = deps.compile ?? compileTest;
	const repair = deps.repair ?? spawnRepair;
	const shell = deps.shell ?? runAcceptance;
	const cwd = process.cwd();
	const secs = (from: number) => Math.round((Date.now() - from) / 1000);

	const t0 = Date.now();
	let authorReport = await authorPhases(task);
	let paths = listPhaseTests(cwd);
	if (!paths.length) {
		return `delegate(phased): the architect wrote no ${PHASE_TEST_DIR}/test_phaseN_*.py files, so there is no phased handover to run.\n\n--- architect output (tail) ---\n${authorReport.slice(-1500)}`;
	}
	// Every phase test must parse before we freeze or run anything (finding 1 recurs per file).
	for (const p of paths) {
		let err = await compile(resolve(cwd, p));
		for (let i = 0; err && i < MAX_ORACLE_REPAIRS; i++) {
			if (verbose()) process.stdout.write(`\n[handover] ${p} does not parse — asking the architect to fix the syntax (attempt ${i + 1}/${MAX_ORACLE_REPAIRS}):\n${err}\n`);
			authorReport = await repair(err, p);
			err = existsSync(resolve(cwd, p)) ? await compile(resolve(cwd, p)) : "(test missing)";
		}
		if (err) return `delegate(phased): ${p} does not parse after ${MAX_ORACLE_REPAIRS} repair attempts, so it cannot be frozen or run.\n\n--- syntax error ---\n${err}\n\n--- architect output (tail) ---\n${authorReport.slice(-1200)}`;
	}
	const authorWall = secs(t0);
	const authorStats = latestRunStats(cwd);
	if (verbose()) {
		for (const p of paths) { try { process.stdout.write(`\n──── ${p} ────\n${readFileSync(resolve(cwd, p), "utf8")}\n`); } catch {} }
		try { process.stdout.write(`\n──── BRIEF.md ────\n${readFileSync(resolve(cwd, "BRIEF.md"), "utf8")}\n`); } catch {}
	}

	// Git checkpointing (best-effort): a clean slate, then a commit per passing phase, so a later
	// phase that breaks an earlier one is reverted to the last good phase, not carried forward.
	const haveGit = (await shell("command -v git >/dev/null 2>&1")).passed;
	if (haveGit) {
		// Keep heavy/irrelevant paths out of the checkpoints so `git clean` on a revert is safe.
		try {
			const gi = resolve(cwd, ".gitignore");
			const have = existsSync(gi) ? readFileSync(gi, "utf8") : "";
			const add = [".venv/", "__pycache__/", "*.pyc", "grader_tests/"].filter((l) => !have.includes(l));
			if (add.length) writeFileSync(gi, (have && !have.endsWith("\n") ? have + "\n" : have) + add.join("\n") + "\n");
		} catch {}
		await shell('git init -q && git add -A && git -c user.email=w@w -c user.name=w commit -q -m handover --no-verify || true');
	}

	const stage = (name: string, stats: { turns: number } | undefined, wall: number) =>
		`${name} ${stats?.turns != null ? `${stats.turns} turns` : "turns n/a"}/${wall}s`;
	const freeze = (p: string, ro: boolean) => { try { chmodSync(resolve(cwd, p), ro ? 0o444 : 0o644); } catch {} };
	const lines: string[] = [];
	let passedCount = 0;
	let prevId = authorStats?.id;
	for (let i = 0; i < paths.length; i++) {
		for (let j = 0; j <= i; j++) freeze(paths[j], true); // the worker cannot weaken any oracle so far
		const cmd = phaseCmd(paths, i);
		const tPhase = Date.now();
		let passed = false, output = "";
		for (let attempt = 0; attempt <= MAX_PHASE_RETRIES && !passed; attempt++) {
			await worker(phaseWorkerBrief(paths, i)); // a fresh worker (fresh turn budget) each attempt
			({ passed, output } = await acceptance(cmd));
		}
		const phaseWall = secs(tPhase);
		const ws = latestRunStats(cwd);
		const wStats = ws && ws.id !== prevId ? ws : undefined;
		prevId = ws?.id ?? prevId;
		lines.push(`phase ${i + 1}/${paths.length} (${paths[i]}): ${passed ? "PASS ✅" : "FAIL ❌"} · ${stage("worker", wStats, phaseWall)}`);
		if (passed) {
			passedCount++;
			if (haveGit) await shell(`git add -A && git -c user.email=w@w -c user.name=w commit -q -m "phase ${i + 1}" --no-verify || true`);
		} else {
			if (verbose()) lines.push(`--- phase ${i + 1} acceptance output ---\n${output.slice(-1200)}`);
			if (haveGit) { for (let j = 0; j <= i; j++) freeze(paths[j], false); await shell("git reset --hard -q && git clean -fdq || true"); }
			break; // a later phase cannot build on a broken one
		}
	}
	for (const p of paths) freeze(p, false);
	const totalWall = secs(t0);
	return [
		`handover (phased): ${paths.length} phase test${paths.length === 1 ? "" : "s"} + BRIEF.md written by the architect.`,
		`phases passed: ${passedCount}/${paths.length}${passedCount < paths.length ? " (stopped at the first failing phase)" : " — full pass ✅"}`,
		...lines,
		`turns/wall: ${stage("architect", authorStats, authorWall)} · total ${totalWall}s`,
	].join("\n");
}

// ── Step-file delegation (MELLUM_DELEGATE_STEPS=1) ──────────────────────────────
// A finer-grained handover than per-phase: the architect splits the whole spec into the SMALLEST
// ordered chunks, each written as stepNN.md (the chunk's own brief + named contracts) with its OWN
// self-contained test tests/test_stepN_*.py, plus a todo.md ledger. Each step gets a fresh worker
// (fresh budget) that reads only its step doc; the HARNESS — never the worker — ticks todo.md after
// it independently runs and passes that step's test, git-checkpointing each pass. "Done" means every
// step is ticked AND a final full run of all step tests is green. The architect derives the steps
// from the spec (it names no suite phase), so this stays agnostic.

/** step01.md, step02.md, … — the per-step instruction docs the architect writes. */
export const STEP_DOC_RE = /^step(\d+)\.md$/i;
export const STEP_TEST_DIR = "tests";
/** tests/test_step1_*.py — the self-contained test for a step (number matched to its doc). */
export const STEP_TEST_RE = /^test_step(\d+)[_.].*\.py$/;
export const TODO_FILE = "todo.md";
/** One fresh-budget retry per step before it is declared failed. */
export const MAX_STEP_RETRIES = 1;

export interface Step { n: number; doc: string; test: string; }

/** The phased architect prompt's sibling: split the spec into small ordered steps, each a doc plus
 * its own self-contained test, and a todo.md ledger. Never the code. */
export function authorStepsPrompt(task: string): string {
	return (
		"You are the ARCHITECT, not the implementer. Do NOT write any implementation code.\n" +
		"Read the task below AND every spec or notes file already in this directory (a specs/ folder, " +
		"AGENTS.md, a roadmap). Break the WHOLE project into SMALL ORDERED STEPS — the smallest chunks " +
		"that each add one working slice (step 1 is the first slice; each later step adds the next).\n" +
		"For each step N (N starts at 1, contiguous — 1, 2, 3, …) write TWO files:\n" +
		"  stepNN.md  (zero-padded: step01.md, step02.md, …) — the instructions for THAT chunk alone: " +
		"what to build, which files, and the exact named contracts it must satisfy.\n" +
		`  ${STEP_TEST_DIR}/test_stepN_<slug>.py — a SELF-CONTAINED test for THAT step only: it asserts ` +
		"every requirement the step adds, each as its own explicit check, and passes on that step alone. " +
		"It must FAIL now, before any implementation.\n" +
		"Pin EXACT NAMED CONTRACTS, not just behaviour. Wherever the spec names something concrete — a " +
		"module, a module-level variable or attribute, a class, a function, a collection or field name, an " +
		"exact count, or a verbatim seed string or literal — assert that named thing DIRECTLY (import the " +
		"module and check the attribute, its type, its length/count, and the exact seed values), as well as " +
		"probing behaviour through any route or output.\n" +
		"COVERAGE: the spec's requirements are the contract. A spec's own \"write tests\" line is a FLOOR, " +
		"not the ceiling — assert EVERY requirement the step states, not just the checks the spec suggests. " +
		"For any requirement about what a user SEES — a rendered label, badge, button, or the order items " +
		"appear on a page — drive the real route and assert on the RESPONSE BODY (the rendered page), not " +
		"only an in-memory object. Exercise the real end-to-end path: create through its own route, act " +
		"through the route, then re-read through the route — do NOT mutate seed or fixture state in place. " +
		"Each assertion must FAIL on the obvious wrong build (state stored but never rendered, an id " +
		"recomputed from position, items silently reordered).\n" +
		"NORTH STAR: in each stepNN.md, COPY the exact spec text — the requirement lines VERBATIM — that " +
		"the step must satisfy, under a \"## Spec (verbatim)\" heading. That copied spec is the step's north " +
		"star: write the step's test to assert each copied requirement, and quote the requirement in the " +
		"assertion message so a failure names the exact spec line it breaks. Copy the spec's words, never a " +
		"paraphrase. Also point each stepNN.md back to the original spec plan it came from — name the spec " +
		"file and section (for example specs/roadmap.md and the phase) — so the step stays linked to the " +
		"full plan, not just its own slice.\n" +
		QUOTING_RULE + "\n" +
		`Then write ${TODO_FILE} — a checklist with ONE UNCHECKED line per step, in order, each naming the ` +
		"step doc and its test:\n" +
		`  - [ ] step01 — <title> — ${STEP_TEST_DIR}/test_step1_<slug>.py\n` +
		"And write BRIEF.md — 2 to 4 sentences on what to build overall and which files. Write ONLY the " +
		`step docs, the step tests, ${TODO_FILE} and BRIEF.md, nothing else; do NOT create, edit or stub ` +
		"any implementation file. Before you stop, confirm the steps are contiguous from 1, each step doc " +
		"has its own test, and together they cover the whole spec.\n\n" +
		`Task: ${task}`
	);
}

/** The step architect pass: split the spec into step docs + self-contained tests + a todo.md. */
export function spawnAuthorSteps(task: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...guardArgs(), "-e", SELF, `/mellum ${authorStepsPrompt(task)}`], "architect: splitting the spec into steps");
}

/** The final spec-coverage pass: the architect re-reads the spec against the tests it wrote and ADDS
 * any requirement it left unasserted, before the oracle is frozen. A harness-guaranteed pass, not a
 * prose rule — for a fixed small model a guaranteed pass lands where a rule in the first prompt does
 * not. It edits only the test files and may never weaken an assertion. */
export function authorVerifyPrompt(task: string): string {
	return (
		"You are the ARCHITECT doing a FINAL SPEC-COVERAGE PASS. Do NOT write any implementation code.\n" +
		"Re-read every spec or notes file in this directory, every step doc (stepNN.md), AND every " +
		`${STEP_TEST_DIR}/test_step*.py you wrote. For EACH step, go through the spec's requirements for ` +
		"that step ONE BY ONE and confirm each is asserted in that step's test. The requirements are the " +
		"contract; the spec's own \"write tests\" suggestion is a FLOOR, not the ceiling. Where a requirement " +
		"is unasserted or only partly checked, ADD the missing assertion to that step's test: assert a " +
		"rendered requirement through the RESPONSE BODY (the real route's output), exercise the real " +
		"end-to-end path (create → act → re-read through the routes) rather than mutating seed state, and " +
		"make each check FAIL on the obvious wrong build. Confirm each stepNN.md quotes VERBATIM, under its " +
		"\"## Spec (verbatim)\" heading, the spec requirements that step covers — its north star — and copy " +
		"in any requirement line that is missing. Edit ONLY the step docs and test files; do NOT touch any " +
		"implementation file, and do NOT weaken, delete, or make always-true any existing assertion. " +
		QUOTING_RULE + "\n\n" +
		`Task: ${task}`
	);
}

/** The final spec-coverage pass as a spawned architect run. */
export function spawnAuthorVerify(task: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...guardArgs(), "-e", SELF, `/mellum ${authorVerifyPrompt(task)}`], "architect: final spec-coverage pass");
}

/** The step docs paired with their numbered tests, ordered by step number. A doc with no matching
 * test cannot be gated, so it is left out (and reported as "no paired step" when none pairs up). */
export function listSteps(cwd: string): Step[] {
	let docs: string[] = [];
	try { docs = readdirSync(cwd); } catch { return []; }
	let tests: string[] = [];
	try { tests = readdirSync(resolve(cwd, STEP_TEST_DIR)); } catch {}
	const testByN = new Map<number, string>();
	for (const f of tests) { const m = STEP_TEST_RE.exec(f); if (m) testByN.set(Number(m[1]), `${STEP_TEST_DIR}/${f}`); }
	const steps: Step[] = [];
	for (const f of docs) {
		const m = STEP_DOC_RE.exec(f);
		if (!m) continue;
		const n = Number(m[1]);
		const test = testByN.get(n);
		if (test) steps.push({ n, doc: f, test });
	}
	return steps.sort((a, b) => a.n - b.n);
}

/** The self-contained pytest command for ONE step (that step's test alone). */
export function stepTestCmd(step: Step): string {
	return `uv run --with pytest python -m pytest ${step.test} -q`;
}

/** The full-suite pytest command over the given steps' tests (regression guard + final verdict). */
export function allStepsCmd(steps: Step[]): string {
	return `uv run --with pytest python -m pytest ${steps.map((s) => s.test).join(" ")} -q`;
}

/** What the per-step worker is told: read your step doc, pass your step's test, keep earlier steps
 * green. On a retry, `failure` carries the previous attempt's actual test output, handed back as the
 * bugs to fix — so the worker fixes the real non-compliance instead of rebuilding blind. */
export function stepWorkerBrief(steps: Step[], i: number, failure?: string): string {
	const s = steps[i];
	return (
		`This is step ${s.n} of ${steps.length}. Read ${s.doc} — it is YOUR instructions for this step — ` +
		`and BRIEF.md for the overall goal. Implement the solution so this step's test passes:\n  ${s.test}\n` +
		(i > 0 ? "Earlier steps are already built and their tests pass — do NOT break them. " : "") +
		`Do NOT edit any ${STEP_TEST_DIR}/test_step*.py file; they are the frozen oracle. ` +
		"You may also consult the original spec plan in this directory (the specs/ folder, a roadmap, " +
		"AGENTS.md) for context — your step doc and its verbatim spec block are the contract, the full " +
		"plan is there to refer to. Work only inside this directory — do NOT read, search for, or copy " +
		"files outside it. " +
		`Run this exact command until every test passes, then stop:\n  ${stepTestCmd(s)}` +
		(failure
			? `\n\nYour previous attempt did NOT pass. These are the failures (bugs) — your build does not comply with the spec. Fix them so every check passes:\n${failure.slice(-1500)}`
			: "")
	);
}

/** The todo.md ledger the harness owns: one line per step, ticked [x] only for steps it verified. */
export function renderTodo(steps: Step[], done: ReadonlySet<number>): string {
	const body = steps.map((s) => `- [${done.has(s.n) ? "x" : " "}] step${String(s.n).padStart(2, "0")} — ${s.doc} — ${s.test}`).join("\n");
	const n = steps.filter((s) => done.has(s.n)).length;
	return `# TODO — ${n}/${steps.length} steps done and tested\n\n${body}\n`;
}

export interface DoTaskStepsDeps extends DoTaskPhasedDeps {
	authorSteps?: (task: string) => Promise<string>;
	authorVerify?: (task: string) => Promise<string>;
}

/**
 * Step-file delegation (MELLUM_DELEGATE_STEPS=1): the architect splits the spec into small ordered
 * steps (a stepNN.md doc + a self-contained test each) and a todo.md ledger; then each step gets its
 * OWN fresh worker reading only its step doc. The harness runs that step's own test, and only on a
 * real pass ticks todo.md and git-checkpoints it — the worker's self-exit is never trusted. Done
 * means every step is ticked AND a final full run of all step tests is green.
 */
export async function doTaskSteps(task: string, deps: DoTaskStepsDeps = {}): Promise<string> {
	const authorSteps = deps.authorSteps ?? spawnAuthorSteps;
	const authorVerify = deps.authorVerify ?? spawnAuthorVerify;
	const worker = deps.worker ?? spawnWorker;
	const acceptance = deps.acceptance ?? runAcceptance;
	const compile = deps.compile ?? compileTest;
	const repair = deps.repair ?? spawnRepair;
	const shell = deps.shell ?? runAcceptance;
	const cwd = process.cwd();
	const secs = (from: number) => Math.round((Date.now() - from) / 1000);

	const t0 = Date.now();
	let authorReport = await authorSteps(task);
	const steps = listSteps(cwd);
	if (!steps.length) {
		return `delegate(steps): the architect wrote no paired stepNN.md + ${STEP_TEST_DIR}/test_stepN_*.py files, so there is no step handover to run.\n\n--- architect output (tail) ---\n${authorReport.slice(-1500)}`;
	}
	// Every step test must parse before we freeze or run anything (the architect's nested-quote bug).
	const ensureParses = async (): Promise<string | undefined> => {
		for (const s of steps) {
			let err = await compile(resolve(cwd, s.test));
			for (let i = 0; err && i < MAX_ORACLE_REPAIRS; i++) {
				if (verbose()) process.stdout.write(`\n[handover] ${s.test} does not parse — asking the architect to fix the syntax (attempt ${i + 1}/${MAX_ORACLE_REPAIRS}):\n${err}\n`);
				authorReport = await repair(err, s.test);
				err = existsSync(resolve(cwd, s.test)) ? await compile(resolve(cwd, s.test)) : "(test missing)";
			}
			if (err) return `${s.test} does not parse after ${MAX_ORACLE_REPAIRS} repair attempts: ${err}`;
		}
		return undefined;
	};
	let parseErr = await ensureParses();
	if (parseErr) return `delegate(steps): ${parseErr}\n\n--- architect output (tail) ---\n${authorReport.slice(-1200)}`;

	// Final spec-coverage pass: the architect re-reads the spec against every step test and fills any
	// requirement it left unasserted (the "write-tests floor" miss), before the oracle is frozen. Then
	// re-parse, since the pass just edited the tests.
	if (verbose()) process.stdout.write(`\n[handover] final spec-coverage pass: the architect checks each step test against the spec…\n`);
	authorReport = await authorVerify(task);
	parseErr = await ensureParses();
	if (parseErr) return `delegate(steps): after the spec-coverage pass, ${parseErr}\n\n--- architect output (tail) ---\n${authorReport.slice(-1200)}`;

	const authorWall = secs(t0);
	const authorStats = latestRunStats(cwd);

	// The harness owns todo.md truth: start it all-unchecked and tick only what it verifies itself.
	const done = new Set<number>();
	const writeTodo = () => { try { writeFileSync(resolve(cwd, TODO_FILE), renderTodo(steps, done)); } catch {} };
	writeTodo();
	if (verbose()) {
		for (const s of steps) { try { process.stdout.write(`\n──── ${s.doc} ────\n${readFileSync(resolve(cwd, s.doc), "utf8")}\n`); } catch {} }
		try { process.stdout.write(`\n──── BRIEF.md ────\n${readFileSync(resolve(cwd, "BRIEF.md"), "utf8")}\n`); } catch {}
	}

	// Git checkpointing (best-effort): a clean slate, then a commit per passing step, so a later step
	// that breaks an earlier one is reverted to the last good step, not carried forward.
	const haveGit = (await shell("command -v git >/dev/null 2>&1")).passed;
	if (haveGit) {
		try {
			const gi = resolve(cwd, ".gitignore");
			const have = existsSync(gi) ? readFileSync(gi, "utf8") : "";
			const add = [".venv/", "__pycache__/", "*.pyc", "grader_tests/"].filter((l) => !have.includes(l));
			if (add.length) writeFileSync(gi, (have && !have.endsWith("\n") ? have + "\n" : have) + add.join("\n") + "\n");
		} catch {}
		await shell('git init -q && git add -A && git -c user.email=w@w -c user.name=w commit -q -m handover --no-verify || true');
	}

	const stage = (name: string, stats: { turns: number } | undefined, wall: number) =>
		`${name} ${stats?.turns != null ? `${stats.turns} turns` : "turns n/a"}/${wall}s`;
	const freeze = (p: string, ro: boolean) => { try { chmodSync(resolve(cwd, p), ro ? 0o444 : 0o644); } catch {} };
	const lines: string[] = [];
	let prevId = authorStats?.id;
	for (let i = 0; i < steps.length; i++) {
		for (let j = 0; j <= i; j++) freeze(steps[j].test, true); // the worker cannot weaken any oracle so far
		const tStep = Date.now();
		let passed = false, output = "";
		// Each step is gated on its OWN self-contained test; a later regression is caught by the
		// final full-suite run, not by mixing the cumulative set into a per-step gate.
		for (let attempt = 0; attempt <= MAX_STEP_RETRIES && !passed; attempt++) {
			// A fresh worker each attempt; on a retry, hand back the previous failure as the bugs to fix.
			await worker(stepWorkerBrief(steps, i, attempt > 0 ? output : undefined));
			({ passed, output } = await acceptance(stepTestCmd(steps[i])));
		}
		const stepWall = secs(tStep);
		const ws = latestRunStats(cwd);
		const wStats = ws && ws.id !== prevId ? ws : undefined;
		prevId = ws?.id ?? prevId;
		lines.push(`step ${steps[i].n}/${steps.length} (${steps[i].doc}): ${passed ? "PASS ✅" : "FAIL ❌"} · ${stage("worker", wStats, stepWall)}`);
		if (passed) {
			done.add(steps[i].n);
			writeTodo(); // the harness ticks todo.md only after it verified the step itself
			if (haveGit) await shell(`git add -A && git -c user.email=w@w -c user.name=w commit -q -m "step ${steps[i].n}" --no-verify || true`);
		} else {
			if (verbose()) lines.push(`--- step ${steps[i].n} output ---\n${output.slice(-1200)}`);
			if (haveGit) { for (let j = 0; j <= i; j++) freeze(steps[j].test, false); await shell("git reset --hard -q && git clean -fdq || true"); }
			break; // a later step cannot build on a broken one
		}
	}
	for (const s of steps) freeze(s.test, false);

	// Done only when every step is ticked AND a final full run of all step tests is green.
	const complete = done.size === steps.length;
	const finalGreen = complete ? (await acceptance(allStepsCmd(steps))).passed : false;
	writeTodo();
	const totalWall = secs(t0);
	return [
		`handover (steps): ${steps.length} step doc${steps.length === 1 ? "" : "s"} + self-contained test${steps.length === 1 ? "" : "s"} + ${TODO_FILE} + BRIEF.md.`,
		`steps done and tested: ${done.size}/${steps.length}${complete ? (finalGreen ? " — 100%, full suite green ✅" : " — all ticked but the full suite did not pass ❌") : " (stopped at the first failing step)"}`,
		...lines,
		`turns/wall: ${stage("architect", authorStats, authorWall)} · total ${totalWall}s`,
	].join("\n");
}

// ── Plan delegation, no per-step tests (MELLUM_DELEGATE_PLAN=1) ──────────────────
// The simplest shape: the architect splits the spec into small ordered step docs (stepNN.md, each
// carrying the verbatim spec it covers and a link back to the plan), and a fresh worker builds each
// step from its doc. No per-step test, no freeze, no verify pass — the oracle is the suite's hidden
// grader at the end, and whether that is enough without a per-step gate is the open, measured
// question. Simpler than doTaskSteps; a candidate to replace it if it grades as well.

export interface PlanStep { n: number; doc: string; }

/**
 * How many times the architect is re-dispatched if it wrote no stepNN.md files. The fixed small
 * model sometimes spends its whole output budget reasoning and truncates before writing anything;
 * this is the harness guard for that (a guarantee, not a prose rule) — retry with feedback.
 */
export const MAX_AUTHOR_RETRIES = 2;

/** The feedback-augmented task for a re-dispatched architect that wrote no step docs. Agnostic. */
export function authorRetryTask(task: string): string {
	return (
		"RETRY — your previous attempt wrote NO stepNN.md files. Most likely you spent your whole " +
		"output budget reasoning before writing anything. This time write the files FIRST: emit " +
		"step01.md immediately, then step02.md, and so on, keeping any reasoning between files to a " +
		"sentence. The files are the only thing that matters — write them before you run out.\n\n" +
		task
	);
}

/** At most this many requirement bullets belong in one step; the plan's step floor scales by it. */
export const MAX_REQS_PER_STEP = 5;

/**
 * The minimum number of steps a plan for this spec should have, derived from the spec itself:
 * one step per MAX_REQS_PER_STEP requirement bullets (lines that start with -, * or a number).
 * A prose spec with no bullets imposes no floor (0). Agnostic — it reads the task, nothing else.
 * This is the guard against an architect that under-splits a many-requirement spec into a handful
 * of coarse steps (each too big for the fixed worker, so a contract gets dropped and the build
 * breaks). A heuristic floor, to be screened, not a suite-tuned number.
 */
export function planMinSteps(task: string): number {
	let bullets = 0;
	for (const line of task.split("\n")) {
		if (/^\s*([-*]|\d+[.)])\s+\S/.test(line)) bullets++;
	}
	return bullets === 0 ? 0 : Math.ceil(bullets / MAX_REQS_PER_STEP);
}

/** Feedback for a re-dispatched architect whose plan was too coarse for the spec. Agnostic. */
export function authorSplitTask(task: string, got: number, want: number): string {
	return (
		`RETRY — your plan had only ${got} step${got === 1 ? "" : "s"}, too coarse for this spec. Each ` +
		"step must add ONE small slice, not a whole phase — a single step that bundles many " +
		`requirements is too big to build correctly. Split finer: aim for at least ${want} steps, at ` +
		`most ${MAX_REQS_PER_STEP} requirements per step. Rewrite the stepNN.md files from step01.md.\n\n` +
		task
	);
}

/** The architect prompt for plan mode: split the spec into step docs only — no tests. */
export function authorPlanPrompt(task: string): string {
	return (
		"You are the ARCHITECT, not the implementer. Do NOT write any implementation code and do NOT " +
		"write any tests.\n" +
		"Read the task below AND every spec or notes file already in this directory (a specs/ folder, " +
		"AGENTS.md, a roadmap). Break the WHOLE project into SMALL ORDERED STEPS — the smallest chunks " +
		"that each add one working slice (step 1 is the first slice; each later step adds the next).\n" +
		"For each step N (N starts at 1, contiguous — 1, 2, 3, …) write ONE file:\n" +
		"  stepNN.md  (zero-padded: step01.md, step02.md, …) — the instructions for THAT chunk alone: " +
		"what to build, which files, and the EXACT named contracts it must satisfy (module, variable, " +
		"class, field and collection names, exact counts, verbatim seed strings).\n" +
		"In each stepNN.md, COPY the exact spec text — the requirement lines VERBATIM — that the step must " +
		"satisfy, under a \"## Spec (verbatim)\" heading, and point back to the original spec plan it came " +
		"from (name the spec file and section, for example specs/roadmap.md and the phase). Copy the " +
		"spec's words, never a paraphrase.\n" +
		`Then write ${TODO_FILE} — a checklist with ONE UNCHECKED line per step, in order (- [ ] step01 — ` +
		"<title>). And write BRIEF.md — 2 to 4 sentences on what to build overall and which files. Write " +
		`ONLY the step docs, ${TODO_FILE} and BRIEF.md — no tests, no implementation files. Before you ` +
		"stop, confirm the steps are contiguous from 1 and together cover the whole spec.\n" +
		"Write the step files AS YOU GO — emit step01.md first, then the next, and keep your reasoning " +
		"between files to a sentence, so you do NOT run out of output before the files are written.\n\n" +
		`Task: ${task}`
	);
}

/** The plan architect pass as a spawned run. */
export function spawnAuthorPlan(task: string): Promise<string> {
	return runPi(["-p", "--no-approve", "--no-skills", "--no-prompt-templates", "--no-themes", ...guardArgs(), "-e", SELF, `/mellum ${authorPlanPrompt(task)}`], "architect: splitting the spec into step docs (no tests)");
}

/** Remove any stepNN.md in the cwd, so a re-dispatched architect's plan is counted clean. */
export function clearStepDocs(cwd: string): void {
	for (const s of listStepDocs(cwd)) { try { rmSync(resolve(cwd, s.doc)); } catch {} }
}

/** The step docs (stepNN.md) in the cwd, ordered by step number. No paired test is required. */
export function listStepDocs(cwd: string): PlanStep[] {
	let docs: string[] = [];
	try { docs = readdirSync(cwd); } catch { return []; }
	const steps: PlanStep[] = [];
	for (const f of docs) {
		const m = STEP_DOC_RE.exec(f);
		if (m) steps.push({ n: Number(m[1]), doc: f });
	}
	return steps.sort((a, b) => a.n - b.n);
}

/** What the plan-mode worker is told: build THIS step from its doc; no test to run. */
export function planWorkerBrief(steps: PlanStep[], i: number): string {
	const s = steps[i];
	// MELLUM_DELEGATE_WORKER_DIRECT=1 adds a terse nudge: the step is already fully
	// specified by the architect, so the worker should implement it rather than
	// re-derive the whole plan. A probe showed this cuts a step's thinking ~half and
	// keeps the clean think/answer split (unlike enable_thinking=false). Default off,
	// so the shipped brief is frozen until a ladder screen measures it.
	const direct = process.env.MELLUM_DELEGATE_WORKER_DIRECT === "1";
	return (
		`This is step ${s.n} of ${steps.length}. Read ${s.doc} — it is YOUR instructions for this step, ` +
		"including the exact spec it must satisfy (its \"## Spec (verbatim)\" block) — and BRIEF.md for the " +
		"overall goal. Build the solution for this step so every requirement in its spec block is met. " +
		(i > 0 ? "Earlier steps are already built — do NOT break them. " : "") +
		"You may also consult the original spec plan in this directory (the specs/ folder, a roadmap, " +
		"AGENTS.md) for context. Work only inside this directory — do NOT read, search for, or copy files " +
		"outside it. " +
		(direct
			? "This step is fully specified: implement it directly from the doc — do not reason at length " +
			  "or re-derive the earlier steps' decisions; make exactly the change the doc asks for. "
			: "") +
		"Implement the step completely, then stop."
	);
}

/** The brief for one fresh attempt after a step worker stalled at the turn budget: hand over the
 * stall and ask for the simplest correct build, so it stops thrashing on a failing command. */
export function planRethinkBrief(steps: PlanStep[], i: number, turns: number, cap: number): string {
	const s = steps[i];
	return (
		`Your previous attempt at step ${s.n} stalled: it ran ${turns} tool calls (budget ${cap}) without ` +
		`finishing — usually from re-running a failing command instead of fixing its cause. Start over on ` +
		`this step from ${s.doc} and BRIEF.md. Make the SIMPLEST change that satisfies its spec, using the ` +
		`project's ordinary conventions. If a command fails, read the error and fix the cause once; do not ` +
		`re-run it repeatedly, add dependencies, or build scaffolding. Implement it and stop.`
	);
}

/** The plan-mode todo ledger the harness owns: one line per step, ticked as each is built. */
export function renderPlanTodo(steps: PlanStep[], done: ReadonlySet<number>): string {
	const body = steps.map((s) => `- [${done.has(s.n) ? "x" : " "}] step${String(s.n).padStart(2, "0")} — ${s.doc}`).join("\n");
	const n = steps.filter((s) => done.has(s.n)).length;
	return `# TODO — ${n}/${steps.length} steps built\n\n${body}\n`;
}

export interface DoTaskPlanDeps {
	authorPlan?: (task: string) => Promise<string>;
	worker?: (brief: string) => Promise<string>;
	shell?: (cmd: string) => Promise<{ passed: boolean; output: string }>;
	runStats?: (cwd: string) => { turns: number; wall?: number; id: string } | undefined;
}

// The per-step worker budget from MELLUM_TURN_CAP, or 0 when unset. When set (e.g. 25), a worker
// that stalls at the budget gets one rethink re-dispatch; unset keeps the old single-attempt loop.
const workerTurnCap = (): number => {
	const n = Number(process.env.MELLUM_TURN_CAP);
	return Number.isFinite(n) && n > 0 ? n : 0;
};

/**
 * Plan delegation (MELLUM_DELEGATE_PLAN=1): the architect splits the spec into step docs (no tests),
 * and a fresh worker builds each step from its doc. The harness checkpoints each step with git and
 * ticks todo.md as it goes — there is no per-step gate, so "built" is the worker finishing, not a test
 * passing. The suite's hidden grader is the only oracle, applied at the end; this is the arm that
 * measures whether the test machinery is worth its complexity.
 */
export async function doTaskPlan(task: string, deps: DoTaskPlanDeps = {}): Promise<string> {
	const authorPlan = deps.authorPlan ?? spawnAuthorPlan;
	const worker = deps.worker ?? spawnWorker;
	const shell = deps.shell ?? runAcceptance;
	const runStats = deps.runStats ?? latestRunStats;
	const cwd = process.cwd();
	const secs = (from: number) => Math.round((Date.now() - from) / 1000);

	const t0 = Date.now();
	// Two harness guards on the architect pass — guarantees, not prose rules, for the fixed model:
	//   (1) truncation: it spends its output budget reasoning and writes NO stepNN.md;
	//   (2) coarseness: it writes docs but under-splits a many-requirement spec into a handful of
	//       steps, each too big for the worker to build correctly (a dropped contract → broken build).
	// Either way re-dispatch with the fitting feedback, within one shared retry budget.
	const minSteps = planMinSteps(task);
	let authorReport = await authorPlan(task);
	let steps = listStepDocs(cwd);
	let authorAttempts = 1;
	while (authorAttempts <= MAX_AUTHOR_RETRIES && (!steps.length || steps.length < minSteps)) {
		authorAttempts++;
		const hint = steps.length ? authorSplitTask(task, steps.length, minSteps) : authorRetryTask(task);
		clearStepDocs(cwd); // a coarse plan is rewritten from step01.md — don't leave stale docs behind
		authorReport = await authorPlan(hint);
		steps = listStepDocs(cwd);
	}
	if (!steps.length) {
		return `delegate(plan): the architect wrote no stepNN.md step docs after ${authorAttempts} attempts, so there is no plan to run.\n\n--- architect output (tail) ---\n${authorReport.slice(-1500)}`;
	}
	const coarse = steps.length < minSteps; // retries spent but still under the floor — run it anyway
	const authorWall = secs(t0);
	const authorStats = runStats(cwd);

	const done = new Set<number>();
	const writeTodo = () => { try { writeFileSync(resolve(cwd, TODO_FILE), renderPlanTodo(steps, done)); } catch {} };
	writeTodo();
	if (verbose()) {
		for (const s of steps) { try { process.stdout.write(`\n──── ${s.doc} ────\n${readFileSync(resolve(cwd, s.doc), "utf8")}\n`); } catch {} }
		try { process.stdout.write(`\n──── BRIEF.md ────\n${readFileSync(resolve(cwd, "BRIEF.md"), "utf8")}\n`); } catch {}
	}

	const haveGit = (await shell("command -v git >/dev/null 2>&1")).passed;
	if (haveGit) {
		try {
			const gi = resolve(cwd, ".gitignore");
			const have = existsSync(gi) ? readFileSync(gi, "utf8") : "";
			const add = [".venv/", "__pycache__/", "*.pyc", "grader_tests/"].filter((l) => !have.includes(l));
			if (add.length) writeFileSync(gi, (have && !have.endsWith("\n") ? have + "\n" : have) + add.join("\n") + "\n");
		} catch {}
		await shell('git init -q && git add -A && git -c user.email=w@w -c user.name=w commit -q -m handover --no-verify || true');
	}

	const stage = (name: string, stats: { turns: number } | undefined, wall: number) =>
		`${name} ${stats?.turns != null ? `${stats.turns} turns` : "turns n/a"}/${wall}s`;
	const lines: string[] = [];
	let prevId = authorStats?.id;
	const cap = workerTurnCap();
	for (let i = 0; i < steps.length; i++) {
		const tStep = Date.now();
		await worker(planWorkerBrief(steps, i)); // a fresh worker (fresh turn budget) builds this step
		let ws = runStats(cwd);
		let wStats = ws && ws.id !== prevId ? ws : undefined;
		prevId = ws?.id ?? prevId;
		// Rethink: a worker that stalled at the turn budget left the step half-built. Give it ONE
		// fresh attempt with the stall handed over, so it takes the simplest path instead of thrashing.
		let rethought = false;
		if (cap && wStats && wStats.turns >= cap) {
			rethought = true;
			await worker(planRethinkBrief(steps, i, wStats.turns, cap));
			ws = runStats(cwd);
			if (ws && ws.id !== prevId) wStats = ws;
			prevId = ws?.id ?? prevId;
		}
		const stepWall = secs(tStep);
		done.add(steps[i].n);
		writeTodo();
		if (haveGit) await shell(`git add -A && git -c user.email=w@w -c user.name=w commit -q -m "step ${steps[i].n}" --no-verify || true`);
		lines.push(`step ${steps[i].n}/${steps.length} (${steps[i].doc}): built${rethought ? " · rethought after stall" : ""} · ${stage("worker", wStats, stepWall)}`);
	}
	const totalWall = secs(t0);
	return [
		`handover (plan): ${steps.length} step doc${steps.length === 1 ? "" : "s"} + ${TODO_FILE} + BRIEF.md (no tests).`,
		`steps built: ${done.size}/${steps.length} — grade with the suite's hidden oracle (there is no per-step gate).`,
		...(coarse ? [`note: the plan stayed coarse (${steps.length} steps, below the ${minSteps}-step floor for this spec) after the split retries — built as best effort.`] : []),
		...lines,
		`turns/wall: ${stage("architect", authorStats, authorWall)} · total ${totalWall}s`,
	].join("\n");
}

const INSTRUCTION_ROLES = new Set(["system", "developer"]);

/**
 * A copy of a user message with the project facts appended: to string content, to the
 * last text part of array content, or as a new text part when there is none. Never
 * mutates `m`; a message that already ends with the block is returned as is.
 */
export function withFacts(m: Msg, facts: string): Msg {
	if (typeof m.content === "string") return m.content.endsWith(facts) ? m : { ...m, content: m.content + facts };
	if (!Array.isArray(m.content)) return { ...m, content: facts.replace(/^\n+/, "") };
	const parts: any[] = [...m.content];
	for (let i = parts.length - 1; i >= 0; i--) {
		const p = parts[i];
		if (p && p.type === "text" && typeof p.text === "string") {
			if (!p.text.endsWith(facts)) parts[i] = { ...p, text: p.text + facts };
			return { ...m, content: parts };
		}
	}
	parts.push({ type: "text", text: facts.replace(/^\n+/, "") });
	return { ...m, content: parts };
}

export function filterForMellum(payload: any, systemPrompt: string, opts: { expectMarker?: boolean; keepSystem?: boolean; stripThinking?: boolean } = {}) {
	if (!payload || !Array.isArray(payload.messages)) return payload;
	const msgs: Msg[] = payload.messages;
	const isMarker = (m: Msg) => m.role === "user" && (textOf(m).includes(MARK_ON) || textOf(m).includes(MARK_OFF));
	const isBootstrap = (m: Msg) => textOf(m).includes(BOOTSTRAP_MARKER);
	let start = 0;
	let markerAt = -1;
	for (let i = msgs.length - 1; i >= 0; i--) {
		if (msgs[i].role === "user" && textOf(msgs[i]).includes(MARK_ON)) {
			markerAt = i;
			break;
		}
	}
	let markerMissing = false;
	if (markerAt >= 0) {
		start = markerAt + 1;
		// Pi delivers a queued marker after the user message it was queued for, so the
		// prompt that started the mode sits just before the marker (possibly behind an
		// off-marker). Keep it unless a later user message already carries the task.
		const laterUser = msgs.slice(start).some((m) => m.role === "user" && !isMarker(m));
		if (!laterUser) {
			let j = markerAt - 1;
			while (j >= 0 && isMarker(msgs[j])) j--;
			if (j >= 0 && msgs[j].role === "user" && !isBootstrap(msgs[j])) start = j;
		}
	} else if (opts.expectMarker) {
		// The marker was compacted away or never arrived: send only the last user
		// message rather than the whole parent history, and say so.
		markerMissing = true;
		for (let i = msgs.length - 1; i >= 0; i--) {
			if (msgs[i].role === "user" && !isMarker(msgs[i]) && !isBootstrap(msgs[i])) {
				start = i;
				break;
			}
		}
	}
	const kept = msgs
		.slice(start)
		.filter((m) => !INSTRUCTION_ROLES.has(m.role ?? "") && !isMarker(m) && !isBootstrap(m));
	const system = opts.keepSystem
		? (msgs.find((m) => m.role === "system") ?? { role: "system", content: "" })
		: { role: "system", content: systemPrompt };
	const messages = opts.stripThinking ? stripReasoning(kept as Record<string, any>[]) : kept;
	const out: any = { ...payload, messages: [system, ...messages] };
	// Tool-narrowing and project facts are remedy units now (context/narrow-tools,
	// context/add-project-facts); the thin worker only drops the pre-marker history and
	// swaps the system prompt. The units reuse the narrowTools/withFacts exports below.
	if (markerMissing) out.mellumModeMarkerMissing = true;
	return out;
}

/** Keep only the worker's seven tools in `out` (and drop a tool_choice outside them), reading
 * them from `payload`. Shared with the `context/narrow-tools` remedy unit. */
export function narrowTools(payload: any, out: any): void {
	const tools = payload.tools.filter((t: any) => WORKER_TOOLS.includes(t?.function?.name ?? t?.name));
	if (tools.length) out.tools = tools;
	else delete out.tools;
	const chosen = payload.tool_choice?.function?.name ?? payload.tool_choice?.name;
	if (chosen && !WORKER_TOOLS.includes(chosen)) delete out.tool_choice;
}

/**
 * Drop earlier assistant reasoning from the payload.
 *
 * Left in place by default: removing it made runs 60% slower on the ladder (A12),
 * because this backend's prefix cache absorbs the repeated reasoning and the run
 * pays for the lost context in output tokens instead. `MELLUM_STRIP_THINKING=1`
 * opens the seam so the claim can be measured rather than assumed.
 */
export function stripReasoning<T extends Record<string, any>>(messages: T[]): T[] {
	return messages.map((m) => {
		if (m?.role !== "assistant") return m;
		if (!("reasoning_content" in m) && !("reasoning" in m)) return m;
		const { reasoning_content: _content, reasoning: _reasoning, ...rest } = m;
		return rest as T;
	});
}

/**
 * What the parent sees of a finished Mellum span: one block instead of every
 * read, edit and test run. Built from the span's own messages (Pi's internal
 * message format, as seen by the `context` event). Open spans are untouched.
 */
export interface HandoffOptions {
	/** Reports whether a written path still exists at handoff time; omitted means never flag. */
	exists?: (path: string) => boolean;
}

export function collapseHandoffs(messages: Msg[], opts: HandoffOptions = {}): Msg[] {
	// At the `context` event a sent marker is a `custom` message; in the provider
	// payload it has become a user message. Accept both.
	const hasMark = (m: Msg, mark: string) => (m.role === "user" || m.role === "custom") && textOf(m).includes(mark);
	const out: Msg[] = [];
	let i = 0;
	while (i < messages.length) {
		const m = messages[i];
		if (hasMark(m, MARK_ON)) {
			let j = i + 1;
			while (j < messages.length && !hasMark(messages[j], MARK_OFF)) j++;
			if (j >= messages.length) {
				out.push(...messages.slice(i));
				break;
			}
			// The task is the user message just before the on-marker (Pi queues the
			// marker after the prompt it was queued with), else the first after it.
			const last = out[out.length - 1];
			const prev = last && last.role === "user" && !hasMark(last, MARK_OFF) ? out.pop() : undefined;
			let span = messages.slice(i + 1, j);
			// The off-marker is queued "next turn", so it lands after the prompt the user
			// typed next; trailing user messages after the span's last reply are that
			// prompt, not part of the task.
			let tail = span.length;
			while (tail > 0 && span[tail - 1].role === "user") tail--;
			const trailing = span.slice(tail);
			span = span.slice(0, tail);
			const task = prev ? textOf(prev) : textOf(span.find((x) => x.role === "user") ?? {});
			const factsSource = /facts: (\S+)/.exec(textOf(m))?.[1];
			out.push(handoffMessage(task, span, opts, factsSource), ...trailing);
			i = j + 1;
			continue;
		}
		out.push(m);
		i++;
	}
	return out;
}

const MAX_HANDOFF_COMMANDS = 15;

function summaryLine(stats: SpanStats, factsSource?: string): string {
	const n = stats.requests;
	const wall = stats.wallSeconds === undefined ? "wall unknown" : `${stats.wallSeconds} s`;
	const last = { ok: "last command ok", failed: "last command failed", unfinished: "last command did not finish", none: "no commands" }[stats.lastCommand];
	return `Mellum: ${n} request${n === 1 ? "" : "s"}, ${stats.usage.output.toLocaleString("en-US")} output tokens, ${wall}, ${last}${factsSource ? `, facts: ${factsSource}` : ""}`;
}

function handoffMessage(task: string, span: Msg[], opts: HandoffOptions = {}, factsSource?: string): Msg {
	const stats = spanStats(span);
	const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n) + "…" : s);
	const oneLine = (s: string) => s.replace(/\s+/g, " ").trim();
	const fileList = stats.files.map((f) => (opts.exists && !opts.exists(f) ? `${f} (missing at handoff)` : f));
	const shown = stats.commands.slice(-MAX_HANDOFF_COMMANDS);
	const hidden = stats.commands.length - shown.length;
	const commandLines = shown.map((c) => `- ${clip(oneLine(c.command), 200)}${!c.finished ? " (no result)" : c.failed ? " (failed)" : ""}`);
	const body = [
		"[mellum-worker handoff] Mellum ran a task in this session; its tool calls are in the transcript but not repeated here.",
		summaryLine(stats, factsSource),
		`Task: ${clip(task.trim(), 400)}`,
		`Files edited or written: ${fileList.length ? fileList.join(", ") : "none"}`,
		commandLines.length
			? `Commands run${hidden ? ` (${hidden} earlier not shown)` : ""}:\n${commandLines.join("\n")}`
			: "Commands run: none",
		stats.lastCommandOutput ? `Last command output:\n${clip(stats.lastCommandOutput, 600)}` : "Last command output: none",
		stats.finalReply ? `Mellum's final reply:\n${clip(stats.finalReply, 1500)}` : "Mellum's final reply: (empty)",
	].join("\n");
	return { role: "user", content: [{ type: "text", text: body }], timestamp: Date.now() };
}

export type Subcommand = { cmd: "on" | "off" | "check" | "learn" | "last" | "task"; n?: number; task?: string };

/** `/mellum` arguments: on (or nothing), off, check, learn [n], last; anything else is a task. */
export function parseSubcommand(args: string): Subcommand {
	const want = (args || "").trim();
	if (want === "" || want === "on") return { cmd: "on" };
	if (want === "off" || want === "check" || want === "last") return { cmd: want };
	const learn = /^learn(?:\s+(\d+))?$/.exec(want);
	if (learn) return { cmd: "learn", n: learn[1] === undefined ? 10 : Number(learn[1]) };
	return { cmd: "task", task: want };
}

/** The one line shown on activation when the server is not as the measured settings expect. */
export function serverWarning(server: ServerCheck, nCtxMin: number): string | undefined {
	if (server.up === false) return "the llama-server did not report status ok. Run /mellum check.";
	if (server.nCtx !== undefined && server.nCtx < nCtxMin) {
		return `the llama-server context window is ${server.nCtx}, below the measured ${nCtxMin}. Run /mellum check.`;
	}
	return undefined;
}

/** The trailing span still open at the end of `messages`: its task text and messages, or undefined. */
export function openSpan(messages: Msg[]): { task: string; span: Msg[] } | undefined {
	const hasMark = (m: Msg, mark: string) => (m.role === "user" || m.role === "custom") && textOf(m).includes(mark);
	let on = -1;
	for (let i = messages.length - 1; i >= 0; i--) {
		if (hasMark(messages[i], MARK_OFF)) return undefined;
		if (hasMark(messages[i], MARK_ON)) {
			on = i;
			break;
		}
	}
	if (on === -1) return undefined;
	const span = messages.slice(on + 1);
	// The prompt sits just before the on-marker, or behind the previous one-shot's off-marker,
	// which Pi delivers after the next prompt (as filterForMellum allows for).
	let p = on - 1;
	while (p >= 0 && hasMark(messages[p], MARK_OFF)) p--;
	const prev = messages[p];
	const task = prev && prev.role === "user" && !hasMark(prev, MARK_ON) ? textOf(prev) : textOf(span.find((m) => m.role === "user") ?? {});
	return { task, span };
}

function runsFile(): string | undefined {
	const file = modeRunsFile(process.env, home()); // not "."; PowerShell sets no HOME
	return file === undefined ? undefined : resolve(file);
}

/**
 * Reports a problem the user must see. Without a UI (`pi -p`, `--mode json`) Pi's notify
 * is a no-op, so the message goes to stderr instead. Never throws.
 */
function warn(ctx: any, msg: string, level: "warning" | "error") {
	try {
		if (ctx?.hasUI === false) console.error(msg);
		else ctx?.ui?.notify?.(msg, level);
	} catch {}
}

/** Shows output the user asked for: notify with a UI, stdout without one. */
function say(ctx: any, msg: string, level: "info" | "warning" | "error" = "info") {
	if (ctx?.hasUI === false) console.log(msg);
	else ctx?.ui?.notify?.(msg, level);
}

const home = () => process.env.HOME || homedir();
const readIfExists = (p: string) => (existsSync(p) ? readFileSync(p, "utf8") : undefined);

/**
 * `options.fetch` replaces the global fetch for the server checks (tests pass a fake).
 */
export default function (pi: any, options: { startTimeoutMs?: number; fetch?: typeof fetch; spawnWorker?: (brief: string) => Promise<string>; author?: (task: string) => Promise<string>; authorPhases?: (task: string) => Promise<string>; authorSteps?: (task: string) => Promise<string>; authorVerify?: (task: string) => Promise<string>; authorPlan?: (task: string) => Promise<string>; acceptance?: (cmd: string) => Promise<{ passed: boolean; output: string }> } = {}) {
	// How the primary farms a brief to a fresh worker: the real spawn, or a test's stand-in.
	const runWorker = options.spawnWorker ?? spawnWorker;
	// The full task-delegation loop (author the handover, then run the worker to pass) and its deps.
	const doTaskDeps: DoTaskDeps = { author: options.author, worker: runWorker, acceptance: options.acceptance };
	const doTaskPhasedDeps: DoTaskPhasedDeps = { authorPhases: options.authorPhases, worker: runWorker, acceptance: options.acceptance };
	const doTaskStepsDeps: DoTaskStepsDeps = { authorSteps: options.authorSteps, authorVerify: options.authorVerify, worker: runWorker, acceptance: options.acceptance };
	const doTaskPlanDeps: DoTaskPlanDeps = { authorPlan: options.authorPlan, worker: runWorker };
	let active = false;
	let interactive = false;
	let saved: { model: any; tools: string[] } | undefined;
	let prompt = "";
	let warnedMissing = false;
	// Per-span counters for the one-line summary shown at /mellum off.
	let span = { startedAt: 0, requests: 0, toolCalls: 0, outputTokens: 0 };
	let activeModel = "";
	// The parent's context as last seen while on, plus assistant turns since; the run record is built from these.
	let lastContext: Msg[] = [];
	let turnsSinceContext: Msg[] = [];
	// Per-span facts for the run record, reset in activate.
	let host = "unknown";
	let activation: Activation = "on";
	let promptVersion = "unknown";
	// Facts are a remedy unit now; the worker records the run as facts source "none".
	const spanFacts: ProjectFacts = { source: "none", bullets: [], testCommand: null, chars: 0 };
	let server: ServerCheck = { up: null };

	// The activation check: one admin GET, at most 1 s, never throws; unreadable gives match null.
	async function checkServer(): Promise<ServerCheck> {
		try {
			const { baseUrl } = readProvider("pi", home(), readIfExists);
			return await serverCheck(adminBaseOf(baseUrl), { timeoutMs: 1000, fetch: options.fetch });
		} catch {
			return { up: null };
		}
	}

	// /mellum check: the whole check for Pi, printed. Never activates, never writes.
	async function runCheck(ctx: any) {
		try {
			const inputs = await gatherInputs("pi", { home: home(), read: readIfExists, get: (url) => fetchJson(url, { timeoutMs: 3000, fetch: options.fetch }) });
			const findings = checkSetup(inputs, loadExpected());
			const level = findings.some((f) => f.level === "fail") ? "error" : findings.some((f) => f.level === "warn") ? "warning" : "info";
			say(ctx, formatFindings(findings), level);
		} catch (error) {
			warn(ctx, `mellum check: ${(error as Error)?.message ?? String(error)}`, "error");
		}
	}

	// /mellum learn [n]: the report for this directory, from Mode's and the Worker's records.
	// AGENTS.md is written only when the user answers yes; without a UI, or past the facts cap,
	// nothing is asked or written. After the yes it is read and merged again, and written only
	// when the lines to add are still the ones asked about and still within the cap.
	async function runLearn(ctx: any, n: number | undefined) {
		if (n === undefined || !Number.isInteger(n) || n < 1) return warn(ctx, "mellum learn: n must be a whole number above 0", "warning");
		const cwd: string = typeof ctx?.cwd === "string" ? ctx.cwd : process.cwd();
		const agentsPath = resolve(cwd, "AGENTS.md");
		let merged: ReturnType<typeof mergeSuggestion>;
		let suggestion: string[];
		try {
			const report = learnFromTexts(recordFiles(process.env, home()).map(readIfExists), { cwd, n });
			suggestion = report.suggestion;
			merged = mergeSuggestion(readIfExists(agentsPath), suggestion);
			say(ctx, formatReport(report, cwd, merged.added) + formatMerge(merged, suggestion));
		} catch (error) {
			return warn(ctx, `mellum learn: ${(error as Error)?.message ?? String(error)}`, "error");
		}
		// Past the facts cap Mode would ignore the whole section, so do not offer the write.
		if (ctx?.hasUI === false || merged.added.length === 0 || overCap(merged) || typeof ctx?.ui?.confirm !== "function") return;
		let yes = false;
		try {
			yes = (await ctx.ui.confirm("Add these lines to AGENTS.md?", merged.added.map((b) => `- ${b}`).join("\n"))) === true;
		} catch (error) {
			return warn(ctx, `mellum learn: ${(error as Error)?.message ?? String(error)}`, "error");
		}
		if (!yes) return;
		try {
			const now = mergeSuggestion(readIfExists(agentsPath), suggestion);
			if (overCap(now) || JSON.stringify(now.added) !== JSON.stringify(merged.added)) {
				return warn(ctx, "mellum learn: AGENTS.md changed while asking; run /mellum learn again", "warning");
			}
			writeFileSync(agentsPath, now.text);
			const k = merged.added.length;
			say(ctx, `mellum learn: added ${k} line${k === 1 ? "" : "s"} to ${agentsPath}`);
		} catch (error) {
			warn(ctx, `mellum learn: could not write AGENTS.md: ${(error as Error)?.message ?? String(error)}`, "error");
		}
	}

	// /mellum last: the newest record at or under this directory, as Markdown. A custom message
	// renders it and lets the main model answer questions about it; while Mode is on it is a
	// notification instead, since a message would join Mellum's span. Never starts a turn.
	function runLast(ctx: any) {
		const cwd: string = typeof ctx?.cwd === "string" ? ctx.cwd : process.cwd();
		try {
			const files = recordFiles(process.env, home());
			if (files.length === 0) return say(ctx, "mellum last: run records are off (MELLUM_MODE_RUNS=0)", "warning");
			const { record } = pickLast(files.map(readIfExists), cwd);
			if (!record) return say(ctx, `mellum last: no Mellum runs recorded under ${cwd} (read ${files.join(", ")})`, "warning");
			const text = formatLast(record);
			if (ctx?.hasUI === false || active) return say(ctx, text);
			pi.sendMessage({ customType: "mellum-last", content: text, display: true }, { triggerTurn: false });
		} catch (error) {
			warn(ctx, `mellum last: ${(error as Error)?.message ?? String(error)}`, "error");
		}
	}

	// Same resolver for the handoff collapse and the run record: absolute, else relative to the cwd.
	const existsInCwd = (p: string) => existsSync(isAbsolute(p) ? p : resolve(process.cwd(), p));

	async function activate(ctx: any, notify: boolean, how: Activation) {
		if (active) {
			ctx.ui?.notify?.("mellum-worker is already on", "info");
			return;
		}
		const { provider, id } = DEFAULT_MODEL;
		// The shipped model when the registry has it; otherwise a session model that
		// is itself Mellum, which is what a llama.cpp profile configures.
		const sessionModel = /mellum/i.test(String(ctx.model?.id ?? "")) ? ctx.model : undefined;
		const model = ctx.modelRegistry.find(provider, id) ?? sessionModel;
		if (!model) {
			warn(ctx, `mellum-worker: model ${provider}/${id} not found and the session model is not Mellum; mode stays off`, "error");
			return;
		}
		const label = `${model.provider}/${model.id}`;
		const previous = { model: ctx.model, tools: pi.getActiveTools() };
		// Runs while the model switches; awaited below, so it adds at most its own timeout.
		const pendingServer = checkServer();
		const switched = await pi.setModel(model);
		if (!switched) {
			warn(ctx, `mellum-worker: could not select ${label} (auth or provider error); mode stays off`, "error");
			return;
		}
		saved = previous;
		active = true;
		span = { startedAt: Date.now(), requests: 0, toolCalls: 0, outputTokens: 0 };
		activeModel = label;
		lastContext = [];
		turnsSinceContext = [];
		host = typeof ctx.mode === "string" ? ctx.mode : "unknown";
		activation = how;
		promptVersion = "none"; // the worker applies no prompt; it is a remedy unit now
		interactive = notify;
		warnedMissing = false;
		server = await pendingServer;
		const serverWarn = serverWarning(server, loadExpected().nCtxMin);
		if (serverWarn) warn(ctx, serverWarn, "warning");
		if (notify) pi.sendMessage({ customType: "mellum-worker", content: `${MARK_ON} facts: ${spanFacts.source}`, display: true }, { deliverAs: "nextTurn" });
		if (notify) ctx.ui?.notify?.(`mellum-worker on: ${label}`, "info");
	}

	async function deactivate(ctx: any) {
		if (!active) {
			ctx.ui?.notify?.("mellum-worker is not on", "info");
			return;
		}
		if (!saved?.model) {
			warn(ctx, "mellum-worker: no previous model to restore; staying on. Pick a model with /model, then /mellum off.", "warning");
			return;
		}
		const restored = await pi.setModel(saved.model);
		if (!restored) {
			warn(ctx, "mellum-worker: could not restore the previous model; staying on", "error");
			return;
		}
		pi.setActiveTools(saved.tools);
		writeRunRecord(ctx);
		active = false;
		pi.sendMessage({ customType: "mellum-worker", content: MARK_OFF, display: true }, { deliverAs: "nextTurn" });
		const secs = Math.round((Date.now() - span.startedAt) / 1000);
		ctx.ui?.notify?.(`mellum-worker off: ${span.requests} request${span.requests === 1 ? "" : "s"}, ${span.toolCalls} tool call${span.toolCalls === 1 ? "" : "s"}, ${span.outputTokens.toLocaleString("en-US")} output tokens, ${secs} s`, "info");
	}

	// Never lets an error escape: deactivation must complete whatever happens here.
	function writeRunRecord(ctx: any) {
		let file: string | undefined;
		try {
			file = runsFile();
			if (!file) return;
			const open = openSpan([...lastContext, ...turnsSinceContext]);
			if (!open) return;
			mkdirSync(dirname(file), { recursive: true });
			appendFileSync(file, JSON.stringify(runRecord(open.task, open.span, { endedAt: Date.now(), cwd: process.cwd(), model: activeModel, exists: existsInCwd, host, activation, promptVersion, nudges: 0, guardBlocks: 0, facts: { source: spanFacts.source, testCommand: spanFacts.testCommand, chars: spanFacts.chars }, server })) + "\n");
		} catch (error) {
			warn(ctx, `mellum-worker: could not write the run record${file ? ` to ${file}` : ""}: ${(error as Error)?.message ?? String(error)}`, "warning");
		}
	}

	let oneShot = false;
	// The one in-flight deactivation of a one shot, shared by agent_settled and the headless handler.
	let settling: Promise<void> | undefined;
	// Resolves the headless handler's wait for the run to start; set only while it waits.
	let onRunStart: (() => void) | undefined;
	const startTimeoutMs = options.startTimeoutMs ?? 60_000;

	// Ends a one shot exactly once: a second caller gets the deactivation already under way.
	function settle(ctx: any): Promise<void> {
		if (settling) return settling;
		oneShot = false;
		settling = deactivate(ctx).finally(() => {
			settling = undefined;
		});
		return settling;
	}

	pi.registerCommand("mellum", {
		description: "mellum <task> | on | off | check | learn [n] | last — run Mellum with the worker prompt and tools inside this session",
		handler: async (args: string, ctx: any) => {
			const sub = parseSubcommand(args);
			if (sub.cmd === "off") return deactivate(ctx);
			if (sub.cmd === "on") return activate(ctx, true, "on");
			if (sub.cmd === "check") return runCheck(ctx);
			if (sub.cmd === "learn") return runLearn(ctx, sub.n);
			if (sub.cmd === "last") return runLast(ctx);
			const want = sub.task ?? "";
			// In the primary, /mellum <task> runs the full delegation loop: an architect pass writes
			// the handover (a failing acceptance test + a brief), then the bare worker runs it to pass,
			// and the frozen acceptance test is the verdict. Only a spawned child (CHILD_ENV) runs the
			// task in this session, below — so no recursion.
			if (process.env[CHILD_ENV] !== "1") {
				// MELLUM_DELEGATE_PLAN=1 runs the simplest loop: the architect splits the spec into step
				// docs (no tests) and a fresh worker builds each from its doc; graded only by the hidden oracle.
				if (process.env.MELLUM_DELEGATE_PLAN === "1") {
					say(ctx, "mellum: splitting the spec into step docs (no tests), then a fresh worker builds each…");
					say(ctx, await doTaskPlan(want, doTaskPlanDeps));
					return;
				}
				// MELLUM_DELEGATE_STEPS=1 runs the step-file loop: the architect splits the spec into
				// small ordered steps (a doc + a self-contained test each) and a todo.md ledger, and
				// each step gets its own fresh worker, ticked and checkpointed as the harness verifies it.
				if (process.env.MELLUM_DELEGATE_STEPS === "1") {
					say(ctx, "mellum: splitting the spec into steps (step docs + self-contained tests + todo.md), then a fresh worker per step…");
					say(ctx, await doTaskSteps(want, doTaskStepsDeps));
					return;
				}
				// MELLUM_DELEGATE_PHASED=1 runs the per-phase loop: the architect splits the spec into
				// ordered phases and each phase gets its own fresh worker, checkpointed as it passes.
				if (process.env.MELLUM_DELEGATE_PHASED === "1") {
					say(ctx, "mellum: decomposing the spec into phases, then running a fresh worker per phase…");
					say(ctx, await doTaskPhased(want, doTaskPhasedDeps));
					return;
				}
				say(ctx, "mellum: writing the handover (failing test + brief), then running the worker to pass…");
				say(ctx, await doTask(want, doTaskDeps));
				return;
			}
			// One shot (the worker child): the task runs under the mode and the mode ends when the agent settles.
			if (active) {
				warn(ctx, "mellum-worker is already on; type the task as a normal prompt, or /mellum off first", "warning");
				return;
			}
			// Read while the ctx is certainly live. Without a UI (pi -p, JSON mode) Pi treats the
			// prompt as finished when this handler returns and disposes the runtime, so the
			// handler must wait for the run and the deactivation.
			const headless = ctx.hasUI === false && typeof ctx.waitForIdle === "function";
			const waitForIdle: () => Promise<void> = ctx.waitForIdle;
			await activate(ctx, true, "one-shot");
			if (!active) return;
			oneShot = true;
			if (!headless) {
				pi.sendUserMessage(want);
				return;
			}
			// sendUserMessage is fire-and-forget and the run is not active (so not "busy")
			// until Pi has run its input and before_agent_start handlers: wait for agent_start
			// first, or waitForIdle would return before the task ran.
			const started = new Promise<boolean>((resolve) => {
				onRunStart = () => resolve(true);
			});
			let timer: ReturnType<typeof setTimeout> | undefined;
			const timedOut = new Promise<boolean>((resolve) => {
				timer = setTimeout(() => resolve(false), startTimeoutMs);
			});
			pi.sendUserMessage(want);
			let didStart: boolean;
			try {
				didStart = await Promise.race([started, timedOut]);
			} finally {
				clearTimeout(timer);
				onRunStart = undefined;
			}
			if (!didStart) warn(ctx, `mellum-worker: the task did not start within ${startTimeoutMs / 1000} s; switching the mode off`, "warning");
			await waitForIdle();
			// Pi resolves the idle wait after agent_settled handlers return, so normally
			// agent_settled has already deactivated; cover the other order too.
			if (settling) await settling;
			else if (active && oneShot) await settle(ctx);
		},
	});

	// The delegate tool makes this extension the thing the primary loads: load it, and the
	// primary can hand generic implementation briefs to a local worker by itself. A spawned
	// worker child (CHILD_ENV) gets neither the tool nor the nudge, so it cannot delegate again.
	if (process.env[CHILD_ENV] !== "1" && typeof pi.registerTool === "function") {
		registerDelegate(pi, runWorker);
		pi.on("before_provider_request", (event: any) => (active ? undefined : withDelegateNudge(event.payload)));
	}

	pi.on("agent_start", () => {
		if (oneShot) onRunStart?.();
	});

	pi.on("agent_settled", async (_event: any, ctx: any) => {
		if (active && oneShot) await settle(ctx);
	});

	pi.on("session_start", async (_event: any, ctx: any) => {
		if (process.env.MELLUM_MODE === "1" && !active) await activate(ctx, false, "headless");
	});

	// While on, keep the last parent context snapshot for the run record. Collapsing a
	// finished span into one handoff block for the parent is the delegate/collapse-handoffs
	// remedy unit now, not the worker's job.
	pi.on("context", (event: any) => {
		if (!active) return undefined;
		lastContext = event.messages;
		turnsSinceContext = [];
		return undefined;
	});

	pi.on("before_provider_request", (event: any, ctx: any) => {
		if (!active) return undefined;
		span.requests += 1;
		// The worker swaps nothing into the payload now — not the prompt, not the tools. It only
		// drops the pre-marker history (mode-integrity, so Mellum never sees the parent's turns).
		// The prompt and tool-narrowing are remedy units (context/use-short-prompt,
		// context/narrow-tools) a preset switches on, like every other remediation.
		const out = filterForMellum(event.payload, prompt, {
			expectMarker: interactive,
			keepSystem: true,
			stripThinking: process.env.MELLUM_STRIP_THINKING === "1",
		});
		if (out?.mellumModeMarkerMissing) {
			delete out.mellumModeMarkerMissing;
			if (!warnedMissing) {
				warnedMissing = true;
				ctx?.ui?.notify?.("mellum-worker: the on-marker is gone from the context; sending only the last message", "warning");
			}
		}
		return out;
	});

	// Per-span counters for the /mellum off summary and the run record. Guards (the loop
	// breaker, empty-turn nudge and the rest) are remedy units now, not the worker's job.
	pi.on("tool_call", () => {
		if (!active) return undefined;
		span.toolCalls += 1;
		return undefined;
	});
	pi.on("turn_end", (event: any) => {
		if (!active) return undefined;
		const out = event?.message?.usage?.output;
		if (event?.message?.role === "assistant") {
			if (typeof out === "number") span.outputTokens += out;
			turnsSinceContext.push(event.message);
			streamTurn(event.message); // live turn stream for a verbose delegation child
		}
		return undefined;
	});
}
