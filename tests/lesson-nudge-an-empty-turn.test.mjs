import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const ROOT = resolve(import.meta.dirname, "..");
const page = (p) => readFileSync(resolve(ROOT, "learn", p), "utf8");
const BADGE = (s) => /^\*\*Badge:\*\* `(reference-run|cited|screen|conjecture)`$/m.test(s);

test("the fourth findings lesson follows the six steps and names its badge", () => {
  const l = page("lessons/medium/nudge-an-empty-turn.md");
  const heads = [...l.matchAll(/^## (.+)$/gm)].map((m) => m[1]);
  assert.deepEqual(heads, ["Problem", "Eval case", "Evidence of the problem",
    "Solution", "Validation", "Interpretation"]);
  const sections = l.split(/^## /m).slice(1);
  sections.forEach((s, i) => assert.equal(BADGE(s), i < 5, `step ${i + 1}`));
  assert.match(l, /^### Evidence of the solution$/m);
  assert.match(l, /weakest badge is `screen`/);
  assert.match(l, /^track: lessons$/m);
  assert.match(l, /^position: 3$/m);
  assert.match(l, /^backends: \[llamacpp\]$/m);
});

test("the guards lesson is re-based on llama.cpp and cites no oMLX record", () => {
  const l = page("lessons/medium/nudge-an-empty-turn.md");
  assert.ok(!/docs\/ladder\//.test(l), "lesson links a ladder record");
  assert.ok(!/ablation-a/.test(l), "lesson cites an ablation");
  for (const text of ["nudge never fired", "Nudges", "`error`", "`length`",
    "`stop`", "void for its question"])
    assert.ok(l.includes(text), `lesson lacks ${text}`);
  assert.match(l, /llama\.cpp/);
});

test("the guards lesson quotes the real nudge, not a paraphrase", () => {
  const l = page("lessons/medium/nudge-an-empty-turn.md");
  const code = l.match(/```ts\n([\s\S]*?)```/)?.[1] ?? "";
  assert.match(code, /function createEmptyFinalNudge/);
  assert.match(code, /used >= max/);
  assert.match(code, /NUDGE_TEXT/);
  assert.match(l, /blob\/[0-9a-f]{7,}\/extensions\/mellum-guards\.ts#L\d+-L\d+/);
  assert.match(page("lessons/medium/index.md"), /nudge-an-empty-turn\.md/);
});
