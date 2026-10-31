import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";

// Every lesson names the remedy it teaches and whether its lesson check (a visible FAIL -> PASS on
// a challenge of its own) exists yet. None may claim a FAIL -> PASS it has not shown.
const EXPECTED = {
	E1: "`context/repair-think-tags`",
	E2: "`context/trim-tool-output`",
	E3: "`guard/break-repeat-loops`",
	E4: "`guard/stay-in-workspace`",
	E5: "`guard/refuse-whole-file-rewrite`",
	E6: "`context/narrow-tools`",
	E7: "`guard/cap-turns`",
	M1: "`context/add-project-facts`",
	M2: "`context/use-short-prompt`",
	M3: "`nudge/nudge-empty-turn`",
	M4: "`tool/background-long-commands`",
	M5: "`tool/lookup-library-docs`",
	M6: "`check/check-code-quality`",
	M7: "`tool/keep-a-plan`",
	M8: "your grader",
	H1: "`workflow/spec-driven-flow`",
	H2: "none:",
	H3: "none:",
	H4: "none:",
	H5: "none: you write it",
	H6: "none: you write it",
};

const pages = [];
for (const tier of ["easy", "medium", "hard"]) {
	for (const f of readdirSync(new URL(`../learn/lessons/${tier}/`, import.meta.url))) {
		if (f.endsWith(".md") && f !== "index.md") pages.push(new URL(`../learn/lessons/${tier}/${f}`, import.meta.url));
	}
}

for (const url of pages) {
	const text = readFileSync(url, "utf8");
	const number = text.match(/^number: (\S+)/m)[1];
	test(`${number} names its remedy unit and its lesson check`, () => {
		const unit = text.match(/^\*\*Remedy unit:\*\* (.+)$/m);
		assert.ok(unit, "no **Remedy unit:** line");
		assert.ok(unit[1].startsWith(EXPECTED[number]), `${number}: ${unit[1]}`);
		const check = text.match(/^\*\*Lesson check:\*\* (.+)$/m);
		assert.ok(check, "no **Lesson check:** line");
		assert.match(check[1], /^(not built yet|run (once|twice) on \d{4}-\d{2}-\d{2}, and it did not show|held on \d{4}-\d{2}-\d{2}: FAIL → PASS)/,
			"a lesson check is not built, did not show FAIL -> PASS, or held");
		if (check[1].startsWith("held"))
			assert.match(check[1], /docs\/ladder\/\d{4}-\d{2}-\d{2}-[a-z-]+-check/, "a held check links its record");
	});
}

test("E1's lesson check held, and says so with its record", () => {
	const text = readFileSync(new URL("../learn/lessons/easy/reasoning-as-text.md", import.meta.url), "utf8");
	assert.match(text, /^\*\*Lesson check:\*\* held on 2026-10-30: FAIL → PASS/m);
});

test("E2's lesson check held, and says so with its record", () => {
	const text = readFileSync(new URL("../learn/lessons/easy/context-overflow.md", import.meta.url), "utf8");
	assert.match(text, /^\*\*Lesson check:\*\* held on 2026-10-30: FAIL → PASS/m);
});
