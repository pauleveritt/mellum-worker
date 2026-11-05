import assert from "node:assert/strict";
import { basename } from "node:path";
import test from "node:test";
import { readProjectFacts, factsBlock } from "../extensions/mellum-facts.ts";

const FIXTURE = `# AgentClinic

## Mellum

- Test command: uv run python -m pytest tests
- Write only: app.py, models.py, templates/, tests/
- Do not: install packages or add dependencies; remove or rewrite routes that already work; weaken tests
`;
const FALLBACK = "Test command: uv run --offline python -m pytest -q";
const PYTEST = '[project]\nname = "x"\n[dependency-groups]\ndev = ["pytest"]\n';

function io(files) {
	return { read: (p) => files[basename(p)] }; // basename: the path is joined with "\" on Windows
}
const sum = (bullets) => bullets.reduce((n, b) => n + b.length, 0);

test("the fixture AGENTS.md gives three bullets, its test command and a character count", () => {
	const f = readProjectFacts("/p", io({ "AGENTS.md": FIXTURE }), {});
	assert.equal(f.source, "agents-md");
	assert.deepEqual(f.bullets, [
		"Test command: uv run python -m pytest tests",
		"Write only: app.py, models.py, templates/, tests/",
		"Do not: install packages or add dependencies; remove or rewrite routes that already work; weaken tests",
	]);
	assert.equal(f.testCommand, "uv run python -m pytest tests");
	assert.equal(f.chars, sum(f.bullets));
	assert.equal(f.warning, undefined);
});

test("the section ends at the next level-2 heading, or at the end of the file", () => {
	const mid = "## Mellum\n\n- Test command: make test\n\n## Other\n\n- not mine\n";
	assert.deepEqual(readProjectFacts("/p", io({ "AGENTS.md": mid }), {}).bullets, ["Test command: make test"]);
	const eof = "# T\n\n- outside\n\n## Mellum\n- Test command: make test\n- Do not: x";
	assert.deepEqual(readProjectFacts("/p", io({ "AGENTS.md": eof }), {}).bullets, ["Test command: make test", "Do not: x"]);
	const h1 = "## Mellum\n- Test command: make test\n# Next\n- no\n";
	assert.deepEqual(readProjectFacts("/p", io({ "AGENTS.md": h1 }), {}).bullets, ["Test command: make test"]);
});

test("a level-3 heading inside the section stays in it and contributes only its bullets", () => {
	const md = "## Mellum\n\n- Test command: make test\n\n### Notes\n\nprose that is not a bullet\n- Do not: edit docs\n\n## After\n- no\n";
	const f = readProjectFacts("/p", io({ "AGENTS.md": md }), {});
	assert.deepEqual(f.bullets, ["Test command: make test", "Do not: edit docs"]);
});

test("a heading that merely starts with Mellum is not the section", () => {
	const f = readProjectFacts("/p", io({ "AGENTS.md": "## Mellum notes\n- Test command: make test\n" }), {});
	assert.equal(f.source, "none");
});

test("a section without a test command plus a pytest pyproject merges the fallback last", () => {
	const md = "## Mellum\n- Write only: app.py\n";
	const f = readProjectFacts("/p", io({ "AGENTS.md": md, "pyproject.toml": PYTEST }), {});
	assert.equal(f.source, "agents-md+detected");
	assert.deepEqual(f.bullets, ["Write only: app.py", FALLBACK]);
	assert.equal(f.testCommand, "uv run --offline python -m pytest -q");
	assert.equal(f.chars, sum(f.bullets));
});

test("a section with a test command ignores the pyproject", () => {
	const f = readProjectFacts("/p", io({ "AGENTS.md": FIXTURE, "pyproject.toml": PYTEST }), {});
	assert.equal(f.source, "agents-md");
	assert.equal(f.bullets.length, 3);
});

test("a section without a test command and no pytest keeps its bullets, test command null", () => {
	const f = readProjectFacts("/p", io({ "AGENTS.md": "## Mellum\n- Write only: a.py\n" }), {});
	assert.equal(f.source, "agents-md");
	assert.equal(f.testCommand, null);
});

test("no AGENTS.md and a pytest pyproject is detected", () => {
	const f = readProjectFacts("/p", io({ "pyproject.toml": PYTEST }), {});
	assert.equal(f.source, "detected");
	assert.deepEqual(f.bullets, [FALLBACK]);
	assert.equal(f.testCommand, "uv run --offline python -m pytest -q");
	assert.equal(f.chars, FALLBACK.length);
});

test("AGENTS.md without the section and a pytest pyproject is detected too", () => {
	const f = readProjectFacts("/p", io({ "AGENTS.md": "# Notes\n- hello\n", "pyproject.toml": PYTEST }), {});
	assert.equal(f.source, "detected");
});

test("no AGENTS.md and only a package.json adds nothing", () => {
	const f = readProjectFacts("/p", io({ "package.json": "{}" }), {});
	assert.deepEqual(f, { source: "none", bullets: [], testCommand: null, chars: 0 });
});

test("a pyproject that does not mention pytest adds nothing", () => {
	assert.equal(readProjectFacts("/p", io({ "pyproject.toml": '[project]\nname = "x"\n' }), {}).source, "none");
});

test("bullets over 600 characters: a warning, the section ignored, the fallback applies", () => {
	const long = `## Mellum\n- Test command: make test\n- Do not: ${"x".repeat(600)}\n`;
	const f = readProjectFacts("/p", io({ "AGENTS.md": long, "pyproject.toml": PYTEST }), {});
	assert.match(f.warning ?? "", /600/);
	assert.equal(f.source, "detected");
	assert.deepEqual(f.bullets, [FALLBACK]);
	const none = readProjectFacts("/p", io({ "AGENTS.md": long }), {});
	assert.match(none.warning ?? "", /600/);
	assert.equal(none.source, "none");
	assert.deepEqual(none.bullets, []);
	assert.equal(none.testCommand, null);
});

test("exactly 600 characters of bullets is allowed", () => {
	const body = "Do not: " + "x".repeat(600 - "Do not: ".length);
	const f = readProjectFacts("/p", io({ "AGENTS.md": `## Mellum\n- ${body}\n` }), {});
	assert.equal(f.chars, 600);
	assert.equal(f.warning, undefined);
	assert.equal(f.source, "agents-md");
});

test("MELLUM_MODE_FACTS=0 turns off the block and the fallback", () => {
	const f = readProjectFacts("/p", io({ "AGENTS.md": FIXTURE, "pyproject.toml": PYTEST }), { MELLUM_MODE_FACTS: "0" });
	assert.deepEqual(f, { source: "off", bullets: [], testCommand: null, chars: 0 });
	assert.equal(readProjectFacts("/p", io({ "AGENTS.md": FIXTURE }), { MELLUM_MODE_FACTS: "1" }).source, "agents-md");
});

test("a read that throws is treated as a missing file", () => {
	const f = readProjectFacts("/p", { read: () => { throw new Error("EACCES"); } }, {});
	assert.equal(f.source, "none");
});

test("factsBlock is empty for no bullets, else the heading and the bullets", () => {
	assert.equal(factsBlock({ source: "none", bullets: [], testCommand: null, chars: 0 }), "");
	assert.equal(
		factsBlock({ source: "agents-md", bullets: ["A: 1", "B: 2"], testCommand: null, chars: 8 }),
		"\n\nProject facts:\n- A: 1\n- B: 2",
	);
});
