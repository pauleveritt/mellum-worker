import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = new URL("../scripts/screen.sh", import.meta.url).pathname;

// A stand-in `uv` on PATH that records the ladder arguments screen.sh hands it.
function screen(env = {}) {
	const bin = mkdtempSync(join(tmpdir(), "screen-uv-"));
	const log = join(bin, "argv");
	writeFileSync(join(bin, "uv"), `#!/bin/sh\nprintf '%s\\n' "$@" > "${log}"\n`);
	chmodSync(join(bin, "uv"), 0o755);
	const r = spawnSync("bash", [SCRIPT, "6", "Mellum2.1-12B-A2.5B-Thinking", "", "runs/screen-script-test"], {
		env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, ...env },
		encoding: "utf8",
	});
	assert.equal(r.status, 0, r.stderr);
	return readFileSync(log, "utf8").trim().split("\n");
}

function flag(argv, name) {
	const i = argv.indexOf(name);
	return i < 0 ? undefined : argv[i + 1];
}

test("screen.sh: oMLX stays the default provider", () => {
	const argv = screen();
	assert.equal(flag(argv, "--model"), "omlx/Mellum2.1-12B-A2.5B-Thinking");
	assert.equal(flag(argv, "--provider"), "omlx");
	assert.equal(flag(argv, "--base-url"), "http://127.0.0.1:8001/v1");
});

test("screen.sh: MELLUM_PROVIDER and MELLUM_BASE_URL point a standard screen at another server", () => {
	const argv = screen({ MELLUM_PROVIDER: "vllm", MELLUM_BASE_URL: "http://127.0.0.1:8000/v1" });
	assert.equal(flag(argv, "--model"), "vllm/Mellum2.1-12B-A2.5B-Thinking");
	assert.equal(flag(argv, "--provider"), "vllm");
	assert.equal(flag(argv, "--base-url"), "http://127.0.0.1:8000/v1");
	// Everything else in the run standard is unchanged.
	for (const fixed of ["--effort-ramp", "--guards"]) assert.ok(argv.includes(fixed), fixed);
	assert.equal(flag(argv, "--redispatch"), "5");
	assert.equal(flag(argv, "--thinking"), "off");
});
