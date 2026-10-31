import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const ROOT = resolve(import.meta.dirname, "..");
const page = (p) => readFileSync(resolve(ROOT, "learn", p), "utf8");

test("the pathologies page is four sections of numbered entries", () => {
  const p = page("pathologies.md");
  const heads = [...p.matchAll(/^## (.+)$/gm)].map((m) => m[1]);
  assert.equal(heads.length, 5, `expected five sections, found ${heads.length}`);
  assert.equal(heads[0], "How to read this");
  const entries = [...p.matchAll(/^\d+\. \*\*(.+?)\.\*\* /gm)].map((m) => m[1]);
  assert.ok(entries.length >= 11, `expected at least 11 entries, found ${entries.length}`);
  assert.equal(new Set(entries).size, entries.length, "an entry name repeats");
});

test("every pathology carries an observation and an answer", () => {
  const p = page("pathologies.md");
  // Each entry is a numbered line up to the next numbered line or heading.
  const blocks = p.split(/^\d+\. /m).slice(1);
  for (const block of blocks) {
    const name = block.slice(0, block.indexOf("**") === 2 ? block.indexOf("**", 2) : 60);
    assert.match(block, /\*\*Seen(?: elsewhere)?:\*\*/, `entry lacks Seen: ${name}`);
    assert.match(block, /\*\*Answer:\*\*/, `entry lacks Answer: ${name}`);
    const seen = block.split(/\*\*Answer:/)[0];
    assert.match(seen, /\]\(/, `Seen: line has no record link: ${name}`);
  }
});

test("the page states what it is not", () => {
  const p = page("pathologies.md");
  assert.match(p, /not a denominator/);
  assert.match(p, /[Rr]eference, not a rate/);
  assert.ok(!/docs\/ladder\//.test(p), "page links a ladder record");
  const opening = p.split(/^# .+$/m)[1].split(/^## |^!\[/m)[0].trim();
  assert.equal(opening.split(/(?<=\.)\s+/).filter(Boolean).length, 2);
  assert.ok(opening.split(/\s+/).length <= 45, "opening is over 45 words");
});

test("false success cites the ditch session's record", () => {
  assert.match(page("pathologies.md"), /False success\.[\s\S]*?2026-10-29-the-ditch-session\.md/);
});

test("lessons that left the track keep their evidence: the thinking pathology and the task-shaping backlog entry", () => {
  assert.match(page("pathologies.md"), /\*\*Thinking spends the answer budget\.\*\*[\s\S]*?2026-10-29-lessons-left-the-track\.md/);
  const backlog = readFileSync(resolve(ROOT, "BACKLOG.md"), "utf8");
  assert.match(backlog, /\*\*A unit that shapes the task in a session\.\*\*[\s\S]*?\*Reopens when\*/);
});
