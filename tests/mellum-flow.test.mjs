import assert from "node:assert/strict";
import test from "node:test";

import { mkdtempSync, mkdirSync, writeFileSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { PHASES, finalText, bestPytest, asTodo, asCode, looksLikePytest, freezeName, gateTestName, GATE_DIR, materializeGate, flowBlock, PHASE_CALL_CAP, BASE_GUIDE, toolCallSummaries, reviewFromTestFailure, specCoverageTokens, missingGateCoverage, effectiveMaxTokens } from "../extensions/mellum-flow.ts";

const asstText = (t) => ({ type: "message_end", message: { role: "assistant", content: [{ type: "text", text: t }] } });

// The feed must show a sub-agent's tool calls so a hung phase is diagnosable. pi's --mode json
// emits message_end (with toolCall content) and tool_execution_start — NOT "tool_call", which the
// old code keyed on, so no command was ever logged. toolCallSummaries reads the real schema.
test("toolCallSummaries reads a bash command from a message_end toolCall (the real schema)", () => {
	const evt = { type: "message_end", message: { role: "assistant", content: [
		{ type: "text", text: "running the app" },
		{ type: "toolCall", name: "bash", arguments: { command: "uv run python app.py" } },
	] } };
	assert.deepEqual(toolCallSummaries(evt), [{ name: "bash", where: "uv run python app.py" }]);
});

test("toolCallSummaries handles string-encoded arguments and a targeted path", () => {
	const evt = { type: "message_end", message: { content: [
		{ type: "toolCall", name: "write", arguments: '{"path":"templates/home.html","content":"<h1>hi</h1>"}' },
	] } };
	assert.deepEqual(toolCallSummaries(evt), [{ name: "write", where: "templates/home.html" }]);
});

test("toolCallSummaries reads tool_execution_start and the legacy tool_call too", () => {
	assert.deepEqual(toolCallSummaries({ type: "tool_execution_start", name: "ls", arguments: { path: "src" } }),
		[{ name: "ls", where: "src" }]);
	assert.deepEqual(toolCallSummaries({ type: "tool_call", toolName: "bash", input: { command: "pytest -q" } }),
		[{ name: "bash", where: "pytest -q" }]);
});

test("toolCallSummaries returns nothing for non-tool events and junk", () => {
	assert.deepEqual(toolCallSummaries(asstText("just thinking out loud")), []);
	assert.deepEqual(toolCallSummaries(null), []);
	assert.deepEqual(toolCallSummaries({ type: "message_end", message: {} }), []);
});

// The gate failure goes into REVIEW.md LABELLED so the coder fixes the app, not the test. A bare
// pytest tail names tests/test_gate_phase_N.py and reads as "make these pass", which a small model
// satisfies by editing that test (pointless — the harness restores it). So: fix-the-app label, and
// strip the gate test-file PATHS while keeping the test name + reason.
test("reviewFromTestFailure labels it as the app failing and says do not edit tests", () => {
	const out = reviewFromTestFailure("E   assert 404 == 303\n");
	assert.match(out, /YOUR APP FAILED/);
	assert.match(out, /Fix the application code/);
	assert.match(out, /do NOT edit|Do NOT edit/i);
	assert.match(out, /assert 404 == 303/); // the behaviour/reason is kept
});

test("reviewFromTestFailure strips the gate test-file PATH but keeps the test name", () => {
	const tail = "FAILED tests/test_gate_phase_5.py::test_archive_resolved_complaint - assert 404 == 303";
	const out = reviewFromTestFailure(tail);
	assert.ok(!out.includes("tests/test_gate_phase_5.py"), "the test-file path must be gone");
	assert.match(out, /test_archive_resolved_complaint/); // the test NAME (the behaviour) stays
	assert.match(out, /assert 404 == 303/);
});

test("reviewFromTestFailure neutralises a bare gate-file mention", () => {
	const out = reviewFromTestFailure("see tests/test_gate_phase_2.py for details");
	assert.ok(!out.includes("test_gate_phase_2.py"));
	assert.match(out, /the acceptance test/);
});

test("toolCallSummaries lists multiple tool calls in one message_end", () => {
	const evt = { type: "message_end", message: { content: [
		{ type: "toolCall", name: "write", arguments: { path: "app.py" } },
		{ type: "toolCall", name: "bash", arguments: { command: "uv run pytest -q tests" } },
	] } };
	assert.deepEqual(toolCallSummaries(evt).map((c) => c.name), ["write", "bash"]);
});

test("bestPytest salvages a test written mid-transcript when the examiner ends on chatter", () => {
	// hard phases 4 & 5: the examiner (a tool-using agent) wrote the test, then made a verifying
	// tool call and ended with a short non-test message, so finalText (the LAST text) missed the
	// test and the gate never froze — a whole round wasted. bestPytest scans every assistant block.
	const events = [
		asstText("Let me read the spec first."),
		asstText("```python\nfrom app import app\ndef test_archive():\n    assert 1\n```"),
		asstText("I've written the acceptance test above; it covers archive and audit."),
	];
	const code = bestPytest(events);
	assert.ok(looksLikePytest(code), "must recover the real test");
	assert.match(code, /def test_archive/);
	assert.doesNotMatch(code, /written the acceptance test above/);
});

test("bestPytest prefers the longest complete test over a partial earlier block", () => {
	const events = [
		asstText("def test_a():\n    assert 1"),
		asstText("from app import app\ndef test_a():\n    assert 1\ndef test_b():\n    assert 2\ndef test_c():\n    assert 3"),
	];
	assert.match(bestPytest(events), /test_c/); // the fuller block wins
});

test("bestPytest falls back to finalText when no block is a pytest file", () => {
	assert.equal(bestPytest([asstText("no tests here"), asstText("still nothing")]), "still nothing");
});

test("BASE_GUIDE restores structure generically without contradicting any role", () => {
	assert.match(BASE_GUIDE, /single-purpose|ONE job/i);
	assert.match(BASE_GUIDE, /decisive and brief|do not deliberate/i); // the anti-ramble line
	assert.match(BASE_GUIDE, /authoritative/i); // the role prompt wins on specifics
	// it governs HOW to operate, not WHAT to produce — must not name a role's output (code/test/plan)
	assert.ok(!/write (the )?(code|tests?|implementation)/i.test(BASE_GUIDE), "guide must not prescribe a role's output");
});

test("per-phase max_tokens: planner/reviewers below examine, but not truncating", () => {
	// The examiner is a thinking model that can't be capped; on a complex phase it needs >16384
	// tokens just to FINISH thinking, so 16384 emitted an EMPTY test (all budget spent thinking) and
	// no gate froze — hard phase 5 died on this. Measured: 32000 lets it finish and emit. The
	// examiner must have the most room of any role.
	assert.equal(PHASES.examine.maxTokens, 32000);
	assert.ok(PHASES.code.maxTokens >= 16384);
	for (const r of ["plan", "review_plan", "review_code"]) {
		assert.ok(PHASES[r].maxTokens < PHASES.examine.maxTokens, `${r} capped below examine`);
		// not so tight it truncates a thinking model before it writes its output: 2048 left the
		// planner with an EMPTY TODO (all budget spent thinking). The cap is a runaway backstop;
		// the BASE_GUIDE is the real brevity lever.
		assert.ok(PHASES[r].maxTokens >= 8192, `${r} must fit think + output`);
	}
});

test("flowBlock always allows test (the only exit) and read", () => {
	assert.equal(flowBlock("test", 9999, false), undefined);
	assert.equal(flowBlock("read", 9999, false), undefined);
});

test("flowBlock makes examine run once per phase (blocked once the gate is frozen)", () => {
	assert.equal(flowBlock("examine", 1, false), undefined); // first call: no gate yet
	assert.match(flowBlock("examine", 1, true), /already written|Do NOT examine again/i); // gate frozen → blocked
});

test("flowBlock caps the phase so the orchestrator can't loop to the deadline", () => {
	assert.equal(flowBlock("code", PHASE_CALL_CAP - 1, false), undefined); // under budget
	assert.match(flowBlock("code", PHASE_CALL_CAP, false), /budget reached/i); // at the cap
	assert.match(flowBlock("review_code", PHASE_CALL_CAP + 3, false), /budget reached/i);
	// but test can still be called past the cap, so the phase can finish
	assert.equal(flowBlock("test", PHASE_CALL_CAP + 3, false), undefined);
});

test("the examiner is read-only but has lookup, and writes the acceptance gate from the spec", () => {
	assert.ok(!PHASES.examine.tools.includes("write"));
	assert.ok(!PHASES.examine.tools.includes("bash"));
	assert.ok(PHASES.examine.tools.includes("lookup"));
	assert.ok(PHASES.examine.ext.some((e) => e.includes("mellum-knowledge")));
	assert.match(PHASES.examine.prompt, /acceptance test|definition of DONE/i);
});

test("the examiner is told to be exhaustive and to cover negative/edge cases, not just the happy path", () => {
	assert.match(PHASES.examine.prompt, /exhaustive/i);
	assert.match(PHASES.examine.prompt, /negative|edge/i);
	assert.match(PHASES.examine.prompt, /not just the happy path|only its happy path/i);
	// It must know earlier phases are already frozen so it covers only this phase without contradicting them.
	assert.match(PHASES.examine.prompt, /earlier phase|already frozen/i);
});

test("thinking budget maps to the role: reasoning roles think hard, the coder acts", () => {
	for (const r of ["plan", "review_plan", "examine", "review_code"]) {
		assert.equal(PHASES[r].thinking, "high", r); // reasoning roles
	}
	assert.equal(PHASES.code.thinking, "low"); // the coder executes against a decided gate
});

test("the examiner asserts exact strings only where the spec is verbatim, requirements otherwise", () => {
	// medium phase 1 failed because the examiner invented `initial-scale=1.0` and exact nav markup
	// the spec never gave — brittle strings a correct implementation can't match.
	assert.match(PHASES.examine.prompt, /ONLY where the spec gives them VERBATIM/i);
	assert.match(PHASES.examine.prompt, /NOT an invented string|made-up exact/i);
	assert.match(PHASES.examine.prompt, /brittleness/i);
});

test("the examiner must not assert a bare substring absent when it is part of a legitimate word", () => {
	// hard phase 4 could never pass: the examiner froze `assert "Resolve" not in html` while the
	// same test required "Resolved" present — but "Resolve" is a substring of "Resolved", so the
	// assertion is self-contradictory and no correct app satisfies it. Absence must target the
	// specific action (its form action= URL / exact control), not a prefix of a word on the page.
	assert.match(PHASES.examine.prompt, /substring of a (longer )?word|prefix of|"Resolve" is inside "Resolved"|part of another word/i);
	assert.match(PHASES.examine.prompt, /not in|absent|absence/i);
	assert.match(PHASES.examine.prompt, /form .*action|action=|specific (control|button|action)/i);
});

test("the examiner is told to set follow_redirects=False on the client, not per request", () => {
	// Per-request follow_redirects=False kept slipping: the examiner applied it to some POSTs and
	// forgot it on others (the add-complaint setup POST), then asserted 3xx on a plain POST that
	// TestClient had followed to 200 — a correct app failed, twice. Setting it ONCE on the client
	// eliminates the whole class. The rule must name the client-level construction.
	assert.match(PHASES.examine.prompt, /TestClient\(\s*app\s*,\s*follow_redirects=False\s*\)/);
	assert.match(PHASES.examine.prompt, /redirect/i);
});

test("the examiner must assert relative deltas, not absolute totals, against shared state", () => {
	// hard phase 5 test_stats asserted open==1, but the gate's own earlier tests had added
	// complaints to the shared in-memory store, so the real count was higher — a correct app failed.
	// Tests run in one process against shared state; assert before/after deltas or filter to this
	// test's own records, never an absolute total that assumes a clean store.
	assert.match(PHASES.examine.prompt, /shared|accumulat|earlier tests|other tests|clean (store|state|database)/i);
	assert.match(PHASES.examine.prompt, /delta|before.*after|relative|count before/i);
});

test("the examiner must disable redirect-following when asserting a redirect status", () => {
	// medium phase 3 looped forever: the examiner asserted `client.post(...).status_code == 303`,
	// but starlette's TestClient follows redirects by default, so the response is the final 200 GET
	// and `assert 200 == 303` fails a CORRECT 303 handler. A redirect assertion needs
	// follow_redirects=False. The app was right; the gate was unpassable.
	assert.match(PHASES.examine.prompt, /follow_redirects=False/);
	assert.match(PHASES.examine.prompt, /follows redirects by default|would follow the redirect/i);
});

test("the examiner must assert stable identity for mutate-a-specific-record phases", () => {
	// medium phase 4 failed the hidden grader because Complaint had no stable `id` field — the
	// examiner tested resolve/reopen behaviour but not that identity is an explicit, stable field.
	assert.match(PHASES.examine.prompt, /IDENTITY|identity field/i);
	assert.match(PHASES.examine.prompt, /stable/i);
	assert.match(PHASES.examine.prompt, /list position|index/i); // must forbid positional ids
	assert.match(PHASES.examine.prompt, /distinct ids|DISTINCT ids/i);
});

test("the examiner must seed inputs and assert exact outputs for computed/report endpoints", () => {
	// hard phases 6-7 passed the visible gate but failed the hidden oracle: /tickets reported wrong
	// sums and /visits returned []. The gates accepted a 200 / empty body. A computed endpoint must
	// be driven with seeded rows and checked against the EXACT expected result, with a row included
	// AND one excluded by each filter/definition the spec gives, so a stub fails. General, spec-led.
	assert.match(PHASES.examine.prompt, /computes from data|a sum, count, filter|COMPUTED\/REPORT/i);
	assert.match(PHASES.examine.prompt, /exact (expected )?(result|output|value)|compute the expected|the EXACT result/i);
	assert.match(PHASES.examine.prompt, /mishandle|disagree|included and (one )?excluded|include.*exclude|distinguishing/i);
	// and migrations/named artifacts are asserted RECORDED/applied, not merely defined
	assert.match(PHASES.examine.prompt, /recorded|applied/i);
});

test("the examiner must not destructively mutate a persistent store; compute from existing data", () => {
	// hard phases 6-7 passed visible but failed hidden because the gate ran DELETE FROM tickets /
	// DELETE FROM visits then inserted its own rows into data.db — a destructive write to the
	// file-backed fixture that the spec's report reads "from the database" and the grader checks.
	// For data that already exists, read it and compute the expected; never delete/overwrite it;
	// roll back any row added. General test discipline, not suite-specific.
	assert.match(PHASES.examine.prompt, /persistent|on disk|file-backed|outlives|database file/i);
	assert.match(PHASES.examine.prompt, /read (what is|the data)|compute the expected from (the|what)|already (there|exists)/i);
	assert.match(PHASES.examine.prompt, /roll ?back|do not (delete|overwrite|mutate|reseed)|never (delete|overwrite|mutate|reseed)/i);
});

test("the examiner must write self-contained tests that create their own data, not assume seed ids/state", () => {
	// strengthening for phases 6-7 regressed phase 5: the examiner assumed seed complaints at ids
	// 2/3 in an OPEN state, but a prior test (shared store) had changed them, so a correct app
	// (archive-open -> 400) saw 303 and `next(c.id==3)` hit StopIteration. Tests must create the
	// records they need and never assume a seed record exists at a given id or in a given state.
	assert.match(PHASES.examine.prompt, /self-contained|create the (records|rows|data) it needs|create its own/i);
	assert.match(PHASES.examine.prompt, /never assume a seed|not assume.*seed|a given id|particular id|given state|particular state/i);
});

test("the coder must ground in the real fixture schema, not invent columns", () => {
	// hard phase 7: the fixture `visits` table has a populated `date` column, but the coder invented
	// a `visited_at` column (NULL for every fixture row) and queried that, so /visits returned empty.
	// The coder must inspect the actual columns of existing data and use them, never invent one.
	assert.match(PHASES.code.prompt, /PRAGMA table_info|inspect its real columns|columns that are actually there|already exists/i);
	assert.match(PHASES.code.prompt, /never invent|do not invent|not .*assume a name|existing column already holds/i);
});

test("the coder is pointed at the cumulative gate and told earlier phases must keep passing", () => {
	assert.match(PHASES.code.prompt, /test_gate_phase/);
	assert.match(PHASES.code.prompt, /earlier phase/i);
	assert.match(PHASES.code.prompt, /ALL|all pass|keep passing/i);
});

test("freezeName/gateTestName derive stable per-phase names so the gate accumulates", () => {
	assert.equal(freezeName(1), "phase_1.py");
	assert.equal(freezeName("2"), "phase_2.py");
	assert.equal(freezeName(undefined ?? "1"), "phase_1.py");
	assert.equal(gateTestName("phase_3"), "test_gate_phase_3.py");
});

test("materializeGate restores EVERY frozen phase into tests/ and clears stale gate files", () => {
	const ws = mkdtempSync(join(tmpdir(), "mellum-gate-"));
	mkdirSync(join(ws, GATE_DIR), { recursive: true });
	mkdirSync(join(ws, "tests"), { recursive: true });
	writeFileSync(join(ws, GATE_DIR, "phase_1.py"), "def test_p1():\n    assert 1\n");
	writeFileSync(join(ws, GATE_DIR, "phase_2.py"), "def test_p2():\n    assert 2\n");
	// a stale restored file from a dropped phase, and a coder's own test, must be handled correctly
	writeFileSync(join(ws, "tests", "test_gate_phase_9.py"), "def test_stale():\n    assert 0\n");
	writeFileSync(join(ws, "tests", "test_coder.py"), "def test_keep():\n    assert 1\n");

	const n = materializeGate(ws);
	const got = readdirSync(join(ws, "tests")).sort();

	assert.equal(n, 2);
	assert.deepEqual(got, ["test_coder.py", "test_gate_phase_1.py", "test_gate_phase_2.py"]);
	assert.match(readFileSync(join(ws, "tests", "test_gate_phase_1.py"), "utf8"), /test_p1/);
	rmSync(ws, { recursive: true, force: true });
});

test("asCode extracts a fenced python block, else returns the raw text", () => {
	assert.equal(asCode("```python\nimport x\nassert 1\n```"), "import x\nassert 1\n");
	assert.equal(asCode("def test():\n    assert True"), "def test():\n    assert True\n");
});

test("asCode strips a dangling fence with no matching pair (the hard phase-4 gate SyntaxError)", () => {
	// hard phase 4 looped forever: the examiner emitted raw python then a trailing ``` with NO
	// opening fence, so neither block regex matched and asCode returned it verbatim. The frozen
	// gate ended on a lone ``` → SyntaxError → phase_gate_ok rejected a CORRECT gate and the phase
	// could never pass. A lone fence line must never survive into the Python gate.
	assert.equal(asCode("def test_x():\n    assert 1\n```"), "def test_x():\n    assert 1\n");
	assert.equal(asCode("```python\ndef test_y():\n    assert 1"), "def test_y():\n    assert 1\n");
	// and a fence line in the middle of otherwise-raw output is stripped, not left to break compile
	assert.equal(asCode("import os\n```\ndef test_z():\n    assert 1"), "import os\ndef test_z():\n    assert 1\n");
});

test("asCode prefers a python block over an HTML block that appears first", () => {
	const reply = "```html\n<div>complaints</div>\n```\nand the test:\n```python\ndef test_x():\n    assert 1\n```";
	assert.equal(asCode(reply), "def test_x():\n    assert 1\n");
});

test("looksLikePytest accepts a real test file and rejects HTML/template or testless leakage", () => {
	assert.ok(looksLikePytest("from app import app\ndef test_home():\n    assert 1\n"));
	assert.ok(looksLikePytest("class TestThing:\n    def test_a(self):\n        assert 1\n"));
	// the exact failure seen in flow20: an HTML/template blob written as the "test"
	assert.ok(!looksLikePytest("templates/complaints.html\n{% extends 'base.html' %}\n<div>hi</div>\n"));
	assert.ok(!looksLikePytest("import pytest\nX = 1\n")); // compiles but defines no test
});

test("finalText returns the LAST assistant text block from a json event stream", () => {
	const events = [
		{ type: "message_end", message: { role: "assistant", content: [{ type: "text", text: "first" }] } },
		{ type: "tool_call", toolName: "read" },
		{ type: "message_end", message: { role: "user", content: [{ type: "text", text: "ignored" }] } },
		{ type: "message_end", message: { role: "assistant", content: [{ type: "text", text: "REVIEW: PASS" }] } },
	];
	assert.equal(finalText(events), "REVIEW: PASS");
});

test("finalText is empty when there is no assistant text", () => {
	assert.equal(finalText([{ type: "tool_call", toolName: "bash" }]), "");
	assert.equal(finalText([]), "");
});

test("only the coder phase has write/edit/bash; plan and reviewers are read-only", () => {
	assert.ok(PHASES.code.tools.includes("bash") && PHASES.code.tools.includes("write"));
	// plan outputs text (the harness saves it as TODO.md); reviewers only read. None of them write.
	for (const r of ["plan", "review_plan", "review_code"]) {
		assert.ok(!PHASES[r].tools.includes("bash"), r);
		assert.ok(!PHASES[r].tools.includes("write"), r);
		assert.ok(!PHASES[r].tools.includes("edit"), r);
	}
});

test("only the coder loads the write-safety guards (nonblock/guards/surgical)", () => {
	assert.ok(PHASES.code.ext.some((e) => e.includes("mellum-nonblock")));
	assert.ok(PHASES.code.ext.some((e) => e.includes("mellum-surgical")));
	// The read-only phases never get the write-oriented guards…
	for (const r of ["plan", "review_plan", "examine", "review_code"]) {
		assert.ok(!PHASES[r].ext.some((e) => e.includes("mellum-nonblock")), `${r} no nonblock`);
		assert.ok(!PHASES[r].ext.some((e) => e.includes("mellum-surgical")), `${r} no surgical`);
		assert.ok(!PHASES[r].ext.some((e) => e.includes("mellum-guards")), `${r} no full guards`);
	}
});

test("every phase carries the loop-breaker (unbounded no-op repeats are capped for any model)", () => {
	// The coder gets it via mellum-guards; every other phase via the dedicated loop-guard.
	// A thinking model whose stop-decision never fires (e.g. examine on a fresh workspace)
	// must still be capped so the phase emits and the flow can grade.
	assert.ok(PHASES.code.ext.some((e) => e.includes("mellum-guards")), "coder via guards");
	for (const r of ["plan", "review_plan", "examine", "review_code"]) {
		assert.ok(PHASES[r].ext.some((e) => e.includes("mellum-loopguard")), `${r} loop-guard`);
	}
});

test("effectiveMaxTokens caps a phase at MELLUM_FLOW_MAXTOKENS, never raising it", () => {
	// Unset: the phase keeps its own budget (the default worker is unchanged).
	assert.equal(effectiveMaxTokens(32000, undefined), 32000);
	assert.equal(effectiveMaxTokens(32000, ""), 32000);
	// Set: a ceiling — it stops an over-generating model early, but never lifts a smaller budget.
	assert.equal(effectiveMaxTokens(32000, "10000"), 10000);
	assert.equal(effectiveMaxTokens(8192, "10000"), 8192);
	// Garbage or non-positive is ignored, so a bad env can never zero the budget.
	assert.equal(effectiveMaxTokens(32000, "0"), 32000);
	assert.equal(effectiveMaxTokens(32000, "-5"), 32000);
	assert.equal(effectiveMaxTokens(32000, "abc"), 32000);
});

test("asTodo strips preamble and code fences, keeping from the first heading", () => {
	assert.equal(asTodo("Here is the plan:\n\n## North Star\nDo it\n- [ ] a"), "## North Star\nDo it\n- [ ] a\n");
	assert.equal(asTodo("```markdown\n## North Star\ng\n```"), "## North Star\ng\n");
	assert.equal(asTodo("## North Star\nx"), "## North Star\nx\n");
});

test("every phase has a system prompt and a thinking budget", () => {
	for (const [name, p] of Object.entries(PHASES)) {
		assert.ok(p.prompt.length > 40, name);
		assert.ok(["off", "minimal", "low", "medium", "high", "xhigh", "max"].includes(p.thinking), name);
	}
});

test("specCoverageTokens extracts the contract tokens the spec NAMES", () => {
	const slice = [
		"# Phase 7 — Visits report",
		"`GET /visits` takes `from`, `to`.",
		"Add a migration. Name it `add_tickets_note`; add a nullable `note` column to `tickets`.",
		"POST /complaints returns 303 with Location: /complaints",
		"create an index `idx_tickets_status_archived` on tickets.",
	].join("\n");
	const toks = specCoverageTokens(slice);
	for (const t of ["visits", "add_tickets_note", "note", "303", "idx_tickets_status_archived"]) {
		assert.ok(toks.includes(t), `missing ${t} in ${JSON.stringify(toks)}`);
	}
});

test("specCoverageTokens reduces a templated route to its distinctive leaf", () => {
	const toks = specCoverageTokens("`POST /complaints/{id}/archive` archives it.");
	assert.ok(toks.includes("archive"), JSON.stringify(toks));
	assert.ok(!toks.some((t) => t.includes("{")), "no placeholder token");
});

test("specCoverageTokens does not pin a bare 200", () => {
	assert.ok(!specCoverageTokens("the home page returns 200 with a tagline").includes("200"));
});

test("missingGateCoverage returns only spec tokens the gate never references", () => {
	const slice = "`GET /visits` ... returns 303 ... Name it `add_tickets_note`.";
	// a gate that tests /visits but forgets the 303 and the migration
	const gate = "def test_visits():\n    assert client.get('/visits').json()['visits']\n";
	assert.deepEqual(missingGateCoverage(slice, gate).sort(), ["303", "add_tickets_note"]);
	// a gate that references all of them (any mention counts) → nothing missing
	const full = gate + "\n# 303 add_tickets_note\n";
	assert.deepEqual(missingGateCoverage(slice, full), []);
});

test("asCode makes a gate's TestClient never follow redirects, so a 3xx assertion can pass", () => {
	const gate = "from starlette.testclient import TestClient\nfrom app import app\n\nclient = TestClient(app)\n\ndef test_x():\n    assert client.post('/a').status_code == 303\n";
	assert.match(asCode(gate), /client = TestClient\(app, follow_redirects=False\)/);
	const already = "from starlette.testclient import TestClient\nfrom app import app\nclient = TestClient(app, follow_redirects=False)\n\ndef test_x():\n    assert True\n";
	assert.equal((asCode(already).match(/follow_redirects/g) ?? []).length, 1);
});
