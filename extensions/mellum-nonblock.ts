/**
 * mellum-nonblock: make a long-running bash command THREAD instead of hang.
 *
 * The recorded pathology: the generated app ends with `uvicorn.run(...)`, so a
 * worker that "checks its work" with `uv run python app.py` (or uvicorn, flask
 * run, http.server, npm run dev …) launches a server that never returns. The
 * whole workflow then blocks until the orchestrator's wf-timeout — ~400s burned.
 *
 * A long-running script is fine as long as it THREADS and its output is fed back
 * to the model. So this does not forbid the command — it rewrites it to run in
 * the background (threaded), capture its output, wait a moment, and print what it
 * produced. The call returns at once with the startup output; the process keeps
 * running in the background. Pi exposes `event.input` as mutable for exactly this
 * (extensions/types.ts: "Mutate it in place to patch tool arguments"), so the
 * rewrite is agnostic to the task — it keys off the launcher, not any one app.
 *
 * The orchestrator reaps the workflow's process group when the stage ends, so a
 * backgrounded server does not leak across workflows.
 */

/** Server launchers and blocking dev-server signatures, matched on the command text. */
const SERVER_PATTERNS: { re: RegExp; what: string }[] = [
	{ re: /\buvicorn\b/, what: "uvicorn" },
	{ re: /\bgunicorn\b/, what: "gunicorn" },
	{ re: /\bhypercorn\b/, what: "hypercorn" },
	{ re: /\bdaphne\b/, what: "daphne" },
	{ re: /\bwaitress-serve\b/, what: "waitress" },
	{ re: /\bflask\s+run\b/, what: "flask run" },
	{ re: /\brunserver\b/, what: "manage.py runserver" },
	{ re: /\brails\s+s(erver)?\b/, what: "rails server" },
	{ re: /\bphp\s+-S\b/, what: "php -S" },
	{ re: /\bhttp\.server\b/, what: "python -m http.server" },
	{ re: /--reload\b/, what: "a --reload server" },
	{ re: /\.run\s*\(\s*(?:[^)]*\b(?:host|port)\s*=|["']?0\.0\.0\.0)/, what: "an inline .run(host/port=…) server call" },
	{ re: /\b(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:dev|start|serve)\b/, what: "a dev server" },
	{ re: /\b(?:vite|nodemon|serve)\b/, what: "a dev server" },
	{ re: /\bnext\s+dev\b/, what: "a dev server" },
	{ re: /\bpython[0-9.]*\s+(?:-\w+\s+)*(?:\S*\/)?(?:app|main|server|run|wsgi|asgi|manage)\.py\b/, what: "a server entrypoint (app.py/main.py/…)" },
];

const SENTINEL = "mellum-nonblock";

/** The launcher a command would start (and block on), or undefined for a short command. */
export function blockingLauncher(command: string): string | undefined {
	if (command.includes(SENTINEL)) return undefined; // already threaded
	for (const { re, what } of SERVER_PATTERNS) {
		if (re.test(command)) return what;
	}
	return undefined;
}

/** Rewrite a blocking command to run in the background and print the output it produced. */
export function wrap(command: string): string {
	// Background the original in a subshell, capture output, wait briefly, print it, return.
	return (
		`__nb=$(mktemp "\${TMPDIR:-/tmp}/${SENTINEL}.XXXXXX"); ` +
		`( ${command} ) >"$__nb" 2>&1 & __nbpid=$!; ` +
		`sleep 4; ` +
		`echo "[${SENTINEL}] backgrounded pid $__nbpid (threaded, still running); output so far:"; ` +
		`cat "$__nb"; ` +
		`echo "[${SENTINEL}] still running in the background (log $__nb). Do NOT wait on it — ` +
		`verify behaviour in process with starlette/fastapi TestClient under pytest."`
	);
}

function commandOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const value = (input as Record<string, unknown>).command;
	return typeof value === "string" ? value : undefined;
}

/** On a blocking bash/shell call, rewrite input.command in place to a threaded one. */
export function applyNonblock(toolName: string, input: unknown): string | undefined {
	if (toolName !== "bash" && toolName !== "shell") return undefined;
	const command = commandOf(input);
	if (!command) return undefined;
	const launcher = blockingLauncher(command);
	if (!launcher) return undefined;
	(input as Record<string, unknown>).command = wrap(command);
	return launcher;
}

export default function (pi: { on: (event: string, handler: (event: any) => unknown) => void }): void {
	pi.on("tool_call", (event) => {
		applyNonblock(event?.toolName, event?.input); // thread a server so it returns at once
		return undefined; // never block — the command still runs, just threaded
	});
}
