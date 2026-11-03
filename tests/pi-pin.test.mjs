import assert from "node:assert/strict";
import test from "node:test";
import { spawnSync } from "node:child_process";
import { chmodSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = new URL("../", import.meta.url).pathname;
const SCRIPT = join(ROOT, "scripts/pi-pin.sh");
const read = (name) => readFileSync(join(ROOT, name), "utf8");

/** Source scripts/pi-pin.sh and run `fn` with a fake `pi` first on PATH. */
function call(fn, { pi } = {}) {
	const dir = mkdtempSync(join(tmpdir(), "pi-pin-"));
	if (pi !== undefined) {
		const bin = join(dir, "pi");
		writeFileSync(bin, `#!/bin/sh\necho "${pi}"\n`);
		chmodSync(bin, 0o755);
	}
	return spawnSync("bash", ["-c", `source "${SCRIPT}"; ${fn}`], {
		env: { PATH: `${dir}:/usr/bin:/bin`, HOME: dir },
		encoding: "utf8",
	});
}

test("pi_version reads the version the pi on PATH reports", () => {
	const r = call("pi_version", { pi: "1.1.0" });
	assert.equal(r.status, 0, r.stderr);
	assert.equal(r.stdout.trim(), "1.1.0");
});

test("an unpinned pi warns, naming both versions and the install command", () => {
	const r = call("warn_unpinned_pi", { pi: "1.1.0" });
	assert.equal(r.status, 0, "a different pi must not stop the run");
	assert.match(r.stderr, /1\.1\.0/);
	assert.match(r.stderr, /1\.4\.0/);
	assert.match(r.stderr, /npm install -g .*@earendil-works\/pi-coding-agent@1\.4\.0/);
});

test("the pinned pi is silent", () => {
	const r = call("warn_unpinned_pi", { pi: "1.4.0" });
	assert.equal(r.status, 0, r.stderr);
	assert.equal(r.stderr, "");
});

test("no pi at all is a warning, not a failure", () => {
	const r = call("warn_unpinned_pi");
	assert.equal(r.status, 0, r.stderr);
	assert.match(r.stderr, /1\.4\.0/);
});

test("the pin has one home, and every installer reads it", () => {
	const env = read("scripts/pi-pin.env");
	assert.match(env, /^PI_VERSION=1\.4\.0$/m);
	assert.match(env, /^PI_PACKAGE=@earendil-works\/pi-coding-agent$/m);

	for (const name of ["install.sh", "run.sh"]) {
		assert.match(read(name), /source "\$REPO_DIR\/scripts\/pi-pin\.sh"/, `${name} sources the pin`);
		assert.doesNotMatch(read(name), /^PI_VERSION=/m, `${name} does not set the pin itself`);
		assert.doesNotMatch(read(name), /^PI_PACKAGE=/m, `${name} does not set the package itself`);
	}
	assert.match(read("install.sh"), /\$PI_VERSION/, "install.sh installs the pinned version");
	assert.match(read("run.sh"), /warn_unpinned_pi/, "run.sh warns about a different pi");

	const bat = read("install.bat");
	assert.match(bat, /pi-pin\.env/, "install.bat reads the same pin");
	assert.match(bat, /%PI_PACKAGE%@%PI_VERSION%/, "install.bat installs the pinned version");
	assert.match(bat, /call pi install/, "install.bat installs the harness from the clone");
});
