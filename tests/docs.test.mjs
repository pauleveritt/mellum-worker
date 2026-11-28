import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";
import { formatMerge, formatReport, learnFromTexts, mergeSuggestion } from "../extensions/mellum-learn.ts";

const ROOT = resolve(import.meta.dirname, "..");
const read = (p) => readFileSync(resolve(ROOT, p), "utf8");

test("the README links the Getting Started steps", () => {
  const readme = read("README.md");
  for (const page of ["base-pi-on-llamacpp", "working-with-pi", "eval-suites", "extensions"])
    assert.ok(readme.includes(`learn/getting-started/${page}.md`),
      `README lacks the ${page} lesson`);
  assert.ok(readme.includes("learn/code/harness.py run --suite all --grade"),
    "README lacks the harness command");
});

test("README carries the pinned install line and the status table", () => {
	const readme = read("README.md");
	const version = JSON.parse(read("package.json")).version;
	assert.ok(readme.includes(`pi install git:github.com/andrevanzuydam/mellum-worker@v${version}`));
	assert.match(readme, /15\/15/);
	assert.match(readme, /unmeasured/i);
	assert.match(readme, /uv run --offline pytest -q/);
});

test("every relative markdown link in docs and README resolves", () => {
	for (const file of ["README.md", "docs/recipe.md", "docs/backends/omlx.md", "docs/backends/ollama.md"]) {
		const dir = resolve(ROOT, file, "..");
		for (const m of read(file).matchAll(/\]\(([^)#:]+)(?:#[^)]*)?\)/g)) {
			assert.ok(existsSync(resolve(dir, m[1])), `${file}: broken link ${m[1]}`);
		}
	}
});

test("README Use it says how to run the setup check in Pi Mode and from the terminal", () => {
	const use = read("README.md").split("\n## Use it\n")[1].split("\n## What you get\n")[0];
	assert.match(use, /\*\*Check your setup\.\*\*/);
	assert.ok(use.includes("/mellum check"), "names /mellum check");
	assert.ok(use.includes("scripts/mellum.mjs check --host pi"), "names the CLI for Pi");
	for (const fence of use.matchAll(/```bash\n([\s\S]*?)```/g)) assert.doesNotMatch(fence[1], /\w\|\w/, "no a|b alternation in a bash fence");
	assert.match(use, /exit/i, "says how it exits");
	assert.ok(use.includes("Mellum server settings differ"), "shows the activation warning");
});

test("README Use it says how to run learn in Pi Mode and from the terminal, after the check", () => {
	const use = read("README.md").split("\n## Use it\n")[1].split("\n## What you get\n")[0];
	const at = use.indexOf("**Learn from your runs.**");
	assert.ok(at > use.indexOf("**Check your setup.**"), "a Learn from your runs paragraph after Check your setup");
	const learn = use.slice(at);
	assert.ok(learn.includes("/mellum learn"), "names /mellum learn");
	assert.ok(learn.includes("/mellum learn 25"), "shows the run count");
	assert.ok(learn.includes("scripts/mellum.mjs learn [--n 10] [--file <jsonl>] [--json]"), "names the CLI and its flags");
	assert.ok(learn.includes("AGENTS.md"), "says where the suggestion goes");
	assert.ok(learn.includes("MELLUM_MODE_RUNS"), "says where the records live");
	assert.match(learn, /from\s+the\s+project\s+directory/, "says to run the CLI from the project directory");
	for (const fence of learn.matchAll(/```bash\n([\s\S]*?)```/g)) assert.doesNotMatch(fence[1], /\w\|\w/, "no a|b alternation in a bash fence");
});

test("README Use it says how to see the last run in Pi and from the terminal, after learn", () => {
	const use = read("README.md").split("\n## Use it\n")[1].split("\n## What you get\n")[0];
	const at = use.indexOf("**See the last run.**");
	assert.ok(at > use.indexOf("**Learn from your runs.**"), "a See the last run paragraph after Learn from your runs");
	const last = use.slice(at);
	assert.ok(last.includes("/mellum last"), "names /mellum last");
	assert.ok(last.includes("scripts/mellum.mjs last [--file <jsonl>] [--json]"), "names the CLI and its flags");
	assert.ok(last.includes("| Metric | Value |"), "shows the table");
	assert.match(last, /no record/, "says bare-Pi runs write no record");
});

test("README Model settings says which values the provider entry sends per request and which only the server sets", () => {
	const use = read("README.md").split("\n## Use it\n")[1].split("\n## What you get\n")[0];
	const settings = use.split("**Model settings.**")[1].split("**Check your setup.**")[0];
	assert.match(settings, /Pi\s+sends[^.]*per\s+request/);
	assert.match(settings, /force_sampling/);
	assert.match(settings, /honours/);
	assert.match(settings, /server-only/);
	const check = use.split("**Check your setup.**")[1].split("**Learn from your runs.**")[0];
	assert.match(check, /Mellum server settings differ: (max_context_window|turboquant_kv_enabled) /, "the warning example names a server-only key");
	assert.match(check, /info/, "says overridden server values are info");
});

test("README What helped follows the rungs 6-9 results, and the results table no longer repeats it", () => {
	const readme = read("README.md");
	const get = readme.split("\n## What you get\n")[1].split("\n## ")[0];
	const helped = readme.split("\n## What helped\n")[1]?.split("\n## ")[0];
	assert.ok(helped, "a What helped section");
	assert.ok(readme.indexOf("\n## What helped\n") > readme.indexOf("\n## What you get\n"));
	assert.ok(readme.indexOf("\n## What helped\n") < readme.indexOf("\n## Findings\n"));
	for (const row of [
		"| AgentClinic, 12 runs each | no facts | fallback only | `## Mellum` section |",
		"| passed | 1 | 7 | 9 |",
		"| requests, median | 50 | 28 | 26 |",
		"| seconds, median | 261 | 143 | 106 |",
		"| wrote outside the layout | 8 | 5 | 0 |",
	]) {
		assert.ok(helped.includes(row), `What helped lacks ${row}`);
	}
	assert.match(helped, /Rungs 1–5 did not regress \(15\/15\)/);
	assert.match(get, /A18/, "What you get still links the A18-A20 records");
});

test("README learn paragraph shows a trimmed report and the suggestion", () => {
	const use = read("README.md").split("\n## Use it\n")[1].split("\n## What you get\n")[0];
	const learn = use.slice(use.indexOf("**Learn from your runs.**"));
	assert.match(learn, /```\nmellum learn: \d+ runs in [\s\S]*Suggested for AGENTS\.md:[\s\S]*## Mellum[\s\S]*```/);
});

test("the setup smoke step ends with the check, for Pi", () => {
	const smoke = read("skills/mellum-setup/reference/06-smoke.md");
	assert.ok(smoke.includes("scripts/mellum.mjs check --host"), "names the CLI");
	assert.ok(smoke.includes("/mellum check"), "names the Pi command");
	assert.ok(smoke.indexOf("scripts/mellum.mjs check") > smoke.indexOf("calculator.js` multiplies"), "after the fixture passes");
});

test("recipe has a Records, learn and check section with the seven patterns", () => {
	const recipe = read("docs/recipe.md");
	assert.match(recipe, /^## 4c\. Records, learn and check$/m);
	const section = recipe.split(/^## 4c\. Records, learn and check$/m)[1].split(/^## /m)[0];
	for (const id of ["test-thrash", "bent-project", "false-success", "long-run", "servers", "drift", "announce-stop"]) {
		assert.ok(section.includes(`\`${id}\``), `names the ${id} pattern`);
	}
	assert.ok(section.includes("server"), "names the record's server field");
	assert.ok(section.includes("templates/omlx-model-settings.json"), "says where the expected values come from");
	assert.match(section, /Mellum server settings differ/);
});

test("the oMLX backend guide lists step 3's server values", () => {
	const omlx = read("docs/backends/omlx.md");
	assert.match(omlx, /\| `max_tokens` \| 16384 \|/);
	assert.match(omlx, /\| `forced_ct_kwargs` \| `\["enable_thinking"\]` \|/);
	assert.match(omlx, /force_sampling/, "says force_sampling makes the server's sampling win");
});
