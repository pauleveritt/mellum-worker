/**
 * Pure tool-call parsing for content-tool-call-assist — no Pi/runtime imports, so it is unit
 * testable on its own. It normalises whatever shape a small open model emits in its message
 * content into ONE structured, named-args call the agent loop can run:
 *
 *   - a fenced/loose JSON object: {"tool"|"name", "args"|"arguments": { ... }}
 *   - a JSON object whose args are a POSITIONAL LIST (a tiny model's common mistake:
 *     {"tool":"write","args":["a.py","hi"]}) — mapped onto the tool's declared parameter order
 *   - Hermes/Qwen XML: <tool_call><function=name><parameter=k>v</parameter></function></tool_call>
 *
 * `tools` maps each real tool name to its ORDERED parameter names (declaration order), which is
 * what lets a positional list become named arguments and what guards against promoting data or an
 * unknown tool as a call.
 */

export interface ParsedToolCall {
	name: string;
	arguments: Record<string, unknown>;
}

/** name -> ordered parameter names, as declared in the tool's schema. */
export type ToolParams = Map<string, string[]>;

/** Drop <think>...</think> reasoning so a call restated inside it is not mistaken for the action. */
export function stripThinking(text: string): string {
	let rest = text.replace(/<think>[\s\S]*?<\/think>/gi, "");
	if (/<\/think>/i.test(rest)) rest = rest.slice(rest.toLowerCase().lastIndexOf("</think>") + "</think>".length);
	return rest.replace(/<\/?think>/gi, "").trim();
}

/**
 * Yield every top-level balanced {...} object in the text, string- and escape-aware. A depth
 * counter beats a regex: a non-greedy regex stops at the first inner "}" and a greedy one swallows
 * trailing prose, so nested argument objects break both.
 */
export function* iterJsonObjects(text: string): Generator<string> {
	let depth = 0;
	let start = -1;
	let inStr = false;
	let esc = false;
	for (let i = 0; i < text.length; i++) {
		const ch = text[i];
		if (inStr) {
			if (esc) esc = false;
			else if (ch === "\\") esc = true;
			else if (ch === '"') inStr = false;
			continue;
		}
		if (ch === '"') inStr = true;
		else if (ch === "{") {
			if (depth === 0) start = i;
			depth += 1;
		} else if (ch === "}" && depth > 0) {
			depth -= 1;
			if (depth === 0) yield text.slice(start, i + 1);
		}
	}
}

/** Map a positional list onto a tool's parameter names; undefined if it cannot map cleanly. */
function listToNamedArgs(list: unknown[], paramNames: string[] | undefined): Record<string, unknown> | undefined {
	// Need the parameter names, and never more values than parameters (guessing past the schema is
	// how a wrong call slips through). An empty list with no params is a valid no-arg call.
	if (!paramNames || list.length > paramNames.length) return undefined;
	const args: Record<string, unknown> = {};
	for (let i = 0; i < list.length; i++) args[paramNames[i]] = list[i];
	return args;
}

/**
 * Coerce a parsed object into a tool call, accepting both naming conventions and a positional list.
 * Guards keep model DATA from being mistaken for a call: the object must carry an `arguments`/`args`
 * key (a bare {"name":"..."} is data, e.g. a cart item), and when `tools` is given the name must be
 * one of them. A list of args is mapped onto the named tool's parameter order; a bare scalar, or a
 * list we cannot map, is rejected so the loop re-prompts rather than sending oMLX an invalid call.
 */
export function coerceToolCall(obj: unknown, tools?: ToolParams): ParsedToolCall | undefined {
	if (!obj || typeof obj !== "object" || Array.isArray(obj)) return undefined;
	const o = obj as Record<string, unknown>;
	const hasArgsKey = "arguments" in o || "args" in o;
	if (!hasArgsKey) return undefined;
	const name = typeof o.name === "string" ? o.name : typeof o.tool === "string" ? o.tool : undefined;
	if (!name) return undefined;
	if (tools && !tools.has(name)) return undefined;
	let args: unknown = o.arguments ?? o.args ?? {};
	if (typeof args === "string") {
		try {
			args = JSON.parse(args);
		} catch {
			return undefined; // a bare string is not valid arguments
		}
	}
	if (Array.isArray(args)) {
		const named = listToNamedArgs(args, tools?.get(name));
		return named ? { name, arguments: named } : undefined;
	}
	if (args !== null && typeof args === "object") return { name, arguments: args as Record<string, unknown> };
	return undefined;
}

/** Parse a single XML-ish parameter value: JSON if it parses, else the raw string. */
function coerceScalar(raw: string): unknown {
	const trimmed = raw.trim();
	try {
		return JSON.parse(trimmed);
	} catch {
		return trimmed;
	}
}

/**
 * Convert the Hermes/Qwen XML tool-call form into a structured, named-args call. Many small models'
 * chat templates define tool calls as XML, not JSON:
 *
 *   <tool_call><function=write>
 *     <parameter=path>hello.txt</parameter>
 *     <parameter=content>hi there</parameter>
 *   </function></tool_call>
 *
 * The outer <tool_call> wrapper is optional; a bare <function=...> block is accepted.
 */
export function parseXmlToolCall(text: string, tools?: ToolParams): ParsedToolCall | undefined {
	const fn = text.match(/<function=([^>\s]+)\s*>([\s\S]*?)<\/function>/);
	if (!fn?.[1]) return undefined;
	const name = fn[1];
	if (tools && !tools.has(name)) return undefined;
	const args: Record<string, unknown> = {};
	const paramRe = /<parameter=([^>\s]+)\s*>([\s\S]*?)<\/parameter>/g;
	let m: RegExpExecArray | null = paramRe.exec(fn[2]);
	while (m !== null) {
		if (m[1]) args[m[1]] = coerceScalar(m[2]);
		m = paramRe.exec(fn[2]);
	}
	return { name, arguments: args };
}

/** Pull a tool-call out of model text in any shape (JSON object, positional-list JSON, or XML). */
export function parseContentToolCall(text: string, tools?: ToolParams): ParsedToolCall | undefined {
	for (const region of [stripThinking(text), text]) {
		for (const chunk of iterJsonObjects(region)) {
			try {
				const call = coerceToolCall(JSON.parse(chunk), tools);
				if (call) return call;
			} catch {
				// not valid JSON; keep scanning
			}
		}
		const xml = parseXmlToolCall(region, tools);
		if (xml) return xml;
	}
	return undefined;
}
