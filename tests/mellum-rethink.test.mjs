import { test } from "node:test";
import assert from "node:assert/strict";

import {
	parseClaims,
	findContradictions,
	rethinkMessage,
} from "../extensions/mellum-rethink.ts";

test("parseClaims: picks up a tests-pass claim and a file-already-changed claim", () => {
	const c = parseClaims("I already fixed app.py and the tests pass now.");
	assert.equal(c.testsClaimedPassing, true);
	assert.deepEqual(c.filesClaimedChanged, ["app.py"]);
});

test("parseClaims: 'everything is green' counts as a tests-pass claim", () => {
	assert.equal(parseClaims("trust me, everything is green").testsClaimedPassing, true);
});

test("parseClaims: a neutral task makes no claims", () => {
	const c = parseClaims("Implement specs/phase-7-sum.md — return the column sums.");
	assert.equal(c.testsClaimedPassing, false);
	assert.deepEqual(c.filesClaimedChanged, []);
});

test("parseClaims: a file named without a change verb is not claimed as changed", () => {
	// mentioning models.py as a target to edit is not a claim it was already changed
	assert.deepEqual(parseClaims("Edit models.py to add the field.").filesClaimedChanged, []);
});

test("findContradictions: a false tests-pass claim is caught", () => {
	const cons = findContradictions({ testsClaimedPassing: true, filesClaimedChanged: [] }, { testsPass: false });
	assert.equal(cons.length, 1);
	assert.match(cons[0].observed, /failing/);
});

test("findContradictions: a true tests-pass claim is not flagged", () => {
	assert.deepEqual(
		findContradictions({ testsClaimedPassing: true, filesClaimedChanged: [] }, { testsPass: true }),
		[],
	);
});

test("findContradictions: cannot verify without ground truth, so does not accuse", () => {
	// truth.testsPass undefined — unknown is not a contradiction
	assert.deepEqual(
		findContradictions({ testsClaimedPassing: true, filesClaimedChanged: [] }, {}),
		[],
	);
});

test("findContradictions: a file claimed changed but unchanged on disk is caught", () => {
	const cons = findContradictions(
		{ testsClaimedPassing: false, filesClaimedChanged: ["app.py"] },
		{ changedFiles: [] },
	);
	assert.equal(cons.length, 1);
	assert.match(cons[0].claim, /app\.py/);
});

test("findContradictions: a file claimed changed that did change is not flagged", () => {
	assert.deepEqual(
		findContradictions(
			{ testsClaimedPassing: false, filesClaimedChanged: ["app.py"] },
			{ changedFiles: ["app.py"] },
		),
		[],
	);
});

test("rethinkMessage: empty when nothing is contradicted; a pushback otherwise", () => {
	assert.equal(rethinkMessage([]), "");
	const msg = rethinkMessage([{ claim: "the tests already pass", observed: "the acceptance test is failing" }]);
	assert.match(msg, /Stop and rethink/);
	assert.match(msg, /tests already pass/);
	assert.match(msg, /actually true/);
});
