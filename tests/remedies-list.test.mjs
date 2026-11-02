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

test("the Switch on column uses /remedy, and there is no Lesson column", async () => {
	const units = await listUnits();
	const fromChallenge = renderTable(units);
	assert.match(fromChallenge, /`\/remedy on context\/add-project-facts`/);
	assert.doesNotMatch(fromChallenge, /Lesson/);
});

test("both pages carry the current list (run scripts/remedies-list.mjs to update)", async () => {
	const units = await listUnits();
	for (const page of PAGES) {
		const text = readFileSync(page, "utf8");
		assert.ok(text.includes(renderTable(units, page)), `${page} is out of date`);
	}
});
