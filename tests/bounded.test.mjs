import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import test from "node:test";

import { runBounded } from "../extensions/bounded.ts";

test("a command that finishes returns its exit code and output", () => {
	const r = runBounded("sh", ["-c", "echo hi; echo err >&2; exit 3"], { cwd: tmpdir(), timeoutMs: 5000 });
	assert.equal(r.started, true);
	assert.equal(r.timedOut, false);
	assert.equal(r.code, 3);
	assert.match(r.out, /hi/);
	assert.match(r.out, /err/);
});

test("a command that hangs is killed with its whole process group at the timeout", () => {
	const marker = `sleep 31.${process.pid % 1000}`;
	const t0 = Date.now();
	// The shell backgrounds a child and waits: killing only the shell would leave the child running.
	const r = runBounded("sh", ["-c", `${marker} & ${marker} & wait`], { cwd: tmpdir(), timeoutMs: 1000 });
	assert.equal(r.timedOut, true);
	assert.ok(Date.now() - t0 < 4000, `took ${Date.now() - t0} ms`);
	let left = "";
	try {
		left = execFileSync("pgrep", ["-f", marker], { encoding: "utf8" });
	} catch {
		left = ""; // pgrep exits 1 when nothing matches
	}
	assert.equal(left.trim(), "", "no process of the group is left behind");
});

const left = (marker) => {
	try {
		return execFileSync("pgrep", ["-f", marker], { encoding: "utf8" }).trim();
	} catch {
		return ""; // pgrep exits 1 when nothing matches
	}
};

test("a command that exits while a child it started still holds the pipe reports its own exit code", () => {
	const marker = `sleep 47.${process.pid % 1000}`;
	const t0 = Date.now();
	// A test run that passes but leaves a server inheriting its stdout: the pass must not read as a timeout.
	const r = runBounded("sh", ["-c", `${marker} & echo passed; exit 0`], { cwd: tmpdir(), timeoutMs: 3000 });
	assert.equal(r.timedOut, false);
	assert.equal(r.code, 0);
	assert.match(r.out, /passed/);
	assert.ok(Date.now() - t0 < 2500, `took ${Date.now() - t0} ms`);
	assert.equal(left(marker), "", "the child is stopped with the group");
});

test("a child with its output redirected does not outlive the call", () => {
	const marker = `sleep 48.${process.pid % 1000}`;
	const r = runBounded("sh", ["-c", `${marker} >/dev/null 2>&1 & exit 0`], { cwd: tmpdir(), timeoutMs: 3000 });
	assert.equal(r.code, 0);
	assert.equal(left(marker), "", "a server a check started cannot hold the port for the next launch");
});

test("a command that cannot start says so instead of reading as red", () => {
	const r = runBounded("no-such-binary-r1", [], { cwd: tmpdir(), timeoutMs: 5000 });
	assert.equal(r.started, false);
	assert.equal(r.timedOut, false);
});
