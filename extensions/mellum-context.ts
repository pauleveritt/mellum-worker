/**
 * mellum-context — context intelligence over a local SQLite FTS5 index (a Pi
 * extension; agnostic, like the feed, the gate, replay and control).
 *
 * Large code projects and large data files do not fit in a prompt. This indexes
 * files into an on-disk SQLite full-text index (FTS5) and ranks passages by
 * BM25 with a recency boost, so the worker searches for the handful of relevant
 * lines instead of loading the whole file into context. The index is the thing
 * leaned on; the model reads only what the search returns.
 *
 *   /index <path> [<path> ...]   chunk and index each file (re-indexing replaces)
 *   /context <query>             the top passages for a query, as doc:line refs
 *
 * If Pi exposes `registerTool`, a `context_search` tool is also registered so
 * the model can search the index itself mid-run.
 *
 * Self-contained: Node `fs` + `node:sqlite` (built in, no npm dep) + Pi hooks;
 * loads with `-e extensions/mellum-context.ts` or the ladder's `--pi-extension`.
 */
import { DatabaseSync } from "node:sqlite";
import { readFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";

export interface Chunk {
	startLine: number;
	endLine: number;
	body: string;
}

export interface Hit {
	doc: string;
	startLine: number;
	endLine: number;
	body: string;
	bm25: number;
	score: number;
	ts: number;
}

/** Split text into line-windows of `size` lines that overlap by `overlap`. */
export function chunkLines(text: string, size = 40, overlap = 5): Chunk[] {
	const lines = text.split("\n");
	if (lines.length && lines[lines.length - 1] === "") lines.pop();
	if (lines.length === 0 || lines.every((l) => l.trim() === "")) return [];
	const step = Math.max(1, size - overlap);
	const chunks: Chunk[] = [];
	for (let i = 0; i < lines.length; i += step) {
		const slice = lines.slice(i, i + size);
		chunks.push({ startLine: i + 1, endLine: i + slice.length, body: slice.join("\n") });
		if (i + size >= lines.length) break;
	}
	return chunks;
}

/**
 * Rank key for a hit: smaller is better, matching `ORDER BY score`. BM25 from
 * SQLite is negative and more-negative means more relevant. A recency term in
 * (0, 1] — 1 for a just-indexed chunk, halving every `halfLifeMs` — is
 * subtracted, so a fresh chunk outranks a stale one of equal relevance.
 */
export function rankScore(bm25: number, ageMs: number, halfLifeMs: number): number {
	if (!(halfLifeMs > 0)) return bm25;
	const recency = Math.pow(0.5, Math.max(0, ageMs) / halfLifeMs);
	return bm25 - recency;
}

/** A single FTS5 token; keeps bareword and quoted-phrase queries from erroring. */
export function sanitizeQuery(query: string): string {
	const terms = (query || "").match(/[\p{L}\p{N}_]+/gu) || [];
	if (terms.length === 0) return '""';
	return terms.map((t) => `"${t}"`).join(" OR ");
}

/** Open (creating if needed) the FTS5 index at `dbPath`. */
export function openIndex(dbPath: string): DatabaseSync {
	if (dbPath !== ":memory:") mkdirSync(dirname(dbPath), { recursive: true });
	const db = new DatabaseSync(dbPath);
	db.exec(
		"CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(" +
			"body, doc UNINDEXED, start_line UNINDEXED, end_line UNINDEXED, ts UNINDEXED)",
	);
	return db;
}

/** Replace every chunk of `doc` with fresh chunks of `text`; returns the count. */
export function indexDoc(
	db: DatabaseSync,
	doc: string,
	text: string,
	opts: { size?: number; overlap?: number; ts?: number } = {},
): number {
	const ts = opts.ts ?? Date.now();
	db.prepare("DELETE FROM chunks WHERE doc = ?").run(doc);
	const insert = db.prepare(
		"INSERT INTO chunks(body, doc, start_line, end_line, ts) VALUES(?, ?, ?, ?, ?)",
	);
	const chunks = chunkLines(text, opts.size, opts.overlap);
	for (const c of chunks) insert.run(c.body, doc, c.startLine, c.endLine, ts);
	return chunks.length;
}

/**
 * Order hits chronologically: oldest first by default (the order events
 * happened), newest first when `newestFirst`. Ties within a timestamp fall back
 * to doc then start line, so a single file reads top to bottom.
 */
export function sortChronologically(hits: Hit[], newestFirst = false): Hit[] {
	const dir = newestFirst ? -1 : 1;
	return [...hits].sort(
		(a, b) =>
			dir * (a.ts - b.ts) || a.doc.localeCompare(b.doc) || a.startLine - b.startLine,
	);
}

/**
 * Top passages for a query. Candidates are drawn by BM25; `order` decides how
 * the kept passages are arranged:
 *   "score" (default) — relevance with a recency boost (temporal ranking)
 *   "time"            — the most relevant candidates, then placed in
 *                        chronological order (temporal sequencing), so the
 *                        worker applies context in the order it occurred
 */
export function search(
	db: DatabaseSync,
	query: string,
	opts: {
		limit?: number;
		halfLifeMs?: number;
		now?: number;
		order?: "score" | "time";
		newestFirst?: boolean;
	} = {},
): Hit[] {
	const limit = opts.limit ?? 5;
	const halfLifeMs = opts.halfLifeMs ?? 0;
	const now = opts.now ?? Date.now();
	const rows = db
		.prepare(
			"SELECT body, doc, start_line, end_line, ts, bm25(chunks) AS bm25 " +
				"FROM chunks WHERE chunks MATCH ? ORDER BY bm25 LIMIT ?",
		)
		.all(sanitizeQuery(query), Math.max(limit * 4, limit)) as any[];
	const hits: Hit[] = rows
		.map((r) => ({
			doc: String(r.doc),
			startLine: Number(r.start_line),
			endLine: Number(r.end_line),
			body: String(r.body),
			bm25: Number(r.bm25),
			ts: Number(r.ts),
			score: rankScore(Number(r.bm25), now - Number(r.ts), halfLifeMs),
		}))
		.sort((a, b) => a.score - b.score)
		.slice(0, limit);
	return opts.order === "time" ? sortChronologically(hits, opts.newestFirst) : hits;
}

/** A compact, model-readable rendering of search hits. */
export function renderHits(hits: Hit[]): string {
	if (hits.length === 0) return "mellum-context: no matching passages indexed";
	return hits
		.map((h) => `• ${h.doc}:${h.startLine}-${h.endLine}\n${h.body}`)
		.join("\n\n");
}

function dbPath(): string {
	return process.env.MELLUM_CONTEXT_DB || `${process.env.HOME || homedir()}/.pi/agent/mellum-context.db`;
}

function halfLifeMs(): number {
	const v = Number(process.env.MELLUM_CONTEXT_HALFLIFE_MS);
	return Number.isFinite(v) && v > 0 ? v : 0;
}

export default function (pi: any) {
	const open = () => openIndex(dbPath());

	pi.registerCommand?.("index", {
		description: "chunk and index files into the context store (re-indexing a file replaces it)",
		handler: async (args: string, ctx: any) => {
			const paths = (args || "").split(/\s+/).filter(Boolean);
			if (paths.length === 0) {
				ctx?.ui?.notify?.("mellum-context: /index <path> [<path> ...]", "warning");
				return;
			}
			const db = open();
			let total = 0;
			for (const p of paths) {
				try {
					const abs = resolve(p);
					total += indexDoc(db, p, readFileSync(abs, "utf8"));
				} catch (e: any) {
					ctx?.ui?.notify?.(`mellum-context: cannot index ${p}: ${e?.message}`, "warning");
				}
			}
			db.close();
			ctx?.ui?.notify?.(`mellum-context: indexed ${total} chunks from ${paths.length} file(s)`, "info");
		},
	});

	pi.registerCommand?.("context", {
		description: "search the context store; prints the top passages as doc:line refs",
		handler: async (args: string, ctx: any) => {
			const db = open();
			const hits = search(db, args || "", { halfLifeMs: halfLifeMs() });
			db.close();
			ctx?.ui?.notify?.(renderHits(hits), "info");
		},
	});

	// If Pi supports model-callable tools, let the worker search the index itself.
	pi.registerTool?.("context_search", {
		description:
			"Search the indexed context store for the passages most relevant to a query. " +
			"Use this instead of reading a whole large file; returns doc:line refs with text.",
		parameters: {
			type: "object",
			properties: { query: { type: "string" }, limit: { type: "number" } },
			required: ["query"],
		},
		handler: async (input: { query: string; limit?: number }) => {
			const db = open();
			const hits = search(db, input?.query || "", { limit: input?.limit ?? 5, halfLifeMs: halfLifeMs() });
			db.close();
			return renderHits(hits);
		},
	});
}
