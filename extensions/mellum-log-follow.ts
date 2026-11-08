/** The foreground log-follow guard: refuse `tail -f` (and its spellings) run in the foreground,
 * which waits forever on a log and burns the session to the stall cutoff.
 *
 * Ported from `lc40-thin-worker` (c9ee0b04, 81f659ce), with lc40's shell-word scanner, kept in its
 * own module so the regex server guard in mellum-guards.ts (Andre's f0e31ea) stays as it is. A
 * hang-prevention heuristic, not a complete shell parser or a security boundary. */
import type { Guard } from "./mellum-guards.ts";

function commandOf(input: unknown): string | undefined {
	if (!input || typeof input !== "object") return undefined;
	const record = input as Record<string, unknown>;
	for (const key of ["command", "cmd"]) {
		if (typeof record[key] === "string") return record[key] as string;
	}
	return undefined;
}

interface ShellCommand {
	words: string[];
	background: boolean;
}

/** A small shell-word scanner: quoted descriptions are data, separators split
 * commands, and redirection ampersands do not detach a command. */
function shellCommands(command: string, omitRedirections = false): ShellCommand[] {
	const commands: ShellCommand[] = [];
	let words: string[] = [], word = "", quote = "";
	let redirectionTarget = false, wordQuoted = false;
	let pipelineStart = 0;
	const groups: number[] = [];
	const finishWord = () => {
		if (word || wordQuoted) {
			if (word && !redirectionTarget) words.push(word);
			word = ""; wordQuoted = false; redirectionTarget = false;
		}
	};
	const finish = (background = false) => {
		finishWord();
		if (words.length) commands.push({ words, background });
		words = []; redirectionTarget = false;
	};
	for (let i = 0; i < command.length; i++) {
		const c = command[i];
		if (c === "\\" && quote !== "'" && i + 1 < command.length) {
			if (command[++i] !== "\n") { word += command[i]; wordQuoted = true; }
		} else if (quote) {
			if (c === quote) quote = "";
			else word += c;
		} else if (c === "'" || c === '"') {
			quote = c; wordQuoted = true;
		} else if (c === "#" && !word) {
			while (i + 1 < command.length && command[i + 1] !== "\n") i++;
		} else if (omitRedirections && (c === ">" || c === "<" || (c === "&" && command[i + 1] === ">"))) {
			// A descriptor/operator/target belongs to the shell, not tail's argv.
			// Quoted numeric words remain arguments, even immediately before >.
			if (/^\d+$/.test(word) && !wordQuoted) { word = ""; wordQuoted = false; }
			else finishWord();
			if (c === "&") i++;
			if (command[i + 1] === command[i]) i++;
			if (["&", "|"].includes(command[i + 1])) i++;
			redirectionTarget = true;
		} else if (c === "&" && (command[i - 1] === ">" || command[i + 1] === ">")) {
			word += c;
		} else if (";\n|&()".includes(c)) {
			const doubled = (c === "&" || c === "|") && command[i + 1] === c;
			finish();
			if (c === "(") groups.push(pipelineStart);
			else if (c === ")") pipelineStart = groups.pop() ?? pipelineStart;
			else if (c === "&" && !doubled) {
				for (let j = pipelineStart; j < commands.length; j++) commands[j].background = true;
				pipelineStart = commands.length;
			} else if (c !== "|" || doubled) pipelineStart = commands.length;
			if (doubled) i++;
		} else if (/\s/.test(c)) {
			finishWord();
		} else word += c;
	}
	finish();
	return commands;
}

const QUERY_FLAGS = new Set(["--help", "--version", "-h", "-V"]);
const basename = (word = "") => word.split("/").at(-1) ?? "";

/** The command's words after common launch wrappers (env, exec, uv run, timeout). */
function unwrappedWords(words: string[]): string[] | undefined {
	words = [...words];
	while (words.length) {
		if (/^[A-Za-z_][A-Za-z_0-9]*=/.test(words[0]) || ["env", "exec", "command"].includes(basename(words[0]))) {
			words.shift();
		} else if (basename(words[0]) === "uv" && words[1] === "run") {
			words.splice(0, 2);
			while (words[0]?.startsWith("-")) {
				const option = words.shift();
				if (["--directory", "--project", "--python", "--with"].includes(option ?? "")) words.shift();
			}
		} else if (["timeout", "gtimeout"].includes(basename(words[0]))) {
			words.shift();
			while (words[0]?.startsWith("-") && words[0] !== "--") {
				const option = words.shift();
				if (["--signal", "--kill-after"].includes(option ?? "")) words.shift();
				else if (option && !option.startsWith("--")) {
					// In a short-option cluster, s/k consumes the rest of the
					// same word, or the next word when its operand is separate.
					const operand = option.slice(1).search(/[sk]/);
					if (operand >= 0 && operand === option.length - 2) words.shift();
				}
			}
			if (words[0] === "--") words.shift();
			if (!/^(?:(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?[smhd]?|inf(?:inity)?)$/i.test(words.shift() ?? "")) return undefined;
		} else break;
	}
	return words;
}

/** Foreground tail-follow is a wait, even when a different command detached. */
function followsLog(input: string[]): boolean {
	let words = unwrappedWords(input);
	while (words && basename(words[0]) === "nohup") words = unwrappedWords(words.slice(1));
	if (!words || basename(words.shift()) !== "tail") return false;
	let follow = false;
	for (let i = 0; i < words.length; i++) {
		const word = words[i];
		if (word === "--") break;
		if (QUERY_FLAGS.has(word)) return false;
		if (["--lines", "--bytes"].includes(word)) { i++; continue; }
		if (word === "--follow" || word.startsWith("--follow=")) follow = true;
		else if (word.startsWith("-") && !word.startsWith("--")) {
			const options = word.slice(1);
			for (let j = 0; j < options.length; j++) {
				if ("fF".includes(options[j])) follow = true;
				if ("nc".includes(options[j])) {
					if (j === options.length - 1) i++;
					break;
				}
			}
		}
	}
	return follow;
}

export const logFollowGuard: Guard = (call) => {
	if (call.toolName !== "bash") return undefined;
	const command = commandOf(call.input);
	if (!command || !shellCommands(command, true).some(({ words, background }) => !background && followsLog(words))) return undefined;
	return {
		block: true,
		reason:
			"Blocked before execution: this foreground log-follow command was not run. This message is not application output. " +
			"Use a finite log snapshot such as tail -n 50, not follow mode. " +
			"Verify required startup with bounded readiness/log checks and clean up owned processes; backgrounding a server does not bound later commands.",
	};
};
