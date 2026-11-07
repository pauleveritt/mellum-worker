import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const ROOT = resolve(import.meta.dirname, "..");
const PROFILE = resolve(ROOT, "learn/code/profile/models.json");

const rendered = () => {
  const r = spawnSync("uv", ["run", "scripts/backend.py", "profile", "--dry-run"], {
    cwd: ROOT, encoding: "utf8",
  });
  assert.equal(r.status, 0, r.stderr);
  return r.stdout;
};

test("the committed profile is exactly what the generator writes", () => {
  assert.equal(readFileSync(PROFILE, "utf8"), rendered());
});

test("the profile carries the settings and the llama.cpp provider", () => {
  const p = JSON.parse(readFileSync(PROFILE, "utf8")).providers.llamacpp;
  assert.equal(p.baseUrl, "http://127.0.0.1:8001/v1");
  assert.equal(p.apiKey, "not-needed");
  const m = p.models[0];
  assert.equal(m.id, "Mellum2.1-12B-A2.5B-Thinking");
  assert.equal(m.contextWindow, 50000);
  assert.equal(m.maxTokens, 16384);
  assert.deepEqual(
    [m.samplingParams.temperature, m.samplingParams.top_p, m.samplingParams.top_k],
    [1.0, 0.95, 20],
  );
});
