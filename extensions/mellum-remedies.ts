/**
 * mellum-remedies: switch remedy units on and off in a live Pi session.
 *
 * Every unit under remedies/<kind>/ is installed at session start behind its own switch, and all
 * start off, so the session is bare Pi until the learner turns something on:
 *
 *   /remedy                          a picker of every unit, marked on or off
 *   /remedy on guard/repeat-loops
 *   /remedy off guard/repeat-loops
 *   /remedy preset:easy              every unit in a preset
 *
 * A switch takes effect at the next tool call or request. A tool a unit adds is registered the
 * first time the unit is switched on; Pi cannot unregister a tool, so it stays offered after
 * `off` until the session restarts (its hooks do stop).
 */
import { spawn, type ChildProcess } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REMEDIES = join(dirname(fileURLToPath(import.meta.url)), "..", "remedies");
const KINDS = ["guard", "nudge", "context", "prompt", "tool", "check", "workflow"];

interface Unit {
	name: string;
	pathology: string;
	does: string;
}

/** A picker row: the on/off glyph, the unit name, and what it does — not the pathology it fixes. */
export function remedyRow(name: string, does: string, isOn: boolean): string {
	return `${isOn ? "●" : "○"} ${name}  ${does}`;
}

/** Every unit name under remedies/, in kind order. */
export function unitNames(): string[] {
	const names: string[] = [];
	for (const kind of KINDS) {
		let files: string[] = [];
		try {
			files = readdirSync(join(REMEDIES, kind)).filter((f) => f.endsWith(".ts")).sort();
		} catch {
			continue;
		}
		names.push(...files.map((f) => `${kind}/${f.replace(/\.ts$/, "")}`));
	}
	return names;
}

export function presetUnits(name: string): string[] | undefined {
	try {
		return JSON.parse(readFileSync(join(REMEDIES, "presets", `${name}.json`), "utf8"));
	} catch {
		return undefined;
	}
}

function presetNames(): string[] {
	try {
		return readdirSync(join(REMEDIES, "presets")).filter((f) => f.endsWith(".json")).map((f) => `preset:${f.replace(/\.json$/, "")}`).sort();
	} catch {
		return [];
	}
}

// ---- /challenge: run a tier with the remedies you have on, and score it --------------------

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const agentDir = () => process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent");
const CHALLENGE_RUNS = () => join(agentDir(), "mellum-challenge-runs.jsonl");
const TIERS = ["easy", "medium", "hard"];
const REPO = "andrevanzuydam/mellum-worker";
/** Challenge runs still going when the session ends are stopped with it, and their progress timers. */
const running = new Set<ChildProcess>();
const timers = new Set<ReturnType<typeof setInterval>>();

// The live challenge feed, shown in a pinned widget while a run is active (see runChallenge).
// A global flag lets the lesson panel step aside so the feed has the space.
type ChallengeFeed = {
	tier: string; label: string; runs: number;
	runsDone: number; turns: number; calls: string[]; started: number; thinking?: string;
	done?: { passed: number; total: number; rows: { passed: boolean; turns: number; wall: number }[] };
};
let challenge: ChallengeFeed | undefined;
let challengeRefresh: (() => void) | undefined;

