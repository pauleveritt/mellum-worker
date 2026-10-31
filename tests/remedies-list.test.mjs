import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { listUnits, renderTable, PAGES } from "../scripts/remedies-list.mjs";

test("the remedies list names every unit file under remedies/", async () => {
	const units = await listUnits();
	const names = units.map((u) => u.name);
	for (const expected of ["guard/break-repeat-loops", "nudge/nudge-empty-turn", "context/add-project-facts", "workflow/spec-driven-flow"]) {
		assert.ok(names.includes(expected), expected);
	}
	assert.ok(units.every((u) => u.meta.pathology && u.meta.does));
});

test("a unit with a lesson links that lesson's page, relative to the page the list sits on", async () => {
	const units = await listUnits();
	const fromChallenge = renderTable(units, "learn/challenge/index.md");
	const fromLessons = renderTable(units, "learn/lessons/index.md");
	assert.match(fromChallenge, /\[M1\]\(\.\.\/lessons\/medium\/tell-it-how-to-test\.md\)/);
	assert.match(fromLessons, /\[M1\]\(medium\/tell-it-how-to-test\.md\)/);
	assert.match(fromChallenge, /`--remedy context\/add-project-facts`/);
});

test("both pages carry the current list (run scripts/remedies-list.mjs to update)", async () => {
	const units = await listUnits();
	for (const page of PAGES) {
		const text = readFileSync(page, "utf8");
		assert.ok(text.includes(renderTable(units, page)), `${page} is out of date`);
	}
});
