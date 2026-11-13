/**
 * mellum-flow: the workflow as TOOLS the agent calls, not an external loop.
 *
 * The earlier harness drove the phases from an external Python loop (one `pi` per
 * phase). That is the wrong handle: a capable model, given well-shaped phase tools
 * and a workflow prompt, orchestrates itself. This extension registers the phases
 * as tools — `plan`, `review_plan`, `code`, `review_code`, `test` — and the top
 * agent calls them in order, iterating on REDO / test failure.
 *
 * Each phase (except `test`) runs as an ISOLATED `pi` sub-agent with its own system
 * prompt, thinking budget and tool allowlist, sharing the workspace (the cwd). Only
 * the coder sub-agent can write or run commands; the reviewers are read-only; the
 * planner writes TODO.md. `test` runs pytest directly (deterministic, no model).
 *
 * Light prerequisite guards (not a cage): `review_plan` and `code` require a TODO.md
 * to exist, so the agent must plan before it codes. Order is otherwise the prompt's.
 */

import { spawn } from "node:child_process";
import { appendFileSync, cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// The runner sets MELLUM_FLOW_FEED to a file it tails to the terminal. We append each
// sub-agent step there (pi swallows an extension's stderr in -p mode, so a file is the
// reliable channel). No-op when unset.
const FEED = process.env.MELLUM_FLOW_FEED;
function feed(line: string): void {
	if (!FEED) return;
	try {
		appendFileSync(FEED, line + "\n");
	} catch {
		/* feed is best-effort */
	}
}

const HERE = dirname(fileURLToPath(import.meta.url));
const ext = (name: string) => join(HERE, name);

interface Phase {
	thinking: string;
	tools: string;
	ext: string[];
	prompt: string;
	maxTokens: number;
}

// Our own operating guide, appended with each role under Pi's base prompt (--append-system-prompt;
// see runSubagent). It adds focus, brevity, tool-use and output-only discipline on top of Pi's
// "thorough coding agent" framing, which pushed the examiner to over-assert, WITHOUT contradicting
// any role (it governs HOW to operate, never WHAT to produce). It was written while Pi's base
// prompt was briefly replaced (--system-prompt), when the planner rambled for 600s on a trivial
// plan; "be decisive, do not deliberate at length" is the counter to that, and it stays useful
// now that the base prompt is back.
export const BASE_GUIDE =
	"You are a single-purpose sub-agent in an automated build. Your ONE job is defined under " +
	"YOUR ROLE below; do exactly that and nothing else. Operate with discipline:\n" +
	"- Be decisive and brief. Reach the result and STOP. Do NOT deliberate at length, restate the " +
	"task, think out loud, or add commentary — a long internal monologue wastes the token budget and " +
	"risks truncating your answer before it is written.\n" +
	"- Use the tools you are given to gather exactly what you need, then act. Do not narrate tool use.\n" +
	"- Produce EXACTLY the output your role specifies, in the format it specifies, with nothing around it.\n" +
	"- YOUR ROLE below is authoritative: where it is specific, follow it over this general guidance.\n\n" +
	"=== YOUR ROLE ===\n";

// The coder is the only executor (write/edit/bash + the safety guards). Reviewers are
// read-only judges; the planner turns the spec into a checklist. Budget maps to the ROLE:
// the reasoning roles (plan, review_plan, examine, review_code) think hard; the coder acts
// against an already-decided gate, so it executes rather than deliberates. NOTE: these bite
// only when the model exposes reasoning effort. Mellum/Flint set supportsReasoningEffort:false,
// so --thinking is a no-op for them and reasoning is bounded by max_tokens, not by this budget.
export const PHASES: Record<string, Phase> = {
	plan: {
		thinking: "high",
		tools: "read,grep,find,ls",
		ext: [ext("mellum-loopguard.ts")],
		maxTokens: 8192,
		prompt:
			"You are the PLANNER — step 1 of the pipeline plan → examine → code → test. Turn THIS phase's " +
			"spec (given below, and detailed in specs/) into the implementation checklist the coder will " +
			"follow. specs/roadmap.md may list several phases — plan ONLY the phase(s) the task names. " +
			"Your entire REPLY becomes plan/TODO.md, so output the plan and NOTHING else — no preamble, no " +
			"explanation, no code fences. BEGIN with the exact line `## North Star` (two hashes) and a " +
			"one-sentence goal, then a `- [ ]` checklist of every requirement, copying exact strings, keys, " +
			"routes and status codes verbatim from the spec. Keep it the SIMPLEST plan that meets the phase. " +
			"Do NOT plan to write tests: the EXAMINER writes the acceptance test next, and the coder makes " +
			"it pass — your checklist is the implementation only.",
	},
	review_plan: {
		thinking: "high",
		tools: "read,grep,find,ls",
		ext: [ext("mellum-loopguard.ts")],
		maxTokens: 8192,
		prompt:
			"You are the PLAN REVIEWER — read-only; you judge plan/TODO.md, you do not change files. Read " +
			"plan/TODO.md and specs/. Check the plan (a) opens with a North Star stating the phase's goal " +
			"that every step serves (judge SUBSTANCE — never REDO over heading level or formatting), " +
			"(b) covers every requirement of the phase, and (c) is the simplest that meets it. If it is " +
			"sound, reply EXACTLY `REVIEW: PASS`. Otherwise reply EXACTLY `REVIEW: REDO` then a plain list " +
			"of what to fix — the planner reads your list and revises.",
	},
	examine: {
		thinking: "high",
		tools: "read,grep,find,ls,lookup",
		ext: [ext("mellum-knowledge.ts"), ext("mellum-loopguard.ts")],
		// The examiner is a THINKING model whose reasoning cannot be capped (reasoning_effort and
		// enable_thinking are both no-ops on oMLX — verified). On a complex phase it needs >16384
		// tokens JUST to finish thinking, so at 16384 it emits ZERO output (finish_reason=length,
		// content="") and no gate freezes — hard phase 5 (Archive & Audit) died on exactly this.
		// Measured: at 16384 → empty; at 32000 → finishes thinking and emits a full 7-test file.
		// The cap must leave room for think + the test, so examine gets the largest budget.
		maxTokens: 32000,
		prompt:
			"You are the EXAMINER (step 2 of plan -> examine -> code -> test): write the acceptance test, the executable definition of DONE, for THIS phase's spec (below; details in specs/). It is FROZEN as the gate the coder must pass; you define 'correct' and never see the implementation. Earlier phases are ALREADY frozen and re-run, so cover only THIS phase and do not contradict them. FIRST read those earlier gate files (and the app/models they drive) and REUSE their conventions exactly — the client setup, HOW a record is created (the route, and whether it takes form `data=` or `json=`), and the field names — because they already pin the real app; do not reinvent those mechanics or guess them. Output ONLY the pytest file (no prose, no code fences). Be EXHAUSTIVE about the spec's requirements AND its negative/edge cases, not just the happy path (a weak test the code passes while the real grader fails is the failure that matters); then decide and WRITE the test, do not deliberate at length. Rules, applied to WHAT THE SPEC SAYS, inventing nothing:\n- VERBATIM: assert exact values (field/key names, status codes, routes, quoted strings) ONLY where the spec gives them verbatim. For things described but not quoted, assert the REQUIREMENT exists, never a made-up exact string/class/markup; invented strings are the brittleness that fails correct code.\n- BEHAVIOUR: assert the ordering, inclusion/exclusion and other behaviour the spec states, plus its negative/edge cases (invalid input, empty, forbidden, not-found, duplicates) with exact status/message.\n- COMPUTED/REPORT: for any value or endpoint that computes from data (a sum, count, filter, group, sort, derived view), assert the EXACT result the spec's definition requires, never a bare 200 or a non-empty body (a stub returns those too). Take the expected value from the data the spec points to: when that data ALREADY EXISTS in a store (e.g. a report the spec reads 'from' a database), READ what is actually there and compute the expected from it; do NOT delete, overwrite or reseed that store, because a destructive test corrupts the real data the spec and the grade depend on. Cover a row that a WRONG reading of each definition would mishandle (e.g. where a column-based rule and a status/obvious-field rule disagree), so the test fails a stub or a wrong definition.\n- IDENTITY: if the phase mutates a SPECIFIC record by id, assert the model carries a stable explicit id field, seeded records have DISTINCT ids, the route is addressed by that id, and the id is unchanged and the collection un-renumbered across the mutation, never by list position/index.\n- ABSENCE: to check a control is gone/absent, target it specifically (its form action=\"/...\" URL or the exact element), never a bare substring that is also a substring of a word the page shows.\n- SCHEMA: assert named migration/setup artifacts exist, apply, are idempotent, AND are actually recorded/applied (query the record the spec names, not merely that the function is defined).\n- CLIENT: import `from starlette.testclient import TestClient` and `from app import app`, then build the client ONCE as `client = TestClient(app, follow_redirects=False)` so asserting a 3xx status works (it follows redirects by default otherwise; plain GETs are unaffected). Never import TestClient from flask or anywhere else. Unsure of a library API? call `lookup` first.\n- SELF-CONTAINED / SHARED STATE: tests share state earlier tests have mutated, so never assume a seed record exists at a particular id or in a particular state, and never assert an absolute total that assumes a clean store; capture a COUNT or TOTAL BEFORE your change and assert the exact DELTA, not an absolute `== 1`. For an IN-MEMORY or API-created record, create the ones this test needs (e.g. POST them). For a PERSISTENT (file or database) store that outlives the test, do NOT mutate it destructively; read and compute from what is already there, and if you must add a row to exercise a case, do it in a transaction you ROLL BACK so the store is byte-for-byte unchanged afterward.\nOutput the pytest file only.",
	},
	code: {
		thinking: "low",
		tools: "read,grep,find,ls,write,edit,bash,lookup",
		ext: [ext("mellum-nonblock.ts"), ext("mellum-guards.ts"), ext("mellum-surgical.ts"), ext("mellum-knowledge.ts")],
		maxTokens: 16384,
		prompt:
			"You are the CODER — step 3 of the pipeline (plan → examine → code → test). Read plan/TODO.md " +
			"and specs/. The acceptance tests are ALREADY written for you " +
			"under `tests/` (files named `test_gate_phase_*.py`) — they are the definition of DONE, one " +
			"group per phase. Do NOT edit, delete or weaken ANY of them; your job is to make them ALL pass. " +
			"EARLIER phases' tests must keep passing — build on the existing code, do not break what already " +
			"works. Read the newest `test_gate_phase_*.py` to see exactly what THIS phase requires (exact " +
			"keys, status codes, behaviours), implement each unchecked `- [ ]` item in order, and check it " +
			"off (`- [x]`) once done. Run the tests with `PYTHONPATH=. uv run --with pytest pytest -q tests` " +
			"so `from app import ...` resolves; never start a server — use starlette.testclient.TestClient. " +
			"ALWAYS use the `lookup` tool before writing any unfamiliar or exact-contract API — a library " +
			"signature or default, a database/migration API, exact behaviour — and whenever a failure " +
			"looks API-shaped; do not guess an API you have not confirmed. When you read from data that ALREADY EXISTS (a table or database the feature reports 'from'), FIRST inspect its real columns and rows (e.g. `PRAGMA table_info`, a `SELECT`) and use the columns that are actually there — never invent a new column, or add one to hold what an existing column already holds, or assume a name the data does not use. Make the acceptance test pass." +
			"Address any reviewer feedback below.",
	},
	review_code: {
		thinking: "high",
		tools: "read,grep,find,ls",
		ext: [ext("mellum-loopguard.ts")],
		maxTokens: 8192,
		prompt:
			"You are the CODE REVIEWER — read-only; you judge, you do not change files. Read specs/, " +
			"plan/TODO.md and the code. Check (1) CONFORMANCE — every requirement of THIS phase is actually " +
			"implemented, including ones the frozen tests may not check (exact keys, status codes, fields, " +
			"stable identity, migrations); (2) SIMPLICITY — the simplest code that meets the spec. If it is " +
			"sound, reply EXACTLY `REVIEW: PASS`. Otherwise reply EXACTLY `REVIEW: REDO` then a plain list " +
			"of what is unmet or over-complex — the coder reads your list and revises, then re-runs the tests.",
	},
};

const PYTEST = ["uv", "run", "--with", "pytest", "pytest", "-q", "tests"];

/**
 * The stop-and-emit content cap. The loop-breaker caps repeated no-op CALLS; it cannot cap a model
 * that never makes the stop-and-write decision and instead pours out CONTENT (measured: examine on a
 * non-converging model, 3000+ events streaming toward its budget). maxTokens IS that bound — it forces
 * a `message_end` the examiner's output is salvaged from — but examine's default is a deliberately large
 * 32000 so a reasoning worker has room to think THEN emit. MELLUM_FLOW_MAXTOKENS applies a per-run
 * CEILING instead: it stops an over-generating model early while never lifting a phase's own smaller
 * budget, and unset it leaves every phase (and the default worker) byte-identical. Cascadable, like
 * MELLUM_FLOW_THINKING.
 */
export function effectiveMaxTokens(phaseMax: number, env = process.env.MELLUM_FLOW_MAXTOKENS): number {
	const cap = Number(env);
	return Number.isInteger(cap) && cap > 0 ? Math.min(phaseMax, cap) : phaseMax;
}

/** Pull the final assistant text out of a `--mode json` event stream. */
export function finalText(events: any[]): string {
	let text = "";
	for (const ev of events) {
		if (ev?.type === "message_end" && ev.message?.role === "assistant") {
			for (const block of ev.message.content ?? []) {
				if (block?.type === "text" && block.text) text = block.text;
			}
		}
	}
	return text;
}

/** The examiner is a tool-using agent: on complex phases it writes the test, then makes a
 *  verifying tool call and ends on a short non-test message, so finalText (the LAST text) misses
 *  the test and the gate never freezes — a whole round wasted (seen on hard phases 4 and 5). Scan
 *  EVERY assistant text block, strip fences, and return the longest that looks like a real pytest
 *  file; fall back to finalText when none does. */
export function bestPytest(events: any[]): string {
	let best = "";
	for (const ev of events) {
		if (ev?.type === "message_end" && ev.message?.role === "assistant") {
			for (const block of ev.message.content ?? []) {
				if (block?.type === "text" && block.text) {
					const code = asCode(block.text);
					if (looksLikePytest(code) && code.length > best.length) best = code;
				}
			}
		}
	}
	return best || finalText(events);
}

/** Spawn an isolated `pi` sub-agent for a phase; resolve with its final text. */
/** Summarise the tool calls in a pi `--mode json` stream event, across the schema variants it
 * actually emits (`message_end` carrying toolCall content, `tool_execution_start`, and the legacy
 * `tool_call`), so the sub-agent's actions show in the feed. Returns {name, where} per call, where
 * `where` is the command text or the path the call targets. The old streaming keyed ONLY on
 * `evt.type === "tool_call"` — a type pi never emits for a sub-agent — so no sub-agent command was
 * ever logged, which is exactly why a hung phase could not be diagnosed from the feed. */
export function toolCallSummaries(evt: any): { name: string; where: string }[] {
	const out: { name: string; where: string }[] = [];
	const push = (name: unknown, args: unknown) => {
		let a: any = args;
		if (typeof a === "string") {
			try { a = JSON.parse(a); } catch { a = { command: a }; }
		}
		a = a && typeof a === "object" ? a : {};
		const where = a.path ?? a.file_path ?? (a.command != null ? String(a.command) : "");
		out.push({ name: String(name ?? ""), where: String(where) });
	};
	if (!evt || typeof evt !== "object") return out;
	if (evt.type === "message_end") {
		const content = evt.message?.content;
		if (Array.isArray(content)) {
			for (const b of content) {
				if (b && typeof b === "object" && String(b.type).toLowerCase().includes("toolcall")) push(b.name, b.arguments);
			}
		}
	} else if (evt.type === "tool_execution_start") {
		push(evt.name, evt.arguments ?? evt.input);
	} else if (evt.type === "tool_call") {
		push(evt.toolName, evt.input);
	}
	return out;
}

function runSubagent(phase: string, task: string, cwd: string, signal?: AbortSignal): Promise<string> {
	const cfg = PHASES[phase];
	const dir = mkdtempSync(join(tmpdir(), "mellum-flow-"));
	const promptFile = join(dir, `${phase}.md`);
	// Our operating guide first (focus/brevity), then the authoritative role prompt.
	writeFileSync(promptFile, BASE_GUIDE + cfg.prompt);
	// Per-phase max_tokens: pi has no CLI flag for it, so patch a copy of the inherited agent dir's
	// models.json. The planner/reviewers get a smaller cap than examine/code — but NOT a tight one:
	// the model can't stop thinking, so too low (2048) spends the whole budget thinking and emits an
	// EMPTY output. The cap is a runaway backstop; the BASE_GUIDE is the real brevity lever.
	let env = process.env;
	const baseAgent = process.env.PI_CODING_AGENT_DIR;
	if (baseAgent && existsSync(join(baseAgent, "models.json"))) {
		const agentDir = join(dir, "agent");
		cpSync(baseAgent, agentDir, { recursive: true });
		const mp = join(agentDir, "models.json");
		const data = JSON.parse(readFileSync(mp, "utf8"));
		const prov: any = Object.values(data.providers)[0];
		prov.models[0].maxTokens = effectiveMaxTokens(cfg.maxTokens);
		writeFileSync(mp, `${JSON.stringify(data, null, 2)}\n`);
		env = { ...process.env, PI_CODING_AGENT_DIR: agentDir };
	}
	// The phase's thinking level is the default, but a model whose server templates thinking
	// itself (no pi-managed reasoning channel) can override it per-run via MELLUM_FLOW_THINKING.
	// Mellum leaves it unset, so cfg.thinking stands — this file is byte-identical for it.
	const thinking = process.env.MELLUM_FLOW_THINKING || cfg.thinking;
	const args = [
		"--mode", "json", "-p", "--no-session",
		"--no-extensions", "--no-skills", "--no-prompt-templates", "--no-context-files", "--no-approve",
		"--thinking", thinking, "--tools", cfg.tools,
	];
	for (const e of cfg.ext) args.push("-e", e); // explicit -e still load under --no-extensions
	// Append our guide + role UNDER Pi's base prompt. We tried REPLACING Pi's base (--system-prompt)
	// to stop it diluting the roles, but without it Mellum's planner thinks without bound and never
	// emits a plan — empty output even at 16384 tokens (every medium run died on an empty TODO). Pi's
	// base scaffolding is what keeps the model producing a final answer, so keep it and append
	// BASE_GUIDE + the role on top; the de-brittle examiner prompt mitigates Pi's "be thorough" nudge.
	args.push("--append-system-prompt", promptFile, `Task: ${task}`);

	const capped = effectiveMaxTokens(cfg.maxTokens);
	const capNote = capped < cfg.maxTokens ? `, maxTokens=${capped}` : "";
	feed(`  ━ ${phase} starting (think=${thinking}${capNote}) ━`);
	return new Promise((resolve) => {
		const child = spawn("pi", args, { cwd, env, stdio: ["ignore", "pipe", "pipe"] });
		const events: any[] = [];
		const t0 = Date.now();
		// Heartbeat: a phase working silently should still show it is alive. Independent of pi's
		// event schema — event count climbing = progress, flat = genuinely stuck.
		const beat = setInterval(() => {
			feed(`    [${phase}] …working ${Math.round((Date.now() - t0) / 1000)}s (${events.length} events)`);
		}, 5000);
		let buffer = "";
		const onData = (chunk: Buffer) => {
			buffer += chunk.toString();
			let nl: number;
			while ((nl = buffer.indexOf("\n")) >= 0) {
				const line = buffer.slice(0, nl).trim();
				buffer = buffer.slice(nl + 1);
				if (line) {
					try {
						const evt = JSON.parse(line);
						events.push(evt);
						// Stream the sub-agent's steps to the feed so a working phase is visible,
						// not silent. One line per tool call: `[code] -> write templates/home.html`.
						for (const c of toolCallSummaries(evt)) {
							// Collapse whitespace so a multi-line command (e.g. a heredoc/echo that can hang
							// the shell) shows on ONE feed line, and keep more of it so the culprit is legible.
							feed(`    [${phase}] → ${c.name.padEnd(6)} ${c.where.replace(/\s+/g, " ").slice(0, 300)}`);
						}
					} catch {
						/* non-JSON line */
					}
				}
			}
		};
		child.stdout.on("data", onData);
		// CRITICAL: drain stderr too. pi writes progress/logs there; if we leave the stderr
		// pipe unread it fills (~16KB) and the sub-agent blocks forever on write — the tool
		// then never returns and the orchestrator hangs. We only need to consume it.
		child.stderr.on("data", () => {});
		const abort = () => child.kill("SIGKILL");
		signal?.addEventListener("abort", abort, { once: true });
		child.on("close", () => {
			clearInterval(beat);
			signal?.removeEventListener("abort", abort);
			feed(`  ━ ${phase} done (${events.length} events) ━`);
			// The examiner's whole job is to emit a pytest file; salvage it from any block it was
			// written in (it often ends on verifying chatter). Other roles want their final message.
			const out = phase === "examine" ? bestPytest(events) : finalText(events);
			resolve(out || "(the sub-agent produced no text output)");
		});
		child.on("error", (e) => {
			clearInterval(beat);
			resolve(`(failed to start the ${phase} sub-agent: ${e.message})`);
		});
	});
}

/** Run pytest in the workspace with the project root on PYTHONPATH (matches the grader). */
function runTests(cwd: string): Promise<{ ok: boolean; tail: string }> {
	return new Promise((resolve) => {
		const child = spawn(PYTEST[0], PYTEST.slice(1), {
			cwd,
			env: { ...process.env, PYTHONPATH: cwd },
			stdio: ["ignore", "pipe", "pipe"],
		});
		let out = "";
		child.stdout.on("data", (c: Buffer) => (out += c.toString()));
		child.stderr.on("data", (c: Buffer) => (out += c.toString()));
		child.on("close", (code) => {
			const tail = out.split("\n").slice(-25).join("\n");
			resolve({ ok: code === 0, tail });
		});
		child.on("error", (e) => resolve({ ok: false, tail: `could not run pytest: ${e.message}` }));
	});
}

const textResult = (text: string, isError = false) => ({ content: [{ type: "text", text }], isError });

/** Turn a failed gate run into coder feedback for REVIEW.md, LABELLED so the model fixes the APP,
 * not the test. Two problems to avoid: (1) a bare pytest tail reads like "make these pass", which a
 * small model satisfies by EDITING the named test file — pointless, the harness restores the frozen
 * gate before grading; (2) the tail names `tests/test_gate_phase_N.py`, pointing the model straight
 * at the file to edit. So we prepend an explicit label ("your app failed; fix app.py/models.py;
 * never touch the tests") and strip the gate test-file PATHS, keeping the test NAME and the reason
 * (the behaviour that's wrong) but not a file to open. */
export function reviewFromTestFailure(tail: string): string {
	const behaviour = tail
		.replace(/\S*test_gate_phase_\d+\.py::/g, "") // drop "tests/test_gate_phase_5.py::", keep the test name
		.replace(/\S*test_gate_phase_\d+\.py\b/g, "the acceptance test"); // any bare file mention
	return (
		"=== YOUR APP FAILED THESE ACCEPTANCE CHECKS ===\n" +
		"These are behaviours your application got wrong. Fix the application code (app.py, models.py, " +
		"templates/) so they pass. Do NOT edit, weaken or delete any test — the harness restores the " +
		"frozen tests before grading, so changing a test is discarded and wasted effort.\n\n" +
		behaviour
	);
}

/** Read a file, or "" if it does not exist. Content flows through files, NOT tool arguments —
 * oMLX's tool-call parser drops a tool call whose JSON arguments are a large multi-line string,
 * so the orchestrator calls every tool with NO arguments and the tools read TASK.md / REVIEW.md. */
function readOr(path: string): string {
	try {
		return readFileSync(path, "utf8");
	} catch {
		return "";
	}
}

/** Trim a planner reply to the markdown plan: drop any preamble/code-fences before the first heading. */
export function asTodo(reply: string): string {
	let text = reply.replace(/```[a-z]*\n?/gi, "").trim();
	const lines = text.split("\n");
	const start = lines.findIndex((l) => l.trimStart().startsWith("#"));
	if (start > 0) text = lines.slice(start).join("\n");
	return text.trimEnd() + "\n";
}

/** Extract a Python file from an examiner reply: prefer a ```python block (the examiner sometimes
 * emits an HTML/template block FIRST, which a language-agnostic match would wrongly grab), then any
 * fenced block, then the raw text. */
export function asCode(reply: string): string {
	const py = reply.match(/```python\s*\n([\s\S]*?)```/i);
	const any = reply.match(/```[a-z]*\s*\n([\s\S]*?)```/i);
	const picked = py ? py[1] : any ? any[1] : reply;
	// Safety net: a model can emit a dangling fence (a trailing ``` with no opening, or an opening
	// ```python with no close), which neither regex above pairs, so the raw fence lands in the
	// frozen Python gate and `phase_gate_ok`'s compile() rejects a correct gate — the phase then
	// loops forever. Strip any line that is a lone fence marker; real Python never has one.
	const cleaned = picked.replace(/^[ \t]*```[a-z]*[ \t]*$\n?/gim, "");
	return noFollowRedirects(cleaned).trim() + "\n";
}

/** A gate's TestClient never follows redirects. The examiner is told to build it that way, but a
 * client that follows them turns every 3xx into the target's 200, so a gate asserting the spec's
 * redirect fails a correct app on every round (seen on a phase 4 gate). Plain GETs are unaffected,
 * and a call that passes follow_redirects itself keeps its own choice. */
export function noFollowRedirects(code: string): string {
	return code.replace(/TestClient\(([^()\n]+)\)/g, (call: string, args: string) =>
		/follow_redirects/.test(args) ? call : `TestClient(${args.trim()}, follow_redirects=False)`);
}

/** Is this reply actually a pytest file? It must define a test, and must not be HTML/template
 * leakage (the examiner once emitted a `templates/x.html` Jinja block as the "test"). */
export function looksLikePytest(code: string): boolean {
	if (!/(^|\n)\s*(async\s+)?def\s+test\w*\s*\(|(^|\n)\s*class\s+Test\w*/.test(code)) return false;
	if (/(^|\n)\s*<|\{%|\{\{|(^|\n)\S+\.(html|js|css|txt)\s*(\n|$)/m.test(code)) return false;
	return true;
}

/** The distinctive contract tokens a phase's spec NAMES — routes it declares, DB artifacts it names,
 *  status codes it pins. A gate that references all of them is a SUPERSET of the spec's named surface;
 *  one that drops some is a subset the coder can satisfy while the hidden grader still fails (measured:
 *  7/7 phase gates green, 26/34 hidden — see docs/superpowers/research/2026-10-27-proxy-oracle-gap.md).
 *  Agnostic: every token is read from the spec slice itself, NEVER from the hidden grader. Pure → tested. */
export function specCoverageTokens(slice: string): string[] {
	const toks = new Set<string>();
	// A route reduces to its distinctive leaf segment (len >= 4), so a gate that hits
	// `/complaints/1/archive` satisfies the spec's templated `/complaints/{id}/archive`.
	const leaf = (path: string): string | undefined => {
		const segs = path.replace(/\{[^}]*\}/g, "").split("/").filter(Boolean);
		for (let i = segs.length - 1; i >= 0; i--) if (segs[i].length >= 4) return segs[i];
		return undefined;
	};
	const add = (t?: string) => { if (t) toks.add(t); };
	for (const m of slice.matchAll(/`(\/[\w/{}-]+)`/g)) add(leaf(m[1]));           // `/route`
	for (const m of slice.matchAll(/\b(?:GET|POST|PUT|PATCH|DELETE)\s+(\/[\w/{}-]+)/g)) add(leaf(m[1])); // VERB /route
	for (const m of slice.matchAll(/[Nn]ame it\s+`([^`]+)`/g)) add(m[1]);          // Name it `migration`
	for (const m of slice.matchAll(/\b(?:index|view)\s+`([^`]+)`/g)) add(m[1]);    // index/view `name`
	for (const m of slice.matchAll(/`(\w+)`\s+column/g)) add(m[1]);                // `col` column
	for (const m of slice.matchAll(/(?:status|redirect[^\n.]{0,20}|returns?)\D{0,12}?\b(30[1-8]|4\d\d)\b/gi)) add(m[1]); // pinned 3xx/4xx
	return [...toks];
}

/** The spec tokens a gate text does NOT reference — the parts of the spec its acceptance test leaves
 *  uncovered. Case-insensitive substring presence: the gate need only MENTION the token, so the
 *  assertion form stays the examiner's call; this check only forbids ignoring a named requirement. */
export function missingGateCoverage(slice: string, gateText: string): string[] {
	const hay = gateText.toLowerCase();
	return specCoverageTokens(slice).filter((t) => !hay.includes(t.toLowerCase()));
}

/** Instruction appended to a re-examine when the gate misses named spec tokens. Spec-derived and
 *  concrete, so a fixed small model that ignored the standing "be exhaustive" prose gets told EXACTLY
 *  what to add — a harness guarantee, not another plea. */
export function coverageFeedback(missing: string[]): string {
	return (
		"\n\n=== YOUR ACCEPTANCE TEST IS INCOMPLETE ===\n" +
		"The spec NAMES these and your test does not reference them yet. Add a real assertion for EACH, " +
		"keeping every assertion you already have:\n" +
		missing.map((t) => ` - ${t}`).join("\n") +
		"\nFor a ROUTE word, exercise that route and assert its stated behaviour. For a named " +
		"migration/index/view/column, assert the artifact EXISTS and is applied/recorded (query it — not " +
		"merely that a function is defined). For a status code, assert the response status equals it " +
		"EXACTLY. Output ONLY the full pytest file, no prose, no fences."
	);
}

/** Concatenated text of every phase gate already frozen under plan/gate/ — the cumulative gate the
 *  coder will actually see, so a token covered by an earlier phase is not re-demanded here. */
export function frozenGateText(cwd: string): string {
	const gate = join(cwd, GATE_DIR);
	if (!existsSync(gate)) return "";
	return readdirSync(gate)
		.filter((f) => /^phase_\d+\.py$/.test(f))
		.map((f) => readFileSync(join(gate, f), "utf8"))
		.join("\n");
}

/** How many times examine is re-dispatched to cover spec tokens it missed. Small: examine is the
 *  largest thinking budget, and only phases with a gap retry at all. */
export const EXAMINE_COVERAGE_RETRIES = 2;

/** The frozen gate holds one acceptance test per phase; the current phase comes from MELLUM_PHASE. */
// Harness bookkeeping lives under plan/ so it never pollutes the solution tree (and a
// write-list check — e.g. the ladder's AgentClinic rule — can keep it out of grading).
export const PLAN_DIR = "plan";
export const GATE_DIR = "plan/gate";

/** Freeze filename for a phase inside the gate dir (phase_1.py, phase_2.py, …). */
export function freezeName(phase: string | number): string {
	const n = String(phase).replace(/[^0-9]/g, "") || "1";
	return `phase_${n}.py`;
}

/** The pytest filename a frozen phase is materialised to under tests/ (distinct per phase → accumulates). */
export function gateTestName(frozenStem: string): string {
	return `test_gate_${frozenStem}.py`;
}

/** Copy EVERY frozen phase into tests/ as a distinct pytest file, clearing stale ones first.
 * This is what makes the gate cumulative and tamper-proof: whatever the coder did to tests/,
 * the restored set is the union of every phase's frozen acceptance test. */
export function materializeGate(cwd: string): number {
	const gate = join(cwd, GATE_DIR);
	if (!existsSync(gate)) return 0;
	const tests = join(cwd, "tests");
	mkdirSync(tests, { recursive: true });
	for (const f of readdirSync(tests)) {
		if (/^test_gate_phase_.*\.py$/.test(f)) rmSync(join(tests, f));
	}
	const frozen = readdirSync(gate).filter((f) => /^phase_\d+\.py$/.test(f)).sort();
	for (const f of frozen) {
		writeFileSync(join(tests, gateTestName(f.replace(/\.py$/, ""))), readFileSync(join(gate, f), "utf8"));
	}
	return frozen.length;
}

/** Per-phase tool-call cap: a clean phase is ~6-10 calls (plan, review, examine, code, review, test,
 * plus a REDO or two). Past this the orchestrator is thrashing — a rung-6 flow run re-ran examine 5×
 * and review_code 3× and never called test, burning the whole deadline on a solution it already had. */
export const PHASE_CALL_CAP = 16;

/** The block decision for a phase tool call, given the running budget and whether this phase's gate
 * is already frozen. `test` and `read` are always allowed (test is the only exit). examine runs ONCE
 * per phase — the gate is its product, re-deriving it is pure waste. Returns a reason to block, or
 * undefined to allow. Pure, so it is unit-tested; the live hook supplies the counts and gate state. */
export function flowBlock(toolName: string, calls: number, gateExists: boolean, cap = PHASE_CALL_CAP): string | undefined {
	if (toolName === "test" || toolName === "read") return undefined;
	if (toolName === "examine" && gateExists)
		return "The acceptance test for this phase is already written and frozen. Do NOT examine again — call code() then test().";
	if (calls >= cap)
		return "Phase tool-call budget reached — you have planned, examined and coded enough. Call test() to check and finish; do not plan/examine/code/review_code again.";
	return undefined;
}

export default function (pi: any): void {
	const cwd = () => process.cwd();
	// TASK.md / TODO.md / REVIEW.md live under plan/, created on demand.
	const planPath = (name: string) => join(cwd(), PLAN_DIR, name);
	const ensurePlan = () => mkdirSync(join(cwd(), PLAN_DIR), { recursive: true });
	const hasTodo = () => existsSync(planPath("TODO.md"));
	const needTodo = "No TODO.md yet — call `plan` first, then `review_plan`, before coding.";

	// Cap the phase so the orchestrator can't loop to the deadline, and make examine run once:
	// re-deriving a frozen gate is the single biggest waste in a thrashing phase.
	let calls = 0;
	pi.on("tool_call", (event: { toolName?: string }) => {
		const name = event?.toolName ?? "";
		const gateExists = name === "examine"
			&& existsSync(join(cwd(), GATE_DIR, freezeName(process.env.MELLUM_PHASE ?? "1")));
		const reason = flowBlock(name, calls, gateExists);
		if (reason) return { block: true, reason };
		if (name !== "test" && name !== "read") calls += 1;
		return undefined;
	});

	pi.registerTool({
		name: "plan",
		label: "Plan",
		description:
			"Write TODO.md for this phase's task (read from TASK.md): a `## North Star` goal and a " +
			"checklist of every requirement. Takes NO arguments. Call this FIRST, and again to revise " +
			"the plan on REDO (it re-reads the reviewer feedback in REVIEW.md).",
		parameters: { type: "object", properties: {}, additionalProperties: false },
		async execute(_id: string, _params: any, signal: AbortSignal) {
			const task = readOr(planPath("TASK.md"));
			const fb = readOr(planPath("REVIEW.md"));
			const prompt = task + (fb ? `\n\n=== REVIEWER FEEDBACK — address every point ===\n${fb}` : "");
			const reply = await runSubagent("plan", prompt, cwd(), signal);
			const todo = asTodo(reply);
			// The harness writes TODO.md from the planner's reply, so a plan is ALWAYS persisted.
			ensurePlan();
			writeFileSync(planPath("TODO.md"), todo);
			return textResult(`TODO.md written (${todo.split("\n").length} lines).`);
		},
	});

	pi.registerTool({
		name: "review_plan",
		label: "Review plan",
		description: "Judge TODO.md for a clear North Star, completeness and simplicity. Returns REVIEW: PASS or REDO + reasons.",
		parameters: { type: "object", properties: {}, additionalProperties: false },
		async execute(_id: string, _params: any, signal: AbortSignal) {
			if (!hasTodo()) return textResult(needTodo, true);
			const verdict = await runSubagent("review_plan", "Review plan/TODO.md against the spec in plan/TASK.md (and specs/).", cwd(), signal);
			ensurePlan();
			writeFileSync(planPath("REVIEW.md"), verdict); // the next plan reads this
			// Fail OPEN: loop back to plan only on an explicit REVIEW: REDO. A thinking-model reviewer
			// that rambles or truncates before emitting "REVIEW: PASS" must not trap the pipeline in an
			// infinite plan↔review loop (it never reaches examine). The examiner's test + hidden grader
			// are the real gates; this review is advisory.
			return textResult(verdict.includes("REVIEW: REDO") ? "REVIEW: REDO (feedback saved for the next plan)." : "REVIEW: PASS");
		},
	});

	pi.registerTool({
		name: "examine",
		label: "Examine",
		description:
			"Write the acceptance test — the executable definition of DONE — from the spec in TASK.md. " +
			"Takes NO arguments. Call this AFTER review_plan and BEFORE code; the coder then builds to " +
			"pass it, and it joins the cumulative gate that test() runs (every earlier phase too).",
		parameters: { type: "object", properties: {}, additionalProperties: false },
		async execute(_id: string, _params: any, signal: AbortSignal) {
			const task = readOr(planPath("TASK.md"));
			let code = asCode(await runSubagent("examine", task, cwd(), signal));
			if (!looksLikePytest(code)) {
				// One corrective retry — a dropped or mis-formatted reply must not freeze a junk gate,
				// which would let the phase "pass" with no real test (and best-of-N would promote it).
				const fix = "\n\nYour previous reply was NOT a valid pytest file. Output ONLY the contents of a " +
					"Python pytest file — `def test_...` functions with assertions. No prose, no code fences, no HTML, no templates.";
				code = asCode(await runSubagent("examine", task + fix, cwd(), signal));
			}
			if (!looksLikePytest(code)) {
				return textResult("examine did not produce a valid pytest file — this phase has NO gate yet. Call examine again before code.", true);
			}
			// SPEC-COVERAGE GUARANTEE: the gate must at least REFERENCE every contract the spec names,
				// or it is a subset the coder can satisfy while the hidden grader fails. Re-dispatch the
				// examiner, naming the gaps, until covered or the budget is spent — keeping the best-covered
				// version. Agnostic: the tokens come from THIS phase's spec, never the grader.
				const earlier = frozenGateText(cwd());
				let missing = missingGateCoverage(task, earlier + code);
				for (let tries = 0; missing.length && tries < EXAMINE_COVERAGE_RETRIES; tries++) {
					feed(`    [examine] gate misses spec tokens: ${missing.join(", ")} — re-examining`);
					const next = asCode(await runSubagent("examine", task + coverageFeedback(missing), cwd(), signal));
					if (!looksLikePytest(next)) continue;
					const nextMissing = missingGateCoverage(task, earlier + next);
					if (nextMissing.length < missing.length) { code = next; missing = nextMissing; } // keep the best
				}
				if (missing.length) feed(`    [examine] residual uncovered spec tokens: ${missing.join(", ")}`);
				// Freeze THIS phase under its own name so the gate ACCUMULATES: a later phase can never
			// pass by regressing an earlier one, and the coder cannot weaken a gate it is told not to touch.
			const gate = join(cwd(), GATE_DIR);
			mkdirSync(gate, { recursive: true });
			writeFileSync(join(gate, freezeName(process.env.MELLUM_PHASE ?? "1")), code);
			const n = materializeGate(cwd()); // put this phase + every earlier phase into tests/ for the coder
			return textResult(`Acceptance test written (${code.split("\n").length} lines); gate now covers ${n} phase(s)${cover}. The coder must pass them ALL.`);
		},
	});

	pi.registerTool({
		name: "code",
		label: "Code",
		description:
			"Implement the plan in TODO.md (the coder writes/edits files and runs tests). Takes NO " +
			"arguments — it reads TODO.md, the spec in TASK.md, and any reviewer/test feedback in " +
			"REVIEW.md. Requires a plan to exist.",
		parameters: { type: "object", properties: {}, additionalProperties: false },
		async execute(_id: string, _params: any, signal: AbortSignal) {
			if (!hasTodo()) return textResult(needTodo, true);
			const fb = readOr(planPath("REVIEW.md"));
			const extra = fb ? `\n\n=== FEEDBACK TO ADDRESS ===\n${fb}` : "";
			return textResult(await runSubagent("code", `Implement plan/TODO.md (the spec is in plan/TASK.md).${extra}`, cwd(), signal));
		},
	});

	pi.registerTool({
		name: "review_code",
		label: "Review code",
		description: "Judge the code for conformance to the spec and simplicity. Returns REVIEW: PASS or REDO + reasons.",
		parameters: { type: "object", properties: {}, additionalProperties: false },
		async execute(_id: string, _params: any, signal: AbortSignal) {
			const verdict = await runSubagent("review_code", "Review the implementation against the spec in plan/TASK.md (and specs/).", cwd(), signal);
			ensurePlan();
			writeFileSync(planPath("REVIEW.md"), verdict); // the next code reads this
			// Fail OPEN (see review_plan): REDO only on an explicit REVIEW: REDO, so a lost/truncated
			// verdict can't trap the coder in an endless review loop. test() is the real code gate.
			return textResult(verdict.includes("REVIEW: REDO") ? "REVIEW: REDO (feedback saved for the next code)." : "REVIEW: PASS");
		},
	});

	pi.registerTool({
		name: "test",
		label: "Test",
		description: "Run the test suite (pytest) and report pass/fail with the output tail. Call after coding.",
		parameters: { type: "object", properties: {}, additionalProperties: false },
		async execute() {
			// Restore the WHOLE cumulative gate (every phase) so the coder cannot have weakened or
			// dropped any gate, and a regression in an earlier phase shows up here.
			materializeGate(cwd());
			const { ok, tail } = await runTests(cwd());
			// Feed the ACTUAL gate failure back to the coder. The next code() reads REVIEW.md, so a
			// failing run writes the labelled failure there — the coder sees what its APP did wrong and
			// can fix THAT, instead of re-building from the plan blind and repeating the same omission.
			// Env toggle so the feedback-vs-no-feedback comparison runs from ONE binary:
			// MELLUM_CODER_FEEDBACK=0 turns the loop OFF (the control arm). Default ON. On pass, leave
			// REVIEW.md alone.
			const feedbackOn = process.env.MELLUM_CODER_FEEDBACK !== "0";
			if (!ok && feedbackOn) {
				ensurePlan();
				writeFileSync(planPath("REVIEW.md"), reviewFromTestFailure(tail));
			}
			return textResult(`TESTS: ${ok ? "PASS" : "FAIL"}\n${tail}`, false);
		},
	});
}
