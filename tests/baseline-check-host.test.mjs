import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = new URL("../scripts/baseline/check-host.sh", import.meta.url).pathname;

// A stand-in nvidia-smi on PATH that reports the given GPU rows.
function checkHost(rows) {
	const bin = mkdtempSync(join(tmpdir(), "check-host-"));
	writeFileSync(join(bin, "nvidia-smi"), `#!/bin/sh\nprintf '${rows.map((r) => `${r}\\n`).join("")}'\n`);
	chmodSync(join(bin, "nvidia-smi"), 0o755);
	return spawnSync("bash", [SCRIPT], {
		env: { ...process.env, PATH: `${bin}:${process.env.PATH}` },
		encoding: "utf8",
	});
}

const A6000 = "NVIDIA RTX A6000, 49140, 595.104.02";

test("check-host: the pinned GPU passes", () => {
	const r = checkHost([A6000]);
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stdout, /check-host: OK/);
});

test("check-host: another GPU is refused", () => {
	const r = checkHost(["NVIDIA GeForce RTX 5090, 32607, 570.86.15"]);
	assert.equal(r.status, 1);
	assert.match(r.stderr, /MISMATCH/);
});

test("check-host: the pinned GPU with a different memory size is refused", () => {
	const r = checkHost(["NVIDIA RTX A6000, 46068, 595.104.02"]);
	assert.equal(r.status, 1);
});

test("check-host: a driver too old for the image's CUDA is refused", () => {
	const r = checkHost(["NVIDIA RTX A6000, 49140, 550.163.01"]);
	assert.equal(r.status, 1);
	assert.match(r.stderr, /driver 550\.163\.01 is older than 580/);
});

test("check-host: two of the pinned GPU is not the pinned count", () => {
	const r = checkHost([A6000, A6000]);
	assert.equal(r.status, 1);
});
