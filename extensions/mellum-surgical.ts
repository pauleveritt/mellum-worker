/**
 * mellum-surgical: block a write that would clobber an existing file.
 *
 * The recorded pathology (LESSONS): a model asked to change three lines rewrites
 * the whole file (942 lines -> 2) under a write-only envelope, losing everything
 * it is not re-typing. Measured incidence on the current model is low — Pi's
 * `edit` anchors reliably — so this is a cheap safety net, not a hot path.
 *
 * On a `write` to a file that already exists, it measures the change against the
 * current content and blocks a regeneration: churn (what fraction of lines
 * changed — the clobber signal) and growth (a file that grew so much it must
 * hold a second copy). A write to a NEW file is always allowed — that is what
 * write is for. The block steers the worker to `edit` the targeted change.
 *
 * Churn is the clobber detector; growth stays generous so a legitimate addition
 * (a new route, a new field) is never mistaken for a rewrite. Caps are tunable
 * with MELLUM_SURGICAL (JSON). The churn/growth logic is the same primitive used
 * elsewhere to decide "surgical versus rewrite".
 */

import { existsSync, readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";

export interface Block {
	block: true;
	reason: string;
}

export interface Caps {
	maxChurn: number;
	maxGrowth: number;
}

const DEFAULTS: Caps = { maxChurn: 0.5, maxGrowth: 3 };

/** Lines after / lines before — above 1 means the file grew. */
export function growthRatio(before: string, after: string): number {
	const a = before.replace(/\r\n/g, "\n").split("\n").length;
	const b = after.replace(/\r\n/g, "\n").split("\n").length;
	return a === 0 ? 1 : b / a;
}

/** Fraction of lines that differ between before and after (added or removed), by set membership. */
export function churnFraction(before: string, after: string): number {
	const a = before.replace(/\r\n/g, "\n").split("\n");
	const b = after.replace(/\r\n/g, "\n").split("\n");
	if (!a.length && !b.length) return 0;
	const sa = new Set(a);
	const sb = new Set(b);
	const changed = b.filter((l) => !sa.has(l)).length + a.filter((l) => !sb.has(l)).length;
	return changed / Math.max(1, a.length + b.length);
}

/** Growth first (the more specific failure: a duplicated copy), then churn (a regeneration). */
export function capVerdict(before: string, after: string, caps: Caps): { ok: boolean; reason: string } {
	const growth = growthRatio(before, after);
	if (growth > caps.maxGrowth) {
		const pct = Math.round((growth - 1) * 100);
		return {
			ok: false,
			reason: `it made the file ${pct}% longer, which means it ADDED a second copy of something instead of changing the existing one`,
		};
	}
	const churn = churnFraction(before, after);
	if (churn > caps.maxChurn) {
		return {
			ok: false,
			reason: `it rewrote ${Math.round(churn * 100)}% of the file's lines, which is a regeneration, not a targeted change`,
		};
	}
	return { ok: true, reason: "" };
}

export type Reader = (path: string) => string | null;

function pathOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const record = input as Record<string, unknown>;
	for (const key of ["path", "filePath", "file_path"]) {
		if (typeof record[key] === "string") return record[key] as string;
	}
	return undefined;
}

function contentOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const value = (input as Record<string, unknown>).content;
	return typeof value === "string" ? value : undefined;
}

/** `write` onto an existing file is blocked when the change is a clobber; a new file is always fine. */
export function createSurgicalGuard(caps: Caps, read: Reader): (call: { toolName: string; input: unknown }) => Block | undefined {
	return (call) => {
		if (call.toolName !== "write") return undefined;
		const path = pathOf(call.input);
		if (!path) return undefined;
		const after = contentOf(call.input);
		if (typeof after !== "string") return undefined;
		let before: string | null;
		try {
			before = read(path);
		} catch {
			return undefined; // cannot read the current file: do not block on a read error
		}
		if (before == null) return undefined; // new file — write is the right tool
		const verdict = capVerdict(before, after, caps);
		if (verdict.ok) return undefined;
		return {
			block: true,
			reason:
				`[mellum-surgical] This write would clobber ${path}: ${verdict.reason}. ` +
				`Use edit to change only the lines that must change, reusing what is already there; ` +
				`write is for creating a new file.`,
		};
	};
}

/** MELLUM_SURGICAL (JSON) overrides the caps, e.g. {"maxChurn":0.8}. */
export function resolveCaps(env: string | undefined): Caps {
	if (!env) return { ...DEFAULTS };
	try {
		const parsed = JSON.parse(env);
		if (parsed && typeof parsed === "object") return { ...DEFAULTS, ...parsed };
	} catch {
		// fall through to defaults
	}
	return { ...DEFAULTS };
}

const defaultReader: Reader = (p) => {
	const file = isAbsolute(p) ? p : resolve(process.cwd(), p);
	return existsSync(file) ? readFileSync(file, "utf8") : null;
};

export default function (
	pi: { on: (event: string, handler: (event: any) => unknown) => void },
	options: { read?: Reader } = {},
): void {
	const caps = resolveCaps(process.env.MELLUM_SURGICAL);
	const read = options.read ?? defaultReader;
	const guard = createSurgicalGuard(caps, read);
	pi.on("tool_call", (event) => guard(event));
}
