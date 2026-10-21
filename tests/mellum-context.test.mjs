import { test } from "node:test";
import assert from "node:assert/strict";

import {
	chunkLines,
	rankScore,
	sanitizeQuery,
	openIndex,
	indexDoc,
	search,
	sortChronologically,
	renderHits,
} from "../extensions/mellum-context.ts";

test("chunkLines: overlapping line windows cover every line", () => {
	const text = Array.from({ length: 10 }, (_, i) => `line ${i + 1}`).join("\n");
	const chunks = chunkLines(text, 4, 1);
	assert.equal(chunks[0].startLine, 1);
	assert.equal(chunks[0].endLine, 4);
	// step = size - overlap = 3, so the next window starts at line 4 (overlap of 1)
	assert.equal(chunks[1].startLine, 4);
	assert.equal(chunks[chunks.length - 1].endLine, 10);
	assert.match(chunks[0].body, /line 1\nline 2/);
});

test("chunkLines: empty text yields no chunks", () => {
	assert.deepEqual(chunkLines("", 4, 1), []);
	assert.deepEqual(chunkLines("\n\n", 4, 1), []);
});

test("rankScore: more-relevant (more-negative bm25) ranks first", () => {
	assert.ok(rankScore(-3, 0, 1000) < rankScore(-2, 0, 1000));
});

test("rankScore: for equal relevance, a fresher chunk ranks first", () => {
	const fresh = rankScore(-2, 0, 1000);
	const stale = rankScore(-2, 5000, 1000);
	assert.ok(fresh < stale);
});

test("rankScore: half-life <= 0 ignores recency entirely", () => {
	assert.equal(rankScore(-2, 0, 0), -2);
	assert.equal(rankScore(-2, 999999, 0), -2);
});

test("sanitizeQuery: barewords become an OR of quoted tokens; empty is a safe no-match", () => {
	assert.equal(sanitizeQuery("sum columns"), '"sum" OR "columns"');
	assert.equal(sanitizeQuery("  "), '""');
	// punctuation that would otherwise be FTS5 syntax is stripped
	assert.equal(sanitizeQuery('col1 + col2 "'), '"col1" OR "col2"');
});

test("indexDoc + search: finds the passage and returns its doc:line ref", () => {
	const db = openIndex(":memory:");
	indexDoc(db, "app.py", "def home():\n    return 'board'\n\ndef sum_columns():\n    return totals\n", { size: 2, overlap: 0 });
	indexDoc(db, "readme.md", "install instructions and licence text\n", { size: 2, overlap: 0 });
	const hits = search(db, "sum_columns", { limit: 1 });
	assert.equal(hits.length, 1);
	assert.equal(hits[0].doc, "app.py");
	assert.match(hits[0].body, /sum_columns/);
	db.close();
});

test("indexDoc: re-indexing a doc replaces its old chunks (no duplicates)", () => {
	const db = openIndex(":memory:");
	indexDoc(db, "a.txt", "alpha beta\n", { size: 1, overlap: 0 });
	indexDoc(db, "a.txt", "gamma delta\n", { size: 1, overlap: 0 });
	assert.equal(search(db, "alpha", { limit: 5 }).length, 0);
	assert.equal(search(db, "gamma", { limit: 5 }).length, 1);
	db.close();
});

test("search: with a half-life, the fresher of two equally-relevant docs wins", () => {
	const db = openIndex(":memory:");
	const now = 1_000_000;
	indexDoc(db, "old.txt", "needle\n", { size: 1, overlap: 0, ts: now - 60_000 });
	indexDoc(db, "new.txt", "needle\n", { size: 1, overlap: 0, ts: now });
	const hits = search(db, "needle", { limit: 2, halfLifeMs: 10_000, now });
	assert.equal(hits[0].doc, "new.txt");
	db.close();
});

test("sortChronologically: oldest-first by default, newest-first on request", () => {
	const mk = (doc, ts) => ({ doc, startLine: 1, endLine: 1, body: "", bm25: -1, score: -1, ts });
	const hits = [mk("c", 30), mk("a", 10), mk("b", 20)];
	assert.deepEqual(sortChronologically(hits).map((h) => h.doc), ["a", "b", "c"]);
	assert.deepEqual(sortChronologically(hits, true).map((h) => h.doc), ["c", "b", "a"]);
});

test("search order 'time': most-relevant candidates, then placed in chronological order", () => {
	const db = openIndex(":memory:");
	const now = 1_000_000;
	indexDoc(db, "third.txt", "needle later\n", { size: 1, overlap: 0, ts: now });
	indexDoc(db, "first.txt", "needle early\n", { size: 1, overlap: 0, ts: now - 2000 });
	indexDoc(db, "second.txt", "needle mid\n", { size: 1, overlap: 0, ts: now - 1000 });
	const hits = search(db, "needle", { limit: 3, order: "time", now });
	assert.deepEqual(hits.map((h) => h.doc), ["first.txt", "second.txt", "third.txt"]);
	db.close();
});

test("renderHits: empty hits say so; populated hits carry doc:line refs", () => {
	assert.match(renderHits([]), /no matching passages/);
	const out = renderHits([{ doc: "x.py", startLine: 3, endLine: 9, body: "code", bm25: -1, score: -1, ts: 0 }]);
	assert.match(out, /x\.py:3-9/);
});
