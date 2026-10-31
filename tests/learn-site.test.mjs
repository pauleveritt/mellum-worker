// Retired: "the baseline shows the actual worker code" (learn/lessons/easy/baseline.md) and tests/lesson-write-only-listed.test.mjs (learn/lessons/easy/write-only-listed.md); both pages removed 2026-10-29 by the tiered-track restructure.
import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

const ROOT = resolve(import.meta.dirname, "..");
const page = (p) => readFileSync(resolve(ROOT, "learn", p), "utf8");
const PAGES = [
  "index.md",
  "about/index.md",
  "about/how-to-read.md",
  "about/evidence.md",
  "about/contributing.md",
  "glossary.md",
  "credits.md",
  "pathologies.md",
  "getting-started/index.md",
  "getting-started/base-pi-on-llamacpp.md",
  "getting-started/troubleshoot.md",
  "getting-started/working-with-pi.md",
  "getting-started/eval-suites.md",
  "getting-started/extensions.md",
  "lessons/start-here.md",
  "lessons/index.md",
  ...["easy", "medium", "hard"].flatMap((tier) =>
    readdirSync(resolve(ROOT, "learn/lessons", tier))
      .filter((f) => f.endsWith(".md"))
      .sort()
      .map((f) => `lessons/${tier}/${f}`)),
  "lesson-template.md",
  "project/index.md",
  "project/toolchain.md",
];

test("zensical.toml points docs_dir at learn/", () => {
  const toml = readFileSync(resolve(ROOT, "zensical.toml"), "utf8");
  assert.match(toml, /^docs_dir = "learn"$/m);
  assert.match(toml, /^site_name = "Small AI Learning Center"$/m);
});

test("every required page exists and is in the nav", () => {
  const toml = readFileSync(resolve(ROOT, "zensical.toml"), "utf8");
  for (const p of PAGES) {
    assert.ok(existsSync(resolve(ROOT, "learn", p)), `learn/${p} missing`);
    assert.ok(toml.includes(`"${p}"`), `learn/${p} not in nav`);
  }
});

test("the glossary is parsed by zensical-glossary", () => {
  const toml = readFileSync(resolve(ROOT, "zensical.toml"), "utf8");
  assert.match(toml, /\[project\.markdown_extensions\.zensical_glossary\]/);
  assert.match(toml, /glossary_file = "glossary\.md"/);
  assert.match(toml, /heading_level = 3/);
  assert.match(toml, /first_only = true/);
  assert.match(toml, /pymdownx\.superfences = \{\}/);
  const glossary = page("glossary.md");
  for (const term of ["screen", "nudge", "empty-final nudge", "no-nudge",
    "Baseline Worker", "Baseline Pi"])
    assert.match(glossary, new RegExp(`^### ${term}$`, "mi"));
});

test("the site build runs from the project virtualenv", () => {
  const readme = readFileSync(resolve(ROOT, "README.md"), "utf8");
  assert.match(readme, /uv run zensical build/);
  assert.match(readme, /uv run zensical serve/);
  assert.doesNotMatch(readme, /uvx[^\n]*zensical/);
});

