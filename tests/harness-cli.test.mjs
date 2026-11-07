import { spawnSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const ROOT = resolve(import.meta.dirname, "..");
const FIX = resolve(ROOT, "learn/code/tests/fixtures");
const SUITES = resolve(FIX, "suites");

const run = (runs, binary, ...extra) => spawnSync("uv", [
  "run", "learn/code/harness.py", "run", "--suite", "add",
  "--suites-dir", SUITES, "--runs-dir", runs, "--pi-binary", resolve(FIX, binary),
  ...extra,
], { cwd: ROOT, encoding: "utf8" });

test("a passing run prints one score line", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi.sh");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: PASS \(n=1; run .+; \d+ requests, \d+ tool calls, \d+ tool errors, \d+ nudges\)$/m);
});

test("a failing run says FAIL and shows the test tail", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi-empty.sh");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: FAIL \(n=1; run .+; \d+ requests, \d+ tool calls, \d+ tool errors, \d+ nudges\)$/m);
  assert.match(r.stderr, /failed|error/i);
});

test("--dry-run prints the child's argv", () => {
  const r = run(tmpdir(), "fake-pi.sh", "--dry-run");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /-p .*mellum-recorder\.ts/);
});

test("suite all prints every task and a total", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = spawnSync("uv", ["run", "learn/code/harness.py", "run", "--suite", "all",
    "--suites-dir", SUITES, "--runs-dir", runs,
    "--pi-binary", resolve(FIX, "fake-pi.sh"),
  ], { cwd: ROOT, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: PASS/m);
  assert.match(r.stdout, /^mul: PASS/m);
  assert.match(r.stdout, /^2\/2 suites passed \(2\/2 sessions\)$/m);
});

test("--grade prints one line per grader beside the score", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi.sh", "--grade");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: PASS/m);
  for (const tool of ["ruff", "complexipy"])
    assert.match(r.stdout, new RegExp(`^${tool}: PASS$`, "m"));
  assert.match(r.stdout, /^pyrefly \(advisory\): PASS$/m);
});

test("a lint failure fails the session", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi-unused-import.sh", "--grade");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: FAIL/m);
  assert.match(r.stdout, /^ruff: FAIL/m);
  assert.match(r.stdout, /^pyrefly \(advisory\): PASS$/m);
});

test("without --grade there are no grader lines", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi.sh");
  assert.doesNotMatch(r.stdout, /^ruff:/m);
});

test("--repeat runs the session twice and reports n", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi.sh", "--repeat", "2");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add \[1\/2\]: PASS/m);
  assert.match(r.stdout, /^add \[2\/2\]: PASS/m);
  assert.match(r.stdout, /^add: 2\/2 sessions passed$/m);
});

test("--repeat reports a failure per session", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi-empty.sh", "--repeat", "2");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: 0\/2 sessions passed$/m);
});

test("suite counts tasks and sessions", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = spawnSync("uv", ["run", "learn/code/harness.py", "run", "--suite", "all",
    "--suites-dir", SUITES, "--runs-dir", runs, "--pi-binary", resolve(FIX, "fake-pi.sh"),
    "--repeat", "2",
  ], { cwd: ROOT, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^2\/2 suites passed \(4\/4 sessions\)$/m);
});

test("--deadline stops a session and says so", () => {
  const runs = mkdtempSync(join(tmpdir(), "mellum-runs-"));
  const r = run(runs, "fake-pi-slow.sh", "--deadline", "1");
  assert.equal(r.status, 0, r.stderr);
  assert.match(r.stdout, /^add: FAIL .*deadline\)$/m);
});
