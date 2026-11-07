import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const ROOT = resolve(import.meta.dirname, "..");

test("the harness's Python tests pass under uv run", () => {
  const r = spawnSync("uv", ["run", "--with", "pytest", "python", "-m",
    "pytest", "tests", "-q", "--ignore=tests/fixtures"], {
    cwd: resolve(ROOT, "learn/code"), encoding: "utf8",
  });
  assert.equal(r.status, 0, r.stdout + r.stderr);
});