/** The feed panel's lines: the header, then the live turns and tool calls, or the final score. */
export function renderFeed(c: ChallengeFeed, width: number, theme: any, truncate: (s: string, w: number) => string): string[] {
	const w = Math.max(20, width);
	const secs = Math.round((Date.now() - c.started) / 1000);
	const run = c.runs > 1 ? ` · run ${Math.min(c.runsDone + 1, c.runs)}/${c.runs}` : "";
	const lines = [
		theme.bold(theme.fg("accent", `▍ Challenge · ${c.tier} · ${c.label}${run}`)),
		theme.fg("dim", "─".repeat(w)),
	];
	if (c.done) {
		const ok = c.done.passed === c.done.total;
		lines.push(theme.fg(ok ? "success" : "warning", ` ${c.done.passed}/${c.done.total} passed · ${secs}s`));
		c.done.rows.forEach((r, i) => lines.push(theme.fg("dim",
			`  rep ${i + 1}: ${r.passed ? "pass" : "fail"} · ${r.turns} turns · ${Math.round(r.wall)}s`)));
		lines.push("", theme.fg("dim", " done · type to talk to the model"));
	} else {
		lines.push(theme.fg("dim", ` turn ${c.turns} · ${secs}s · the model is building…`));
		// The current turn's thinking, tail first, as two lines at most.
		if (c.thinking) {
			const cw = Math.max(10, w - 4);
			let t = c.thinking.length > cw * 2 ? `…${c.thinking.slice(-(cw * 2 - 1))}` : c.thinking;
			for (let i = 0, n = 0; i < t.length && n < 2; i += cw, n += 1)
				lines.push(theme.fg("muted", ` ${n === 0 ? "💭" : "  "} ${t.slice(i, i + cw)}`));
		}
		lines.push("");
		const feed = c.calls.slice(-8);
		if (!feed.length) lines.push(theme.fg("dim", "  waiting for the model’s first move…"));
		for (const call of feed) lines.push(` ${theme.fg("mdCode", call)}`);
	}
	return lines.map((l) => truncate(l, w));
}

/** Read the in-flight run: the newest trace, how many runs are done, the turn count, and each
 * tool call so far ("bash python app.py"), so the command can stream what the model is doing. */
function progress(runsDir: string): { trace: string; runsDone: number; turns: number; calls: string[]; thinking: string } {
	let subs: string[] = [];
	try {
		subs = readdirSync(runsDir);
	} catch {
		return { trace: "", runsDone: 0, turns: 0, calls: [], thinking: "" };
	}
	let runsDone = 0;
	let trace = "";
	let newestM = -1;
	for (const s of subs) {
		const d = join(runsDir, s);
		if (existsSync(join(d, "run.json"))) runsDone += 1;
		try {
			const m = statSync(join(d, "trace.jsonl")).mtimeMs;
			if (m > newestM) { newestM = m; trace = join(d, "trace.jsonl"); }
		} catch {
			// no trace yet
		}
	}
	let turns = 0;
	const calls: string[] = [];
	// The model's reasoning streams as reasoning_content deltas; keep the current turn's,
	// reset each provider_request, so the feed shows what it is thinking right now.
	let think = "";
	if (trace) {
		let txt = "";
		try {
			txt = readFileSync(trace, "utf8");
		} catch {
			return { trace, runsDone, turns, calls, thinking: "" };
		}
		for (const line of txt.split("\n")) {
			if (line.includes('"provider_request"')) {
				turns += 1;
				think = "";
			} else if (line.includes('"tool_call"')) {
				try {
					const ev = JSON.parse(line);
					if (ev.type !== "tool_call") continue;
					const input = typeof ev.input === "string" ? ev.input : JSON.stringify(ev.input ?? "");
					calls.push(`${ev.toolName ?? "?"} ${input.replace(/\s+/g, " ").slice(0, 56)}`);
				} catch {
					// a line still being written
				}
			} else if (line.includes('"reasoning_content"')) {
				const m = line.match(/"reasoning_content"\s*:\s*("(?:[^"\\]|\\.)*")/);
				if (m) { try { think += JSON.parse(m[1]); } catch { /* a partial line */ } }
			}
		}
	}
	return { trace, runsDone, turns, calls, thinking: think.replace(/\s+/g, " ").trim() };
}

export interface RunRow { passed: boolean; turns: number; wall: number; }
export interface Score { passed: number; total: number; turns: number; wall: number; rows: RunRow[]; }

