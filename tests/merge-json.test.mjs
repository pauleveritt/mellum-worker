import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { mergeJson } from "../scripts/merge-json.mjs";

const script = join(dirname(fileURLToPath(import.meta.url)), "..", "scripts", "merge-json.mjs");
const fragment = { providers: { llamacpp: { baseUrl: "http://127.0.0.1:8001/v1", models: [{ id: "mellum", maxTokens: 16384 }] } } };

function runCli(args) {
	try {
		return { status: 0, stdout: execFileSync("node", [script, ...args], { encoding: "utf8", stdio: "pipe" }), stderr: "" };
	} catch (err) {
		return { status: err.status, stdout: err.stdout, stderr: err.stderr };
	}
}

function tempDir() {
	return mkdtempSync(join(tmpdir(), "merge-json-"));
}

test("adds the provider when the target has none", () => {
	const out = mergeJson({ providers: { other: { baseUrl: "x" } } }, fragment);
	assert.deepEqual(Object.keys(out.providers).sort(), ["llamacpp", "other"]);
	assert.deepEqual(out.providers.llamacpp.models, [{ id: "mellum", maxTokens: 16384 }]);
});

test("keeps the user's other models in an existing llamacpp provider and appends by id", () => {
	const target = { providers: { llamacpp: { baseUrl: "http://127.0.0.1:8001/v1", models: [{ id: "gemma", maxTokens: 8192 }] } } };
	const out = mergeJson(target, fragment);
	assert.deepEqual(out.providers.llamacpp.models.map((m) => m.id), ["gemma", "mellum"]);
	assert.deepEqual(target.providers.llamacpp.models.map((m) => m.id), ["gemma"], "input not mutated");
});

test("is idempotent and refreshes an existing entry with the same id", () => {
	const once = mergeJson({}, fragment);
	const twice = mergeJson(once, fragment);
	assert.deepEqual(twice, once);
	const updated = mergeJson(once, { providers: { llamacpp: { models: [{ id: "mellum", maxTokens: 4096 }] } } });
	assert.equal(updated.providers.llamacpp.models.length, 1);
	assert.equal(updated.providers.llamacpp.models[0].maxTokens, 4096);
});

test("scalar arrays are replaced, not concatenated", () => {
	assert.deepEqual(mergeJson({ a: [1, 2] }, { a: [3] }), { a: [3] });
});

test("mixed-shape object arrays keep every user entry and append the fragment entry", () => {
	const target = { models: [{ id: "gemma" }, { name: "no-id-entry" }] };
	const frag = { models: [{ id: "mellum" }] };
	const once = mergeJson(target, frag);
	assert.deepEqual(once.models, [{ id: "gemma" }, { name: "no-id-entry" }, { id: "mellum" }]);
	const twice = mergeJson(once, frag);
	assert.deepEqual(twice, once, "running twice adds nothing");
	assert.deepEqual(target.models, [{ id: "gemma" }, { name: "no-id-entry" }], "input not mutated");
});

test("CLI fails clearly on a target that is not valid JSON", () => {
	const dir = tempDir();
	const bad = join(dir, "models.json");
	writeFileSync(bad, '{ "providers": { // comment\n }');
	const frag = join(dir, "frag.json");
	writeFileSync(frag, JSON.stringify(fragment));
	const result = runCli([bad, frag]);
	assert.equal(result.status, 1);
	assert.match(result.stderr, /target .*models\.json is not valid JSON/);
	assert.match(result.stderr, /JSONC comments are not supported/);
});

test("CLI fails clearly when the target root is not a JSON object", () => {
	const dir = tempDir();
	const arr = join(dir, "models.json");
	writeFileSync(arr, "[1, 2]");
	const frag = join(dir, "frag.json");
	writeFileSync(frag, JSON.stringify(fragment));
	const result = runCli([arr, frag]);
	assert.equal(result.status, 1);
	assert.match(result.stderr, /target .*models\.json must contain a JSON object at the root/);
});

test("CLI preview writes nothing; --write creates a missing target and backs up an existing one", () => {
	const dir = tempDir();
	const frag = join(dir, "frag.json");
	writeFileSync(frag, JSON.stringify(fragment));

	const missing = join(dir, "nested", "models.json");
	const created = runCli([missing, frag, "--write"]);
	assert.equal(created.status, 0);
	assert.ok(existsSync(missing), "--write creates the file and its directory");
	assert.deepEqual(JSON.parse(readFileSync(missing, "utf8")), fragment);

	const existing = join(dir, "existing.json");
	writeFileSync(existing, JSON.stringify({ providers: { other: {} } }));
	const before = readFileSync(existing, "utf8");
	const preview = runCli([existing, frag]);
	assert.equal(preview.status, 0);
	assert.match(preview.stdout, /preview only/);
	assert.equal(readFileSync(existing, "utf8"), before, "preview leaves the target unchanged");
	assert.equal(readdirSync(dir).filter((f) => f.startsWith("existing.json.bak-mellum-")).length, 0);

	const applied = runCli([existing, frag, "--write"]);
	assert.equal(applied.status, 0);
	const backups = readdirSync(dir).filter((f) => f.startsWith("existing.json.bak-mellum-"));
	assert.equal(backups.length, 1, "--write leaves one .bak-mellum- sibling");
	assert.equal(readFileSync(join(dir, backups[0]), "utf8"), before);
	assert.deepEqual(JSON.parse(readFileSync(existing, "utf8")).providers.llamacpp.models, fragment.providers.llamacpp.models);
});

test("a models-only fragment keeps an existing llamacpp baseUrl and apiKey", () => {
	// A fragment carrying only `models` (no baseUrl/apiKey) must leave the
	// user's connection fields untouched and append the model by id.
	const only = { providers: { llamacpp: { models: [{ id: "Mellum2.1-12B-A2.5B-Thinking", maxTokens: 16384 }] } } };
	const target = { providers: { llamacpp: { baseUrl: "http://127.0.0.1:9001/v1", apiKey: "sk-secret", api: "openai-completions", models: [{ id: "gemma" }] } } };
	const out = mergeJson(target, only);
	assert.equal(out.providers.llamacpp.baseUrl, "http://127.0.0.1:9001/v1");
	assert.equal(out.providers.llamacpp.apiKey, "sk-secret");
	assert.deepEqual(out.providers.llamacpp.models.map((x) => x.id), ["gemma", "Mellum2.1-12B-A2.5B-Thinking"]);
});

test("preview prints only the merged fragment subtree, not other providers' secrets", () => {
	const dir = tempDir();
	const target = join(dir, "models.json");
	writeFileSync(target, JSON.stringify({ providers: { other: { apiKey: "sk-other" } } }));
	const frag = join(dirname(script), "..", "templates", "pi", "models.llamacpp.json");
	const r = runCli([target, frag]);
	assert.equal(r.status, 0);
	assert.ok(!r.stdout.includes("sk-other"));
	assert.ok(r.stdout.includes("providers.llamacpp (after merge):"));
	assert.ok(r.stdout.includes("preview only"));
});
