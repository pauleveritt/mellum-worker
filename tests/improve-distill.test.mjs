import assert from "node:assert/strict";
import test from "node:test";

import { distill, distillFromRun, lessonsFromVerdict } from "../learn/code/improve_distill.mjs";

// A schema-2 worker record line, as mellum-record writes and mellum-learn reads.
const REC = (o) =>
	JSON.stringify({
		schema: 2,
		kind: "mode",
		endedAt: "2026-10-31T08:00:00Z",
		cwd: "/loop/iter1/ws",
		...o,
	});

test("distill learns 'Do not: start servers' from a run that started one, and merges it into AGENTS.md", () => {
	const recordsText = REC({ commands: [{ command: "uvicorn app:app", failed: false, mutates: false }] });
	const r = distill({
		recordsText,
		agentsMd: "# Project\n\n## Mellum\n\n- Test command: uv run pytest\n",
		cwd: "/loop",
		n: 10,
	});
	assert.ok(r.added.some((b) => /do not/i.test(b) && /server/i.test(b)), JSON.stringify(r.added));
	assert.match(r.text, /start servers/);
	assert.match(r.text, /Test command: uv run pytest/, "keeps the existing bullet");
});

test("distill is additive and idempotent: re-running with the already-carried AGENTS.md adds nothing", () => {
	const recordsText = REC({ commands: [{ command: "uvicorn app:app", failed: false }] });
	const r = distill({
		recordsText,
		agentsMd: "# Project\n\n## Mellum\n\n- Do not: start servers\n",
		cwd: "/loop",
		n: 10,
	});
	assert.deepEqual(r.added, [], "nothing new to add when the carried file already has it");
	assert.match(r.text, /start servers/);
});

test("distill filters records to those under cwd, so an unrelated workspace's record is ignored", () => {
	const recordsText = REC({ cwd: "/somewhere/else/ws", commands: [{ command: "uvicorn app:app", failed: false }] });
	const r = distill({ recordsText, agentsMd: "# Project\n\n## Mellum\n\n", cwd: "/loop", n: 10 });
	assert.deepEqual(r.added, [], "a record outside cwd does not teach anything");
});

test("lessonsFromVerdict teaches the layout and contamination failures the harness flags", () => {
	const b = lessonsFromVerdict({ out_of_layout: ["check_jinja.py", "test_home.py"], contaminated: true });
	assert.ok(b.some((x) => /do not/i.test(x) && /layout/i.test(x)), JSON.stringify(b));
	assert.ok(b.some((x) => /do not/i.test(x) && /test/i.test(x)), JSON.stringify(b));
});

test("lessonsFromVerdict teaches nothing from a clean run", () => {
	assert.deepEqual(lessonsFromVerdict({ out_of_layout: [], contaminated: false }), []);
});

test("distillFromRun merges verdict lessons into AGENTS.md, additively and idempotently", () => {
	const base = "# Project\n\n## Mellum\n\n- Test command: uv run pytest\n";
	const r = distillFromRun({ run: { out_of_layout: ["x.py"], contaminated: false }, agentsMd: base });
	assert.match(r.text, /layout/);
	assert.ok(r.added.length >= 1);
	assert.match(r.text, /Test command: uv run pytest/, "keeps existing facts");
	const again = distillFromRun({ run: { out_of_layout: ["x.py"], contaminated: false }, agentsMd: r.text });
	assert.deepEqual(again.added, [], "re-carrying the same lesson adds nothing");
});