/** Read every run.json under a harness runs dir: one row per run, plus passes/turns/wall totals. */
export function scoreRuns(dir: string): Score {
	const rows: RunRow[] = [];
	let names: string[] = [];
	try {
		names = readdirSync(dir);
	} catch {
		return { passed: 0, total: 0, turns: 0, wall: 0, rows };
	}
	for (const name of names) {
		let r: any;
		try {
			r = JSON.parse(readFileSync(join(dir, name, "run.json"), "utf8"));
		} catch {
			continue;
		}
		rows.push({ passed: !!r.passed, turns: Number(r.turns ?? r.requests ?? 0), wall: Number(r.wall ?? 0) });
	}
	return {
		passed: rows.filter((r) => r.passed).length,
		total: rows.length,
		turns: rows.reduce((a, r) => a + r.turns, 0),
		wall: rows.reduce((a, r) => a + r.wall, 0),
		rows,
	};
}

/** Append a scored challenge run, for /challenge submit to pick up later. A record never fails a run. */
function recordChallenge(rec: object): void {
	try {
		mkdirSync(agentDir(), { recursive: true });
		appendFileSync(CHALLENGE_RUNS(), JSON.stringify(rec) + "\n");
	} catch {
		// ignore
	}
}

/** Every recorded challenge run, newest last, for /challenge submit to pick from. */
function readRecords(): any[] {
	try {
		return readFileSync(CHALLENGE_RUNS(), "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
	} catch {
		return [];
	}
}

/** One line for the picker: tier, base (worker/vanilla) + remedy count, passes, turns, wall, when. */
function recordLabel(r: any, i: number): string {
	const date = String(r.at ?? "").replace("T", " ").slice(0, 16);
	const rem = r.remedies?.length ?? 0;
	const base = r.arm === "bare" ? "vanilla" : "worker";
	const stack = rem ? `${base}+${rem}` : base;
	return `${i + 1}. ${r.tier} · ${stack} · ${r.passed}/${r.total} · ${r.turns} turns · ${Math.round(r.wall)} s · ${date}`;
}

/** Run a command to completion, collecting stdout+stderr, never throwing. */
function sh(cmd: string, args: string[], cwd: string): Promise<{ code: number; out: string }> {
	return new Promise((resolve) => {
		const p = spawn(cmd, args, { cwd });
		let out = "";
		const keep = (b: Buffer) => { out += b.toString(); };
		p.stdout?.on("data", keep);
		p.stderr?.on("data", keep);
		p.on("error", (e) => resolve({ code: 1, out: String(e) }));
		p.on("close", (code) => resolve({ code: code ?? 0, out: out.trim() }));
	});
}

/** /challenge submit: pick recorded runs and open a pull request with their scores. */
async function submitChallenge(ctx: any): Promise<void> {
	if (!existsSync(join(ROOT, ".git"))) {
		return ctx.ui.notify("/challenge submit runs from a mellum-worker checkout", "error");
	}
	const recs = readRecords();
	if (!recs.length) {
		return ctx.ui.notify("no challenge runs recorded yet — run /challenge easy first, then submit", "info");
	}

	const chosen = new Set<number>();
	for (;;) {
		const opts = recs.map((r, i) => `${chosen.has(i) ? "●" : "○"} ${recordLabel(r, i)}`);
		opts.push(`✅ Submit ${chosen.size} run${chosen.size === 1 ? "" : "s"}`, "✕ Cancel");
		const pick = await ctx.ui.select("Challenge runs — toggle the ones to submit, then Submit", opts);
		if (!pick || pick.startsWith("✕")) return;
		if (pick.startsWith("✅")) {
			if (chosen.size) break;
			continue;
		}
		const idx = opts.indexOf(pick);
		if (idx >= 0 && idx < recs.length) chosen.has(idx) ? chosen.delete(idx) : chosen.add(idx);
	}
	const picked = [...chosen].sort((a, b) => a - b).map((i) => recs[i]);

	const confirm = await ctx.ui.select(`Open a pull request to ${REPO} with ${picked.length} run${picked.length === 1 ? "" : "s"}?`, ["Open PR", "Cancel"]);
	if (confirm !== "Open PR") return;
	ctx.ui.notify(`submitting ${picked.length} run${picked.length === 1 ? "" : "s"} to ${REPO}…`, "info");

	const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
	const dir = join(ROOT, "evals", "challenge");
	mkdirSync(dir, { recursive: true });
	const files = picked.map((r, k) => {
		const at = String(r.at ?? stamp).replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z").replace("T", "-");
		const rel = join("evals", "challenge", `${at}-${r.tier}-${k + 1}.json`);
		writeFileSync(join(ROOT, rel), JSON.stringify(r, null, 2) + "\n");
		return rel;
	});

	const branch = `challenge-submit-${stamp}`;
	const title = `challenge: submit ${picked.length} run${picked.length === 1 ? "" : "s"}`;
	const body = [
		"Challenge scores submitted from a live Pi with `/challenge submit`.",
		"",
		"| tier | passed | turns | wall (s) | remedies |",
		"| --- | --- | --- | --- | --- |",
		...picked.map((r) => `| ${r.tier} | ${r.passed}/${r.total} | ${r.turns} | ${Math.round(r.wall)} | ${(r.remedies ?? []).join(", ") || "none"} |`),
		"",
		"🤖 Generated with [Claude Code](https://claude.com/claude-code)",
	].join("\n");
	const bodyFile = join(tmpdir(), `${branch}.md`);
	writeFileSync(bodyFile, body);

	const owner = REPO.split("/")[0];
	const repoName = REPO.split("/")[1];
	const tail = (o: string) => o.split("\n").filter(Boolean).slice(-4).join("\n");
	const back = () => sh("git", ["checkout", "-"], ROOT);

	// The commit is local, so it always works; the branch name is unique per submit.
	for (const [cmd, args] of [["git", ["checkout", "-b", branch]], ["git", ["add", ...files]], ["git", ["commit", "-m", title]]] as [string, string[]][]) {
		const { code, out } = await sh(cmd, args, ROOT);
		if (code !== 0) { await back(); return ctx.ui.notify(`submit stopped at \`${cmd} ${args[0]}\`:\n${tail(out)}`, "error"); }
	}

	// Who is pushing? A contributor cannot push to the upstream repo, so they push to
	// their own fork (created here if they only cloned) and the PR comes from the fork.
	const who = await sh("gh", ["api", "user", "--jq", ".login"], ROOT);
	if (who.code !== 0) { await back(); return ctx.ui.notify("submit needs GitHub access — run `gh auth login`, then /challenge submit again.", "error"); }
	const login = who.out.trim();

	let head = branch;
	if (login && login !== owner) {
		// Idempotent: creates <login>/<repo> if missing, succeeds (0) when it already exists.
		const fork = await sh("gh", ["repo", "fork", REPO, "--clone=false", "--remote=false"], ROOT);
		if (fork.code !== 0) { await back(); return ctx.ui.notify(`submit could not prepare your fork of ${REPO}:\n${tail(fork.out)}`, "error"); }
		const push = await sh("git", ["push", `https://github.com/${login}/${repoName}.git`, `${branch}:${branch}`], ROOT);
		if (push.code !== 0) { await back(); return ctx.ui.notify(`submit could not push to your fork (${login}/${repoName}):\n${tail(push.out)}`, "error"); }
		head = `${login}:${branch}`;
	} else {
		const push = await sh("git", ["push", "-u", "origin", branch], ROOT);
		if (push.code !== 0) { await back(); return ctx.ui.notify(`submit could not push the branch:\n${tail(push.out)}`, "error"); }
	}

	// Open the PR from the branch (on the fork, or on the repo for the owner) to upstream main.
	const pr = await sh("gh", ["pr", "create", "--repo", REPO, "--base", "main", "--head", head, "--title", title, "--body-file", bodyFile], ROOT);
	await back();
	if (pr.code !== 0) return ctx.ui.notify(`submit pushed your runs but could not open the PR:\n${tail(pr.out)}\nOpen it by hand from ${login || "your fork"}.`, "error");
	const prUrl = pr.out.split("\n").find((l) => l.startsWith("http")) ?? pr.out.trim();
	ctx.ui.notify(`submitted ${picked.length} run${picked.length === 1 ? "" : "s"} — ${prUrl}`, "info");
}

/** Run a challenge tier through the harness `runs` times on `arm` with `units` loaded, score and record it. */
async function runChallenge(tier: string, units: string[], runs: number, arm: string, ctx: any): Promise<void> {
	if (!existsSync(join(ROOT, "learn", "code", "harness.py"))) {
		return ctx.ui.notify("/challenge runs from a mellum-worker checkout (no learn/code/harness.py here)", "error");
	}
	const runsDir = mkdtempSync(join(tmpdir(), `challenge-${tier}-`));
	// --arm worker turns the worker on (MELLUM_MODE=1); --arm bare is vanilla Pi. /remedy units stack on top.
	const argv = ["run", "python", "learn/code/harness.py", "run", "--suite", tier, "--arm", arm, "--grade", "--repeat", String(runs), "--runs-dir", runsDir];
	if (units.length) argv.push("--remedy", units.join(","));
	const base = arm === "worker" ? "worker" : "vanilla Pi";
	const on = `${base}${units.length ? ` + ${units.length} remed${units.length === 1 ? "y" : "ies"}` : ""}`;
	ctx.ui?.notify?.(`running the ${tier} challenge — ${on}, n=${runs} — a full suite on the real model, so give it a while.`, "info");

	// A live feed in a pinned panel, in place of the lesson panel while it runs. pi-tui resolves
	// only in the running Pi, so the truncate helper is loaded here, not imported at the top.
	const { truncateToWidth } = await import("@earendil-works/pi-tui");
	challenge = { tier, label: on, runs, runsDone: 0, turns: 0, calls: [], started: Date.now() };
	(globalThis as Record<string, unknown>).__mellumChallengeActive = true;
	ctx.ui?.setWidget?.("challenge", (tui: any, theme: any) => {
		challengeRefresh = () => tui.requestRender();
		return { render: (width: number) => challenge ? renderFeed(challenge, width, theme, truncateToWidth) : [] };
	});

	const child = spawn("uv", argv, { cwd: ROOT, stdio: ["ignore", "pipe", "pipe"] });
	running.add(child);
	let tail = "";
	const keep = (b: Buffer) => { tail = (tail + b.toString()).slice(-2000); };
	child.stdout?.on("data", keep);
	child.stderr?.on("data", keep);

	const tick = setInterval(() => {
		const { runsDone, turns, calls, thinking } = progress(runsDir);
		if (challenge) { challenge.runsDone = runsDone; challenge.turns = turns; challenge.calls = calls; challenge.thinking = thinking; }
		challengeRefresh?.();
		const where = runs > 1 ? `run ${Math.min(runsDone + 1, runs)}/${runs} ` : "";
		ctx.ui?.setStatus?.("challenge", `${tier}: ${where}turn ${turns}…`);
	}, 2000);
	timers.add(tick);

	const clearFeed = () => {
		(globalThis as Record<string, unknown>).__mellumChallengeActive = false;
		challenge = undefined;
		challengeRefresh = undefined;
		ctx.ui?.setWidget?.("challenge", undefined);
	};

	child.on("close", () => {
		clearInterval(tick);
		timers.delete(tick);
		ctx.ui?.setStatus?.("challenge", undefined);
		running.delete(child);
		const s = scoreRuns(runsDir);
		if (s.total === 0) {
			ctx.ui?.notify?.(`the ${tier} challenge produced no result:\n${tail.trim().split("\n").slice(-4).join("\n")}`, "error");
			return clearFeed();
		}
		const rows = s.rows.map((r) => ({ passed: r.passed, turns: r.turns, wall: Math.round(r.wall) }));
		recordChallenge({ tier, arm, remedies: units, runs, passed: s.passed, total: s.total, turns: s.turns, wall: Math.round(s.wall), rows, at: new Date().toISOString() });
		const head = `${tier} challenge · n=${runs} · ${on}`;
		const summary = `${s.passed}/${s.total} passed · ${s.turns} turns · ${Math.round(s.wall)} s wall`;
		const perRep = s.total > 1
			? s.rows.map((r, i) => `  rep ${i + 1}: ${r.passed ? "pass" : "fail"} · ${r.turns} turns · ${Math.round(r.wall)} s`)
			: [];
		ctx.ui?.notify?.([head, summary, ...perRep].join("\n"), s.passed === s.total ? "info" : "warning");
		// Hold the score on the feed for a moment, then clear it so the lesson panel returns.
		if (challenge) { challenge.done = { passed: s.passed, total: s.total, rows }; challengeRefresh?.(); }
		const hold = setTimeout(() => { clearFeed(); timers.delete(hold); }, 15000);
		timers.add(hold);
	});
}

/** A copy of `pi` whose hooks only run while `isOn()`, and whose tools wait for the first switch-on. */
function gated(pi: any, isOn: () => boolean, pendingTools: unknown[][]): any {
	return new Proxy(pi, {
		get(target, prop, receiver) {
			if (prop === "isRemedyEnabled") return isOn;
			if (prop === "on") {
				return (event: string, handler: (e: any, ctx?: any) => unknown, options?: { whileDisabled: boolean }) =>
					target.on(event, (e: any, ctx?: any) => (isOn() || options?.whileDisabled ? handler(e, ctx) : undefined));
			}
			if (prop === "registerTool") return (...args: unknown[]) => { pendingTools.push(args); };
			return Reflect.get(target, prop, receiver);
		},
	});
}

export default async function (pi: any): Promise<void> {
	const on = new Set<string>();
	const units: Unit[] = [];
	const pending = new Map<string, unknown[][]>();

	for (const name of unitNames()) {
		const mod = await import(pathToFileURL(join(REMEDIES, `${name}.ts`)).href);
		const tools: unknown[][] = [];
		pending.set(name, tools);
		mod.default(gated(pi, () => on.has(name), tools));
		units.push({ name, pathology: mod.meta?.pathology ?? "", does: mod.meta?.does ?? "" });
	}
	const known = new Set(units.map((u) => u.name));

	const refresh = (ctx: any) => ctx?.ui?.setStatus?.("remedies", on.size ? `remedies: ${on.size} on` : undefined);

	const switchOn = (name: string) => {
		on.add(name);
		for (const args of pending.get(name)?.splice(0) ?? []) pi.registerTool?.(...args);
	};

	const apply = (args: string, ctx: any): void => {
		const [verb, target] = args.includes(" ") ? args.trim().split(/\s+/, 2) : ["on", args.trim()];
		if (target.startsWith("preset:")) {
			const list = presetUnits(target.slice("preset:".length));
			if (!list) return ctx.ui.notify(`no ${target}; known: ${presetNames().join(", ")}`, "error");
			for (const name of list) verb === "off" ? on.delete(name) : switchOn(name);
			ctx.ui.notify(`${verb === "off" ? "off" : "on"}: ${target} (${list.length} units)`, "info");
			return refresh(ctx);
		}
		if (!known.has(target)) return ctx.ui.notify(`no remedy unit ${target}; type /remedy to pick one`, "error");
		if (verb === "off") on.delete(target);
		else switchOn(target);
		ctx.ui.notify(`${on.has(target) ? "on" : "off"}: ${target}`, "info");
		refresh(ctx);
	};

	// The picker: a live list of every unit with what it does, space toggles the highlighted one
	// on or off at once (the arrows can be claimed by the transcript, so j/k move too).
	const toggle = (name: string, ctx: any) => {
		if (on.has(name)) { on.delete(name); ctx.ui.notify?.(`off: ${name}`, "info"); }
		else { switchOn(name); ctx.ui.notify?.(`on: ${name}`, "info"); }
		refresh(ctx);
	};
	// pi-tui resolves only inside the running Pi process, not the repo, so it is loaded here
	// (the picker runs only in a live session) rather than imported at the top of the module.
	const pickRemedies = async (ctx: any): Promise<void> => {
		const { Key, matchesKey, truncateToWidth } = await import("@earendil-works/pi-tui");
		return ctx.ui.custom((tui: any, theme: any, _kb: unknown, done: (r: void) => void) => {
			let cursor = 0;
			function render(width: number): string[] {
				const w = Math.max(20, width);
				const lines = [
					theme.fg("accent", truncateToWidth(" Remedies — space toggles the highlighted unit", w)),
					theme.fg("dim", truncateToWidth(" j/k move   space toggle   enter/esc close", w)),
				];
				units.forEach((u, i) => {
					const row = remedyRow(u.name, u.does, on.has(u.name));
					lines.push(i === cursor ? theme.fg("accent", truncateToWidth(`›${row}`, w)) : theme.fg("dim", truncateToWidth(` ${row}`, w)));
				});
				return lines;
			}
			function handleInput(data: string) {
				if (matchesKey(data, Key.escape) || matchesKey(data, Key.enter)) return done();
				if (data === "k" || matchesKey(data, Key.up)) { cursor = Math.max(0, cursor - 1); tui.requestRender(); return; }
				if (data === "j" || matchesKey(data, Key.down)) { cursor = Math.min(units.length - 1, cursor + 1); tui.requestRender(); return; }
				if (data === " ") { toggle(units[cursor].name, ctx); tui.requestRender(); return; }
			}
			return { render, invalidate: () => {}, handleInput };
		});
	};

	pi.registerCommand("remedy", {
		description: "Switch remedy units on or off: /remedy, /remedy on <unit>, /remedy off <unit>, /remedy preset:<name>",
		getArgumentCompletions: (prefix: string) => {
			const choices = [
				...units.flatMap((u) => [`on ${u.name}`, `off ${u.name}`]),
				...presetNames(),
			];
			const items = choices.filter((c) => c.startsWith(prefix)).map((c) => ({ value: c, label: c }));
			return items.length ? items : null;
		},
		handler: async (args: string, ctx: any) => {
			if (args.trim()) return apply(args, ctx);
			await pickRemedies(ctx);
		},
	});

	pi.on?.("session_shutdown", () => {
		for (const c of running) c.kill();
		running.clear();
		for (const t of timers) clearInterval(t);
		timers.clear();
		(globalThis as Record<string, unknown>).__mellumChallengeActive = false;
		challenge = undefined;
		challengeRefresh = undefined;
	});

	pi.registerCommand("challenge", {
		description: "Run a challenge tier with the remedies you have on and score it (passes, turns, wall): /challenge easy|medium|hard [n=1]; /challenge submit opens a PR with the runs you choose",
		getArgumentCompletions: (prefix: string) => {
			const base = [...TIERS.flatMap((t) => [t, `${t} n=3`, `${t}:vanilla`]), "submit"];
			const items = base.filter((c) => c.startsWith(prefix)).map((c) => ({ value: c, label: c }));
			return items.length ? items : null;
		},
		handler: async (args: string, ctx: any) => {
			const toks = args.trim().split(/\s+/).filter(Boolean);
			if (toks[0] === "submit") return submitChallenge(ctx);
			const tierTok = toks.find((t) => /^(easy|medium|hard)(:vanilla)?$/.test(t));
			const nTok = toks.find((t) => /^n=\d+$/.test(t));
			const runs = nTok ? Math.max(1, Number(nTok.slice(2))) : 1;
			if (!tierTok) {
				return ctx.ui.notify(`/challenge easy|medium|hard [n=1] — runs that tier on the worker with the remedies you have on (${on.size} on now); add :vanilla (e.g. easy:vanilla) for bare Pi with no worker; n sets how many runs, default 1. /challenge submit opens a PR with the runs you choose`, "info");
			}
			const vanilla = tierTok.endsWith(":vanilla");
			const tier = vanilla ? tierTok.slice(0, -":vanilla".length) : tierTok;
			void runChallenge(tier, [...on], runs, vanilla ? "bare" : "worker", ctx)
				.catch((e) => ctx.ui?.notify?.(`challenge failed to start: ${(e as Error)?.message ?? e}`, "error"));
		},
	});
}
