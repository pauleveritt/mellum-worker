import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = new URL("..", import.meta.url).pathname;

test("lesson-check --dry-run prints the page's before then after line, at its n, on the profile", () => {
	const profile = mkdtempSync(join(tmpdir(), "profile-"));
	const out = execFileSync("bash", [join(ROOT, "scripts/lesson-check.sh"), "E1", "--dry-run", "--profile", profile],
		{ cwd: ROOT, encoding: "utf8", env: { ...process.env, LESSON_CHECK_OUT: "/tmp/check" } });
	const [before, after, extra] = out.trim().split("\n");
	assert.equal(extra, undefined);
	for (const [line, arm] of [[before, "before"], [after, "after"]]) {
		assert.match(line, /harness\.py run /);
		assert.match(line, /--repeat 1/);
		assert.ok(line.includes(`--profile ${profile}`), line);
		assert.ok(line.includes(`--runs-dir /tmp/check/${arm}`), line);
	}
	assert.ok(!before.includes("context/repair-think-tags") && after.includes("context/repair-think-tags"));
});

test("lesson-check refuses a lesson with no before and after line", () => {
	assert.throws(() => execFileSync("bash", [join(ROOT, "scripts/lesson-check.sh"), "M8", "--dry-run"],
		{ cwd: ROOT, stdio: "pipe" }));
});
