import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const CHECKER = resolve(import.meta.dirname, "docs-caps.test.mjs");
const VALID = `# A cycle

## For Andre
The harness rejects workspace-controlled grading.

## Ladder run
No model run: deterministic fixture tests prove this harness repair.

## Persuasion → enforcement
No Pi hook applies to offline grading; the trusted runner enforces the boundary.
`;

function checkDocument(text, kind = "specs") {
	const root = mkdtempSync(join(tmpdir(), "mellum-doc-policy-"));
	try {
		mkdirSync(join(root, "tests"));
		mkdirSync(join(root, "docs/superpowers", kind), { recursive: true });
		copyFileSync(CHECKER, join(root, "tests/docs-caps.test.mjs"));
		writeFileSync(join(root, "docs/superpowers", kind, "2026-11-07-example.md"), text);
		const env = { ...process.env };
		delete env.NODE_TEST_CONTEXT;
		return spawnSync(process.execPath, [
			"--test", "--test-name-pattern=documents from the re-boot",
			join(root, "tests/docs-caps.test.mjs"),
		], { encoding: "utf8", env });
	} finally {
		rmSync(root, { recursive: true, force: true });
	}
}

test("document gate rejects For Andre buried after another section", () => {
	const buried = VALID.replace("## For Andre", "## Background\nContext.\n\n## For Andre");
	const result = checkDocument(buried);
	assert.notEqual(result.status, 0, "a buried For Andre passed the document gate");
	assert.match(result.stdout + result.stderr, /first section must be For Andre/);
	assert.equal(checkDocument(VALID).status, 0);
});

test("document gate rejects required headings supplied only inside a code example", () => {
	const result = checkDocument(`# Example\n\n\`\`\`markdown\n${VALID}\`\`\`\n`);
	assert.notEqual(result.status, 0, "a fenced template passed as real document sections");
	assert.match(result.stdout + result.stderr, /first section must be For Andre/);
	assert.equal(checkDocument(`---\nphase: F\n---\n\n${VALID}`).status, 0);
});

test("document gate rejects an empty enforcement assessment", () => {
	const empty = VALID.slice(0, VALID.indexOf("No Pi hook"));
	const result = checkDocument(empty);
	assert.notEqual(result.status, 0, "an empty enforcement section passed the document gate");
	assert.match(result.stdout + result.stderr, /Persuasion.*enforcement.*empty/);
	assert.equal(checkDocument(VALID).status, 0);
});

test("document gate requires a Close section in implementation plans", () => {
	const result = checkDocument(VALID, "plans");
	assert.notEqual(result.status, 0, "an implementation plan without closure passed the document gate");
	assert.match(result.stdout + result.stderr, /Close/);
	const complete = `${VALID}\n## Close\nSquash-merge into integration, then remove the cycle worktree and branch.\n`;
	assert.equal(checkDocument(complete, "plans").status, 0);
});