test("the glossary extension is a declared dev dependency", () => {
  const pyproject = readFileSync(resolve(ROOT, "pyproject.toml"), "utf8");
  const group = pyproject.match(/^\[dependency-groups\]\n([\s\S]*?)(?=^\[|\Z)/m);
  assert.ok(group, "pyproject.toml declares no [dependency-groups]");
  for (const dep of ["\"zensical\"", "\"zensical-glossary\""])
    assert.ok(group[1].includes(dep), `dev group lacks ${dep}`);
});

test("CI builds the site with uv run, not uvx", () => {
  const ci = readFileSync(resolve(ROOT, ".github/workflows/docs.yml"), "utf8");
  assert.match(ci, /uv run zensical build/);
  assert.doesNotMatch(ci, /uvx/);
  assert.match(ci, /pyproject\.toml/);
});

test("credits name both authors and Tina4", () => {
  const c = page("credits.md");
  assert.match(c, /a collaboration between Paul Everitt and Andre van Zuydam/);
  assert.match(c, /\[Tina4\]\(https?:\/\//);
});

test("evidence page defines all four badges", () => {
  const e = page("about/evidence.md");
  for (const b of ["reference-run", "cited", "screen", "conjecture"])
    assert.ok(e.includes(`\`${b}\``), `badge ${b} missing`);
});

const STEPS = ["Problem", "Eval case", "Evidence of the problem",
  "Solution", "Validation", "Interpretation"];

test("the lesson template has the six steps in order, badges on 1-5", () => {
  const t = page("lesson-template.md");
  const heads = [...t.matchAll(/^## (.+)$/gm)].map((m) => m[1]);
  assert.deepEqual(heads, STEPS);
  const sections = t.split(/^## /m).slice(1);
  sections.forEach((s, i) =>
    assert.equal(/\*\*Badge:\*\*/.test(s), i < 5, `step ${i + 1} badge`));
});

test("lesson 1 numbers every step and fetches every grader", () => {
  const l = page("getting-started/base-pi-on-llamacpp.md");
  const numbers = [...l.matchAll(/^## (\d+)\./gm)].map((m) => Number(m[1]));
  assert.deepEqual(numbers, [1, 2, 3, 4, 5, 6, 7]);
  assert.match(l, /^## 3\. Fetch the tools/m);
  assert.match(l, /uvx complexipy --version/);
  assert.doesNotMatch(l, /PowerShell profile line in\s+step 7/);
});

test("troubleshooting is a standalone Getting Started page", () => {
  const t = page("getting-started/troubleshoot.md");
  assert.match(t, /^track: getting-started$/m);
  assert.match(t, /^prerequisites: \[\]$/m);
});

test("the home page links the Introduction and counts five lessons", () => {
  const index = page("index.md");
  assert.match(index, /\[Introduction\]\(introduction\/index\.md\): Demystifying/);
  assert.match(index, /five steps/);
  assert.doesNotMatch(index, /three (lessons|steps)/);
});

test("lesson 1 walks from uv to a base-Pi answer", () => {
  const l = page("getting-started/base-pi-on-llamacpp.md");
  assert.match(l, /^track: getting-started$/m);
  const order = [
    "install uv", "pyproject.toml", "uvx ruff",
    "uv run scripts/backend.py start", "uv run scripts/backend.py chat",
    "PI_CODING_AGENT_DIR",
  ];
  let at = -1;
  for (const step of order) {
    const next = l.toLowerCase().indexOf(step.toLowerCase());
    assert.ok(next > at, `${step} missing or out of order`);
    at = next;
  }
  for (const text of ["--no-extensions", "--no-context-files", "--no-session",
    "backend.py stop", "learn/code/profile"])
    assert.ok(l.includes(text), `lesson 1 lacks ${text}`);
  const index = page("getting-started/index.md");
  assert.ok(index.includes("base-pi-on-llamacpp.md"), "index does not link lesson 1");
  assert.doesNotMatch(index, /coming/);
});

test("the Getting Started index points to troubleshooting", () => {
  assert.match(page("getting-started/index.md"), /troubleshoot\.md/);
});

test("the project pages orient a maintainer and name the checks", () => {
  const index = page("project/index.md");
  for (const text of ["scripts/backend.py", "docs/sdd.md", "AGENTS.md"])
    assert.ok(index.includes(text), `project index lacks ${text}`);
  const toolchain = page("project/toolchain.md");
  for (const text of ["pyproject.toml", "[tool.mellum]",
    "uv run scripts/backend.py", "PI_CODING_AGENT_DIR", "npm test",
    "uv run pytest", "uv run zensical build"])
    assert.ok(toolchain.includes(text), `toolchain lacks ${text}`);
});

test("Build a Harness explains isolation and the one command", () => {
  const l = page("getting-started/the-harness.md");
  assert.match(l, /^track: getting-started$/m);
  const order = ["fresh directory", "harness.py run --suite easy",
    "n=1", "--repeat 3"];
  let at = -1;
  for (const step of order) {
    const next = l.toLowerCase().indexOf(step.toLowerCase());
    assert.ok(next > at, `${step} missing or out of order`);
    at = next;
  }
  for (const text of ["hidden", "score line", "trace.jsonl",
    "sessions passed", "not a rate", "temperature 1.0", "top_p 0.95",
    "top_k 20", "max_tokens 16384", "context 50000"])
    assert.ok(l.toLowerCase().includes(text), `lesson 2 lacks ${text}`);
  assert.match(page("getting-started/index.md"), /the-harness\.md/);
});

test("lesson 3 runs the suite, grading and the trace", () => {
  const l = page("getting-started/eval-suites.md");
  assert.match(l, /^track: getting-started$/m);
  for (const text of ["run --suite all --grade", "ruff", "pyrefly", "complexipy",
    "trace.jsonl", "three", "graders", "one observation"])
    assert.ok(l.toLowerCase().includes(text), `lesson 3 lacks ${text}`);
  assert.match(page("getting-started/index.md"), /eval-suites\.md/);
});

test("the Lessons index introduces the three tiers", () => {
  const index = page("lessons/index.md");
  for (const tier of ["easy", "medium", "hard"]) assert.match(index, new RegExp(`\\(${tier}/index\\.md\\)`));
  assert.match(index, /grid cards/);
  assert.doesNotMatch(index, /old numbers|retired/i);
});

test("the lesson template asks for evidence and records the conventions", () => {
  const t = page("lesson-template.md");
  assert.match(t, /^### Evidence of the solution$/m);
  for (const text of ["Passes", "Turns", "Failed checks", "Tool errors",
    "Context", "Wall", "Output tokens"])
    assert.ok(t.includes(text), `template lacks ${text}`);
  assert.match(t, /^### Quality and budget$/m);
  assert.match(t, /^### What to try next$/m);
  assert.match(t, /^### The code$/m);
  assert.match(t, /nudge fires/i);
  assert.ok(t.includes("```ts"), "template lacks a code sample");
  assert.match(t, /n = 1/);
  for (const text of ["### Repository conventions",
    "tests/lesson-<slug>.test.mjs", "Do not copy a production source file",
    "line range"])
    assert.ok(t.includes(text), `template lacks ${text}`);
});

test("the extensions page teaches the extension mechanism and remedy units", () => {
  const l = page("getting-started/extensions.md");
  for (const text of ["A Pi extension", "registerCommand", "pi.on",
    "before_provider_request", "tool_call", "agent_before_settle", "registerTool",
    "context", "callback", "/mellum", "runaway search", "remedies/<kind>/",
    "meta", "remedies/presets/", "preset:easy", "--remedy", "--extension",
    "/remedy", "baseline-worker"])
    assert.ok(l.toLowerCase().includes(text.toLowerCase()), `extensions page lacks ${text}`);
  assert.doesNotMatch(l, /assert True|Run it on the ditch|n = 1/);
  assert.match(page("getting-started/index.md"), /extensions\.md/);
});

test("Working With Pi covers the basics and the course's two commands", () => {
  const l = page("getting-started/working-with-pi.md");
  for (const text of ["/quit", "Ctrl+D", "Shift+Enter", "Escape", "read", "bash",
    "edit", "write", "grep", "find", "ls", "Ctrl+O", "pi --continue", "/resume",
    "/tree", "/fork", "/model", "/trust", ".pi/extensions", "/lesson", "/lesson S0",
    "/remedy on guard/break-repeat-loops", "/remedy off", "/remedy preset:easy",
    "remedies: N on"])
    assert.ok(l.includes(text), `Working With Pi lacks ${text}`);
  assert.match(page("getting-started/index.md"), /working-with-pi\.md/);
  assert.match(page("getting-started/base-pi-on-llamacpp.md"), /\(working-with-pi\.md\)/);
});

test("the second findings lesson follows the six steps and names its badge", () => {
  const l = page("lessons/medium/a-short-prompt.md");
  const heads = [...l.matchAll(/^## (.+)$/gm)].map((m) => m[1]);
  assert.deepEqual(heads, ["Problem", "Eval case", "Evidence of the problem",
    "Solution", "Validation", "Interpretation"]);
  const sections = l.split(/^## /m).slice(1);
  const badge = (s) => /^\*\*Badge:\*\* `(reference-run|cited|screen|conjecture)`$/m.test(s);
  sections.forEach((s, i) => assert.equal(badge(s), i < 5, `step ${i + 1}`));
  assert.match(l, /weakest badge is `(?:reference-run|cited|screen|conjecture)`/);
  assert.ok(!/docs\/ladder\//.test(l), "lesson links a ladder record");
  assert.match(page("lessons/medium/index.md"), /a-short-prompt\.md/);
});

test("learn/ never says tutorial or case study", () => {
  for (const p of PAGES)
    assert.doesNotMatch(page(p), /tutorial|case stud/i, p);
});

test("reference-run is earned on the suites, not the ladder", () => {
  const evidence = page("about/evidence.md");
  const row = evidence.split("\n").find((l) => l.startsWith("| `reference-run`"));
  assert.ok(row, "no reference-run row");
  assert.match(row, /preregistration/);
  assert.doesNotMatch(row, /docs\/ladder\//);
  assert.match(evidence.split("\n").find((l) => l.startsWith("| `cited`")), /docs\/ladder\//);
  const entry = page("glossary.md").split("### Reference-run")[1].split("###")[0];
  assert.match(entry, /preregistered run on llama\.cpp/);
  assert.doesNotMatch(entry, /ladder run/);
});

test("the harness is the measured instrument", () => {
  const harness = page("getting-started/the-harness.md");
  assert.doesNotMatch(harness, /`ladder\/` is the measured instrument/);
  assert.doesNotMatch(harness, /do not replace `docs\/ladder\/`/);
  assert.match(harness, /`learn\/code\/harness\.py` is the measured instrument/);
  assert.doesNotMatch(page("project/index.md"), /\*\*The ladder\*\*/);
  assert.match(page("project/toolchain.md"), /Measured work lands in `docs\/superpowers\/research\/`/);
  assert.doesNotMatch(page("getting-started/the-harness.md"), /ladder is the measuring/);
  assert.doesNotMatch(page("getting-started/eval-suites.md"), /Rates come from the ladder/);
  assert.doesNotMatch(page("getting-started/eval-suites.md"), /The ladder is the measuring instrument/);
});

test("the run record groups the failed checks by module", () => {
  const suite = page("getting-started/eval-suites.md");
  assert.match(suite, /grader module/);
  assert.match(suite, /missing_checks|expected tests that did not pass/);
  const harness = page("getting-started/the-harness.md");
  assert.match(harness, /--specs joined\|split/);
  assert.match(harness, /spec-variants|spec variant/);
  const entry = page("glossary.md").split("### Failed checks")[1].split("###")[0];
  assert.match(entry, /module/);
  assert.match(suite, /checks_ran: false/);
  assert.match(page("glossary.md"), /^### checks did not run$/mi);
});

test("the lesson template opens with the two-sentence paragraph", () => {
  const t = page("lesson-template.md");
  const opening = t.split(/^# .+$/m)[1].split(/^## |^!!! /m)[0].replace(/```[\s\S]*?```/g, "").trim();
  assert.ok(opening.length > 0, "template has no opening paragraph");
  assert.equal(opening.split(/(?<=\.)\s+/).filter(Boolean).length, 2);
  assert.ok(opening.split(/\s+/).length <= 45, "opening is over 45 words");
  assert.match(t, /two-sentence paragraph/);
});

test("a lesson screen is sized by what it reads", () => {
  const lessons = PAGES.filter((p) => /^lessons\/(easy|medium|hard)\/(?!index\.md$)/.test(p));
  for (const p of lessons) {
    const l = page(p).replace(/\s+/g, " ");
    // The rule is about the evidence the page rests on, so it reads the
    // Validation step; an Interpretation may still describe a retired screen.
    const evidence = l.split("## Validation")[1]?.split("## Interpretation")[0] ?? "";
    const nOne = /\bn ?= ?1\b/.test(evidence);
    if (nOne) {
      // One session settles presence; it cannot support an absence or a comparison.
      assert.doesNotMatch(evidence, /\bnull\b/i, `${p}: n = 1 cannot be a null`);
      assert.doesNotMatch(evidence, /\bvoid\b/i, `${p}: n = 1 cannot be a void arm`);
      assert.doesNotMatch(evidence, /\bseparat(?:ed|es|ion)\b/i, `${p}: n = 1 cannot claim separation`);
    }
    // A lesson with no arm says so instead of quoting an n.
    if (/\bno arm\b/i.test(l)) continue;
    // Every other lesson states the size of its evidence somewhere.
    assert.match(
      l,
      /\bn ?= ?[1-9]\b|\b(?:one|two|three|four|five|ten|45)[ -](?:session|sessions)\b|sessions per arm/,
      `${p}: states no n for its evidence`,
    );
  }
});

test("every lesson page opens with the two-sentence paragraph", () => {
  const lessons = PAGES.filter((p) => /^lessons\/(easy|medium|hard)\/(?!index\.md$)/.test(p));
  assert.ok(lessons.length >= 8, "lesson discovery found too few pages");
  for (const p of lessons) {
    const l = page(p);
    const opening = l.split(/^# .+$/m)[1].split(/^## |^!!! /m)[0].trim();
    assert.ok(opening.length > 0, `${p} has no opening paragraph`);
    assert.equal(opening.split(/(?<=\.)\s+/).filter(Boolean).length, 2, `${p} opening is not two sentences`);
    assert.ok(opening.split(/\s+/).length <= 45, `${p} opening is over 45 words`);
    assert.doesNotMatch(opening, /`|\]\(|\*\*Badge/, `${p} opening carries markup`);
  }
});

test("Start Here teaches reading a failed session (folded in from Read the Failure)", () => {
  const l = page("lessons/start-here.md");
  for (const text of ["checks_ran", "stalled", "trace.jsonl", "pathologies-and-their-remedies",
    "Nine bare sessions", "foreground"])
    assert.ok(l.includes(text), `Start Here lacks ${text}`);
  assert.doesNotMatch(l, /Lesson E2/);
});

test("the harness is a Getting Started page, not a lesson (it applies no remedy)", () => {
  const l = page("getting-started/the-harness.md");
  assert.match(l, /^track: getting-started$/m);
  assert.doesNotMatch(l, /^number:/m);
  assert.doesNotMatch(l, /\*\*Remedy unit:\*\*|\*\*Lesson check:\*\*/);
  assert.match(page("getting-started/index.md"), /the-harness\.md/);
});

test("the Hard index opens with who drives, folded in from the lesson that left the track", () => {
  const index = page("lessons/hard/index.md");
  assert.match(index, /## Who drives/);
  assert.match(index.replace(/\s+/g, " "), /confident final over work it never checked/);
  assert.match(index, /2026-10-29-lessons-left-the-track\.md/);
  assert.doesNotMatch(index, /who-drives\.md|the-handoff\.md/);
  const backlog = readFileSync(new URL("../BACKLOG.md", import.meta.url), "utf8");
  assert.match(backlog, /\*\*The handoff block as a unit\.\*\*[\s\S]*?\*Reopens when\*/);
});
