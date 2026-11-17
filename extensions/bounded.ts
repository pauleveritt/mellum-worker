/** Run a settle check's command under a timeout that ends its whole process group.
 *
 * `spawnSync`'s own `timeout` signals only the direct child, so a check whose command starts a
 * server (an import that runs the app, a test that launches one) keeps the pipe open and hangs
 * settle. Here a short node child spawns the command in a group of its own and, at the timeout,
 * kills the group. The call stays synchronous, so callers keep their shape. Built-ins only. */
import { spawnSync } from "node:child_process";

export interface Bounded {
	/** The exit code, or null when the command was killed or never started. */
	code: number | null;
	/** stdout and stderr, interleaved as they arrived. */
	out: string;
	timedOut: boolean;
	/** False when the command could not start (a missing binary): our tooling, never a red gate. */
	started: boolean;
}

// The command's own exit decides the result: a child it left behind (a server holding the pipe,
// or one with its output redirected) does not turn a finished run into a timeout, and is killed
// with the group whichever way the command ended. A short grace after exit collects trailing output.
const RUNNER = `
const { spawn } = require("node:child_process");
const o = JSON.parse(process.argv[1]);
let out = "", timedOut = false, done = false, exitCode = null, grace = null;
const c = spawn(o.cmd, o.args, { detached: true, stdio: ["ignore", "pipe", "pipe"] });
const killGroup = () => { try { process.kill(-c.pid, "SIGKILL"); } catch {} };
const finish = (r) => { if (done) return; done = true; clearTimeout(t); clearTimeout(grace); process.stdout.write(JSON.stringify(r)); };
const end = (code) => { killGroup(); finish({ code: timedOut ? null : (exitCode ?? code), out, timedOut, started: true }); };
c.stdout.on("data", (d) => { out += d; });
c.stderr.on("data", (d) => { out += d; });
const t = setTimeout(() => { timedOut = true; killGroup(); }, o.timeoutMs);
c.on("error", () => finish({ code: null, out: "", timedOut: false, started: false }));
c.on("exit", (code) => { exitCode = code; if (!timedOut) grace = setTimeout(() => end(code), 300); });
c.on("close", (code) => end(code));
`;

export function runBounded(
	cmd: string,
	args: string[],
	opts: { cwd: string; env?: NodeJS.ProcessEnv; timeoutMs: number },
): Bounded {
	const r = spawnSync(process.execPath, ["-e", RUNNER, JSON.stringify({ cmd, args, timeoutMs: opts.timeoutMs })], {
		cwd: opts.cwd,
		env: opts.env ?? process.env,
		encoding: "utf8",
		maxBuffer: 16 * 1024 * 1024,
		// A backstop: a process that left the group can still hold the pipe after the kill.
		timeout: opts.timeoutMs + 5000,
	});
	try {
		return JSON.parse(r.stdout) as Bounded;
	} catch {
		return { code: null, out: r.stdout ?? "", timedOut: true, started: true };
	}
}
