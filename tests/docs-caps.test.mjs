import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

// The caps in docs/sdd.md, enforced. Over cap means a research doc is owed.
const ROOT = resolve(import.meta.dirname, "..");
const read = (p) => readFileSync(resolve(ROOT, p), "utf8");
const lines = (s) => s.split("\n").length;

test("ROADMAP.md is at most 400 lines", () => {
	assert.ok(lines(read("ROADMAP.md")) <= 400);
});

// A row is a pointer: the detail lives in the spec, plan, record or research note it links.
// Lowered from 900/900/1,000 on 2026-11-07, when old rows had grown into reports.
const CELL = { ships: 400, excludes: 250, status: 300 };

test("roadmap cells: Ships at most 400 chars, Excludes 250, Status 300", () => {
	const rows = read("ROADMAP.md").split("\n").filter((l) => /^\| \*\*/.test(l));
	assert.ok(rows.length > 0, "no feature-cycle rows found");
	for (const row of rows) {
		const [, cycle, ships, excludes, status] = row.split("|").map((c) => c.trim());
		assert.ok(ships.length <= CELL.ships, `${cycle} Ships cell is ${ships.length} chars`);
		assert.ok(excludes.length <= CELL.excludes, `${cycle} Excludes cell is ${excludes.length} chars`);
		assert.ok(status.length <= CELL.status, `${cycle} Status cell is ${status.length} chars`);
	}
});

test("a closed or superseded roadmap row links to where its detail lives", () => {
	const rows = read("ROADMAP.md").split("\n").filter((l) => /^\| \*\*/.test(l));
	for (const row of rows) {
		const [, cycle, , , status] = row.split("|").map((c) => c.trim());
		if (/^(closed|superseded)\b/.test(status)) assert.match(status, /\]\(/, `${cycle} Status has no link`);
	}
});

test("backlog entries are at most 1,200 chars and each states a reopen condition", () => {
	const body = read("BACKLOG.md").split("Reopen conditions, not promises.")[1] ?? "";
	const entries = body.split(/\n\n(?=\*\*)/).map((e) => e.trim()).filter(Boolean);
	assert.ok(entries.length > 0, "no backlog entries found");
	for (const e of entries) {
		const title = e.match(/^\*\*(.+?)\*\*/)?.[1] ?? e.slice(0, 40);
		assert.ok(e.length <= 1200, `backlog entry "${title}" is ${e.length} chars`);
		assert.match(e, /\*Reopens when\*/, `backlog entry "${title}" has no reopen condition`);
	}
});

test("plans are at most 400 lines and at most 25% fenced; specs at most 400 lines", () => {
	const dir = (p) => (existsSync(resolve(ROOT, p)) ? readdirSync(resolve(ROOT, p)).filter((f) => f.endsWith(".md")) : []);
	for (const f of dir("docs/superpowers/plans")) {
		const text = read(`docs/superpowers/plans/${f}`);
		const n = lines(text);
		assert.ok(n <= 400, `plan ${f} is ${n} lines`);
		let fenced = 0, inFence = false;
		for (const l of text.split("\n")) {
			if (l.startsWith("```")) { inFence = !inFence; continue; }
			if (inFence) fenced += 1;
		}
		assert.ok(fenced / n <= 0.25, `plan ${f} is ${Math.round((100 * fenced) / n)}% fenced`);
	}
	for (const f of dir("docs/superpowers/specs")) {
		const n = lines(read(`docs/superpowers/specs/${f}`));
		assert.ok(n <= 400, `spec ${f} is ${n} lines`);
	}
});

test("the roadmap trifecta: ROADMAP.md, BACKLOG.md and ARCHIVE.md, and no per-phase roadmap file", () => {
	for (const f of ["ROADMAP.md", "BACKLOG.md", "ARCHIVE.md"]) assert.ok(existsSync(resolve(ROOT, f)), `${f} is missing`);
	const extra = readdirSync(ROOT).filter((f) => /^ROADMAP-.+\.md$/.test(f));
	assert.deepEqual(extra, [], "closed phases go in ARCHIVE.md, not a ROADMAP-<phase>.md");
});

// From 2026-11-07 (the re-boot) every spec, plan and research note is short and carries the
// three sections a reader (Andre) looks for first. Earlier documents keep the 400-line caps above.
const SHAPE_FROM = "2026-11-07";
const SHAPE = { specs: 100, plans: 150, research: 150 };
const SECTIONS = [/^For Andre$/, /^Ladder run$/, /^Persuasion (→|->) enforcement$/];
// Andre's own notes, merged from origin/main, are written in his shape, not for him to read.
const SHAPE_EXEMPT = new Set([
	"research/2026-11-07-request-metric-and-architect-direct-on-easy.md",
]);

function documentSections(text) {
	const sections = [];
	let current = null, fence = null;
	const content = text.replace(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/, "");
	for (const line of content.split(/\r?\n/)) {
		const marker = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
		if (fence) {
			if (marker && marker[1][0] === fence[0] && marker[1].length >= fence.length && !marker[2].trim()) fence = null;
			continue;
		}
		if (marker) { fence = marker[1]; continue; }
		const heading = line.match(/^## (.+?)(?: +#+)?\s*$/);
		if (heading) {
			current = { title: heading[1], body: [] };
			sections.push(current);
		} else if (current) current.body.push(line);
	}
	return sections;
}

test("documents from the re-boot on are short and carry For Andre, Ladder run and Persuasion → enforcement", () => {
	for (const [kind, cap] of Object.entries(SHAPE)) {
		const dir = `docs/superpowers/${kind}`;
		if (!existsSync(resolve(ROOT, dir))) continue;
		for (const f of readdirSync(resolve(ROOT, dir)).filter((f) => f.endsWith(".md") && f.slice(0, 10) >= SHAPE_FROM && !SHAPE_EXEMPT.has(`${kind}/${f}`))) {
			const text = read(`${dir}/${f}`);
			assert.ok(lines(text) <= cap, `${kind} ${f} is ${lines(text)} lines (cap ${cap})`);
			const sections = documentSections(text);
			assert.equal(sections[0]?.title, "For Andre", `${kind} ${f}: first section must be For Andre`);
			for (const pattern of kind === "plans" ? [...SECTIONS, /^Close$/] : SECTIONS) {
				const section = sections.find((s) => pattern.test(s.title));
				assert.ok(section, `${kind} ${f} has no section matching ${pattern}`);
				assert.ok(section.body.join("\n").trim(), `${kind} ${f}: ${section.title} section is empty`);
			}
		}
	}
});
