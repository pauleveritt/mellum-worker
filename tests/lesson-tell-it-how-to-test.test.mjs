import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const ROOT = resolve(import.meta.dirname, "..");
const page = (p) => readFileSync(resolve(ROOT, "learn", p), "utf8");
const BADGE = (s) => /^\*\*Badge:\*\* `(reference-run|cited|screen|conjecture)`$/m.test(s);

test("the fifth findings lesson follows the six steps and names its badge", () => {
  const l = page("lessons/medium/tell-it-how-to-test.md");
  const heads = [...l.matchAll(/^## (.+)$/gm)].map((m) => m[1]);
  assert.deepEqual(heads, ["Problem", "Eval case", "Evidence of the problem",
    "Solution", "Validation", "Interpretation"]);
  const sections = l.split(/^## /m).slice(1);
  sections.forEach((s, i) => assert.equal(BADGE(s), i < 5, `step ${i + 1}`));
  assert.match(l, /weakest badge is `(?:reference-run|cited|screen|conjecture)`/);
  assert.match(l, /^track: lessons$/m);
  assert.match(l, /^position: 1$/m);
  assert.match(l, /^backends: \[llamacpp\]$/m);
});

test("the facts lesson is a null with the injection count beside it", () => {
  const l = page("lessons/medium/tell-it-how-to-test.md");
  assert.ok(!/docs\/ladder\//.test(l), "lesson links a ladder record");
  assert.ok(!/ablation-a/.test(l), "lesson cites an ablation");
  for (const text of ["Project facts:", "MELLUM_MODE_FACTS", "26/26", "0/51",
    "Do not: start servers", "null"])
    assert.ok(l.includes(text), `lesson lacks ${text}`);
  assert.match(l, /llama\.cpp/);
  assert.match(page("lessons/medium/index.md"), /tell-it-how-to-test\.md/);
});
