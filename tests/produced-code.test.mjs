import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import { producedCode } from "../extensions/mellum-lessons.ts";

// A run dir as the harness lays it out: <runs>/<stamp>-<name>-<hex>/workspace/…
function run(runs, stamp, files) {
  const ws = join(runs, `${stamp}-add-abc123`, "workspace");
  mkdirSync(ws, { recursive: true });
  for (const [rel, text] of Object.entries(files)) {
    const p = join(ws, rel);
    mkdirSync(join(p, ".."), { recursive: true });
    writeFileSync(p, text);
  }
  return ws;
}

test("producedCode returns the newest run's solution file, not the grader test", () => {
  const runs = mkdtempSync(join(tmpdir(), "produced-"));
  run(runs, "20261030T120000Z", {
    "add.py": "def add(a, b):\n    return a - b\n",
    "task.md": "# add",
    "tests/test_add.py": "assert add(2, 3) == 5\n",
  });
  const got = producedCode(runs);
  assert.equal(got?.name, "add.py");
  assert.match(got.text, /return a - b/);
});

test("producedCode reads the latest run when several exist", () => {
  const runs = mkdtempSync(join(tmpdir(), "produced-"));
  run(runs, "20261030T120000Z", { "add.py": "def add(a, b):\n    return a - b\n" });
  run(runs, "20261030T120005Z", { "add.py": "def add(a, b):\n    return a + b\n" });
  assert.match(producedCode(runs).text, /return a \+ b/);
});

test("producedCode is undefined when no run has a solution file", () => {
  const runs = mkdtempSync(join(tmpdir(), "produced-"));
  assert.equal(producedCode(runs), undefined);
});
