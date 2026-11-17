/**
 * mellum-rethink — a skeptical "stop and pause, rethink" gate (a Pi extension;
 * agnostic, like the feed, the gate, replay, control and context).
 *
 * The human can be wrong, or lying. If the worker is told "the tests already
 * pass" or "I already fixed app.py" and the ground truth disagrees, a trusting
 * worker encodes the false premise. This parses the claims a human makes in the
 * task, checks the cheap, checkable ones against ground truth, and when a claim
 * contradicts what is actually there it pushes back: it sends the worker a
 * skeptical note naming the contradiction and asks it to re-examine before
 * continuing, rather than taking the claim on faith.
 *
 * Ground truth comes from a probe the wiring supplies — does the acceptance
 * test actually pass, which files actually changed. The pure core (parse +
 * check + message) carries no I/O and is unit-tested.
 *
 * Each contradiction is also written to the feed (kind "rethink"), so the
 * dashboard intelligence centre can show told-vs-truth side by side.
 *
 * Self-contained: Node `fs`/`child_process` + Pi hooks; loads with `-e` or
 * `--pi-extension`.
 */
import { appendFileSync, mkdirSync, existsSync, statSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";

export interface Claims {
	testsClaimedPassing: boolean;
	filesClaimedChanged: string[];
}

export interface Truth {
	testsPass?: boolean;
	changedFiles?: string[];
}

export interface Contradiction {
	claim: string;
	observed: string;
}

const FILE = /[\w./-]+\.(?:py|js|ts|mjs|md|json|txt|html|css|sql)\b/gi;

/** Pull the cheap, checkable claims out of a human message. */
export function parseClaims(text: string): Claims {
	const t = text || "";
	const testsClaimedPassing =
		/\b(all|the)?\s*tests?\b[^.]*\b(already\s+)?(pass(es|ing|ed)?|green|succeed(s|ing)?)\b/i.test(t) ||
		/\b(everything|it all)\s+(passes|works|is green)\b/i.test(t);
	const filesClaimedChanged: string[] = [];
	// "I already fixed/changed/updated/wrote X" — a change verb in the same clause
	// just before the filename. Scanning the clause (not a naive sentence split)
	// avoids breaking on the dot inside "app.py".
	const changeVerb = /\b(already\s+)?(fixed|changed|updated|wrote|edited|implemented|done|handled)\b/i;
	for (const m of t.matchAll(FILE)) {
		const before = t.slice(Math.max(0, (m.index ?? 0) - 80), m.index);
		const clause = before.split(/[.!?\n]\s/).pop() ?? "";
		if (changeVerb.test(clause) && !filesClaimedChanged.includes(m[0])) {
			filesClaimedChanged.push(m[0]);
		}
	}
	return { testsClaimedPassing, filesClaimedChanged };
}

/** Claims that the ground truth contradicts — the lies worth pushing back on. */
export function findContradictions(claims: Claims, truth: Truth): Contradiction[] {
	const out: Contradiction[] = [];
	if (claims.testsClaimedPassing && truth.testsPass === false) {
		out.push({ claim: "the tests already pass", observed: "the acceptance test is failing" });
	}
	const changed = new Set(truth.changedFiles ?? []);
	if (truth.changedFiles) {
		for (const f of claims.filesClaimedChanged) {
			if (!changed.has(f)) {
				out.push({ claim: `${f} was already changed`, observed: `${f} is unchanged on disk` });
			}
		}
	}
	return out;
}

/** The skeptical push-back the worker is sent; empty when nothing is contradicted. */
export function rethinkMessage(cons: Contradiction[]): string {
	if (cons.length === 0) return "";
	const lines = cons.map((c) => `• You were told: ${c.claim}. But ${c.observed}.`);
	return (
		"Stop and rethink. A claim in the task does not match the ground truth:\n" +
		lines.join("\n") +
		"\nDo not take the claim on faith. Re-examine the actual files and test result, " +
		"then continue from what is actually true."
	);
}

function feedPath(): string {
	return process.env.MELLUM_FEED || `${process.env.HOME || homedir()}/.pi/agent/mellum-feed.ndjson`;
}

function writeFeed(cons: Contradiction[]): void {
	if (cons.length === 0) return;
	try {
		const path = feedPath();
		mkdirSync(dirname(path), { recursive: true });
		for (const c of cons) {
			appendFileSync(path, JSON.stringify({ t: Date.now(), kind: "rethink", ...c }) + "\n");
		}
	} catch {
		// best-effort
	}
}

/** Ground truth from the environment: does the acceptance test pass, what changed. */
function probeTruth(): Truth {
	const truth: Truth = {};
	const test = process.env.RETHINK_TEST;
	if (test && existsSync(resolve(test))) {
		const pytest = (process.env.RETHINK_PYTEST || "uv run --offline python -m pytest -q").split(/\s+/);
		const r = spawnSync(pytest[0], [...pytest.slice(1), test], { encoding: "utf8", timeout: 300_000 });
		truth.testsPass = r.status === 0;
	}
	// Files claimed changed are checked lazily in the hook (needs the claimed paths).
	return truth;
}

/** A file "changed" = it exists and was modified since the run began. */
function changedSince(paths: string[], startedAt: number): string[] {
	return paths.filter((p) => {
		try {
			return existsSync(resolve(p)) && statSync(resolve(p)).mtimeMs >= startedAt;
		} catch {
			return false;
		}
	});
}

export default function (pi: any) {
	const startedAt = Date.now();
	let pending = "";

	const examine = (text: string) => {
		const claims = parseClaims(text || "");
		const truth = probeTruth();
		if (claims.filesClaimedChanged.length) {
			truth.changedFiles = changedSince(claims.filesClaimedChanged, startedAt);
		}
		const cons = findContradictions(claims, truth);
		if (cons.length) {
			writeFeed(cons);
			pending = rethinkMessage(cons);
		}
	};

	// Read the human's claims as they arrive.
	pi.on("context", (event: any) => {
		const msgs = event?.messages;
		if (Array.isArray(msgs)) {
			const last = [...msgs].reverse().find((m) => m?.role === "user" || m?.role === "custom");
			const content = last?.content;
			const text = typeof content === "string"
				? content
				: Array.isArray(content)
					? content.filter((b: any) => b?.type === "text").map((b: any) => b.text).join(" ")
					: "";
			if (text) examine(text);
		}
		return undefined;
	});

	// Push back before the worker settles on a false premise.
	pi.on("agent_before_settle", (_event: any, ctx: any) => {
		if (pending) {
			const note = pending;
			pending = "";
			ctx?.ui?.notify?.("mellum-rethink: contradiction found — pushing back", "warning");
			return { continue: true, message: note };
		}
		return undefined;
	});
}
