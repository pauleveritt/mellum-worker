/** Find and stop what this session's own commands left running.
 *
 * Pi's bash tool copies process.env for every command, and a command's children inherit it, so a
 * variable set here marks exactly the processes this session starts from now on. Nothing is
 * classified by name, port or directory, so a server the developer started themselves is left alone.
 * `ps` reads the mark from each process's environment; macOS hides that for its own system binaries
 * (/bin/sleep), not for an interpreter such as a project's Python.
 * Used before a settle re-run: a server the model left in the background must not decide the test. */
import { spawnSync } from "node:child_process";

const MARK = "MELLUM_SESSION_PROCESS";
const GRACE_MS = 2000;

function sleep(ms: number): void {
	Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

/** Mark every command this session starts from now on. */
export function markSessionProcesses(): void {
	process.env[MARK] = `${process.pid}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function marked(): number[] {
	const mark = process.env[MARK];
	if (!mark) return [];
	const env = { ...process.env };
	delete env[MARK]; // so `ps` does not list itself
	const r = spawnSync("ps", ["axeww", "-o", "pid=,command="], { env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
	if (r.status !== 0 || typeof r.stdout !== "string") return [];
	return r.stdout
		.split("\n")
		.filter((line) => line.includes(`${MARK}=${mark}`))
		.map((line) => Number.parseInt(line.trim(), 10))
		.filter((pid) => Number.isInteger(pid) && pid !== process.pid);
}

function signal(pids: number[], name: NodeJS.Signals): void {
	for (const pid of pids) {
		try {
			process.kill(pid, name);
		} catch {
			// already gone
		}
	}
}

/** Stop this session's leftover processes and return how many there were. Never throws: a failure
 * here must not block the settle it runs before. */
export function stopSessionProcesses(): number {
	try {
		const found = marked();
		if (found.length === 0) return 0;
		signal(found, "SIGTERM");
		const end = Date.now() + GRACE_MS;
		while (Date.now() < end && marked().length > 0) sleep(50);
		signal(marked(), "SIGKILL");
		return found.length;
	} catch {
		return 0;
	}
}
