import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = new URL("../scripts/llama-release.sh", import.meta.url).pathname;

/** Run `fn args` with scripts/llama-release.sh sourced; `bin` holds fake tools put first on PATH. */
function call(fn, args, { bin = {}, env = {} } = {}) {
	const dir = mkdtempSync(join(tmpdir(), "llama-release-"));
	for (const [name, body] of Object.entries(bin)) {
		const p = join(dir, name);
		writeFileSync(p, `#!/bin/sh\n${body}\n`);
		chmodSync(p, 0o755);
	}
	const script = `source "${SCRIPT}"; ${fn} ${args.map((a) => `'${a}'`).join(" ")}`;
	return execFileSync("bash", ["-c", script], {
		env: { PATH: `${dir}:/usr/bin:/bin`, HOME: dir, ...env },
		encoding: "utf8",
	}).trim();
}

const smi = (v) => `echo "| NVIDIA-SMI 615.78   Driver Version: 615.78   CUDA Version: ${v}     |"`;

test("an NVIDIA driver with CUDA 13 picks the CUDA 13.4 build", () => {
	assert.equal(call("llama_flavor", ["x86_64"], { bin: { "nvidia-smi": smi("13.1") } }), "cuda-13.4");
});

test("a newer driver's 'CUDA UMD Version' banner is read too", () => {
	const umd = `echo "| NVIDIA-SMI 615.78.08   KMD Version: 615.78.08     CUDA UMD Version: 13.4     |"`;
	assert.equal(call("llama_flavor", ["x86_64"], { bin: { "nvidia-smi": umd } }), "cuda-13.4");
});

test("an NVIDIA driver with CUDA 12 picks the CUDA 12.8 build on x86_64", () => {
	assert.equal(call("llama_flavor", ["x86_64"], { bin: { "nvidia-smi": smi("12.4") } }), "cuda-12.8");
});

test("MELLUM_LLAMA_FLAVOR overrides detection", () => {
	assert.equal(call("llama_flavor", ["x86_64"], { bin: { "nvidia-smi": smi("13.1") }, env: { MELLUM_LLAMA_FLAVOR: "cpu" } }), "cpu");
});

test("CUDA flavors bring the matching runtime archive", () => {
	assert.deepEqual(call("llama_assets", ["b12066", "cuda-13.4", "x86_64"]).split("\n"), [
		"llama-b12066-bin-ubuntu-cuda-13.4-x64.tar.gz",
		"cudart-llama-b12066-bin-ubuntu-cuda-13.4-x64.tar.gz",
	]);
});

test("vulkan and cpu are one archive each, arm64 named arm64", () => {
	assert.equal(call("llama_assets", ["b12066", "vulkan", "aarch64"]), "llama-b12066-bin-ubuntu-vulkan-arm64.tar.gz");
	assert.equal(call("llama_assets", ["b12066", "cpu", "x86_64"]), "llama-b12066-bin-ubuntu-x64.tar.gz");
});

test("no prebuilt for an unknown arch or CUDA 12.8 on arm64", () => {
	assert.equal(call("llama_assets", ["b12066", "cpu", "riscv64"]), "");
	assert.equal(call("llama_assets", ["b12066", "cuda-12.8", "aarch64"]), "");
});
