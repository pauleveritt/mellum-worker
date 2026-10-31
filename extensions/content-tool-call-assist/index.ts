/**
 * content-tool-call-assist
 *
 * Problem: small open models often "know" the right tool call but emit it inside
 * their text content -- a fenced ```json {"name","arguments"} block, or a
 * <tool_call>...</tool_call> tag -- instead of the structured tool_calls field.
 * Pi only executes structured tool calls, so such a turn ends with text and no
 * action, and the agent loop stalls.
 *
 * This extension registers a provider that delegates streaming to the built-in
 * openai-completions implementation and, when a turn produced NO structured tool
 * call but its content carries a tool-call-shaped payload, promotes that payload
 * into a real tool call before the turn settles. The model drives the loop as if
 * it had tool-called natively.
 *
 * Load with: pi -e ./packages/coding-agent/examples/extensions/content-tool-call-assist
 */

import {
	type Api,
	type AssistantMessage,
	type AssistantMessageEvent,
	type AssistantMessageEventStream,
	createAssistantMessageEventStream,
	type Model,
	type SimpleStreamOptions,
	type SystemMessage,
	streamSimple,
	type Tool,
	type ToolCall,
	type TranscriptContext,
} from "@earendil-works/pi-ai/compat";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { parseContentToolCall, type ParsedToolCall, type ToolParams } from "./parse";

/** The real upstream wire protocol we delegate to. */
const UPSTREAM_API = "openai-completions" as Api;
/** The synthetic api our registered models declare, so Pi routes them to us. */
const ASSIST_API = "content-tool-call-assist" as Api;

// The pure tool-call parsing (JSON object, positional-list, Hermes XML) lives in ./parse so it can
// be unit tested without Pi's runtime imports. index.ts supplies it the tool parameter order.

/** Tools available at the end of the transcript, from replayed system messages. */
function collectTools(context: TranscriptContext): Tool[] {
	const byName = new Map<string, Tool>();
	for (const message of context.messages) {
		if (message.role !== "system") continue;
		for (const tool of message.toolsAdded ?? []) byName.set(tool.name, tool);
		for (const ref of message.toolsRemoved ?? []) byName.delete(ref.name);
	}
	return [...byName.values()];
}

/**
 * Build the name -> ordered parameter-name map `parse` needs to turn a positional-list call into
 * named arguments and to reject an unknown tool. Parameter order is the tool schema's property
 * declaration order (JSON preserves key order). Tool schemas vary by host, so read the common
 * shapes defensively; a tool with no discoverable schema maps to an empty list (object-args and
 * XML calls still work — only positional-list mapping needs the names).
 */
function toolParams(tools: Tool[]): ToolParams {
	const map: ToolParams = new Map();
	for (const t of tools) {
		const holder = t as { parameters?: unknown; inputSchema?: unknown; schema?: unknown };
		const s = (holder.parameters ?? holder.inputSchema ?? holder.schema) as { properties?: unknown } | undefined;
		const props = s && typeof s === "object" ? s.properties : undefined;
		map.set(t.name, props && typeof props === "object" ? Object.keys(props as object) : []);
	}
	return map;
}

/**
 * A late system message that tells a small model to ACT via a tool call instead
 * of explaining in prose. The think cap, the worked JSON shape, and the real
 * tool names pull it back to emitting a single fenced call, which
 * parseContentToolCall then promotes. Names only: each tool's full schema
 * already rides in the request's (native) tool field, which the host needs
 * anyway to render tool-result turns and to execute the call -- so this lists
 * names, not a second copy of the schema. On a retry (attempt > 0) the wording
 * hardens, because the previous attempt produced no call.
 */
function buildForceNudge(context: TranscriptContext, attempt: number): SystemMessage {
	const names = collectTools(context).map((tool) => tool.name);
	const toolLine = names.length
		? `Tools (parameters are in the tool definitions): ${names.join(", ")}`
		: "Use the tools defined above.";
	const lines = [
		"You are a careful agent and you work in single steps.",
		"Think in AT MOST two short sentences, then emit EXACTLY ONE tool call and stop.",
		"Do not explain, summarize, or write code in prose. Act only by calling a tool.",
		"",
		"End your reply with ONE fenced JSON block naming one tool:",
		"```json",
		'{"tool": "<name>", "args": { ... }}',
		"```",
		"",
		toolLine,
		"One tool per reply. Make the change by calling a tool; do not describe it.",
	];
	if (attempt > 0) {
		lines.push(
			"",
			"Your previous reply contained NO tool call. Reply now with ONLY the fenced JSON tool call, nothing before or after it.",
		);
	}
	return { role: "system", content: lines.join("\n"), timestamp: Date.now() };
}

let counter = 0;
function syntheticId(): string {
	counter += 1;
	return `assist_${Date.now().toString(36)}_${counter}`;
}

type DoneEvent = Extract<AssistantMessageEvent, { type: "done" }>;

function envFlag(name: string): boolean {
	const v = process.env[name];
	return v === "1" || v === "true";
}
function envNum(name: string, fallback: number): number {
	const v = Number(process.env[name]);
	return Number.isFinite(v) ? v : fallback;
}

/** Append the promoted tool call to a settled turn and emit it as a toolUse turn. */
function emitPromoted(outer: AssistantMessageEventStream, done: DoneEvent, parsed: ParsedToolCall): void {
	const toolCall: ToolCall = {
		type: "toolCall",
		id: syntheticId(),
		name: parsed.name,
		arguments: parsed.arguments as ToolCall["arguments"],
	};
	const message: AssistantMessage = {
		...done.message,
		content: [...done.message.content, toolCall],
		stopReason: "toolUse",
	};
	const index = message.content.length - 1;
	outer.push({ type: "toolcall_start", contentIndex: index, partial: message });
	outer.push({
		type: "toolcall_delta",
		contentIndex: index,
		delta: JSON.stringify(parsed.arguments),
		partial: message,
	});
	outer.push({ type: "toolcall_end", contentIndex: index, toolCall, partial: message });
	outer.push({ type: "done", reason: "toolUse", message });
	outer.end(message);
}

/** Live single pass: stream events through and promote a content tool call at `done`. */
function streamLive(
	outer: AssistantMessageEventStream,
	upstreamModel: Model<Api>,
	context: TranscriptContext,
	options: SimpleStreamOptions | undefined,
): void {
	const tools = toolParams(collectTools(context));
	void (async () => {
		let sawToolCall = false;
		let text = "";
		try {
			for await (const event of streamSimple(upstreamModel, context, options)) {
				if (event.type === "toolcall_start") sawToolCall = true;
				else if (event.type === "text_delta") text += event.delta;

				if (event.type === "done") {
					const parsed = sawToolCall ? undefined : parseContentToolCall(text, tools);
					if (!parsed) {
						outer.push(event);
						outer.end(event.message);
						return;
					}
					emitPromoted(outer, event, parsed);
					return;
				}
				if (event.type === "error") {
					outer.push(event);
					outer.end(event.error);
					return;
				}
				outer.push(event);
			}
		} catch (error) {
			throw error instanceof Error ? error : new Error(String(error));
		}
	})();
}

interface AttemptResult {
	captured: AssistantMessageEvent[];
	done?: DoneEvent;
	parsed?: ParsedToolCall;
	/** True when the turn acted: a native tool call or a promotable content call. */
	acted: boolean;
}

/** One buffered attempt: collect every event, then report whether the turn acted. */
async function runAttempt(
	upstreamModel: Model<Api>,
	context: TranscriptContext,
	options: SimpleStreamOptions,
	tools: ToolParams,
): Promise<AttemptResult> {
	const captured: AssistantMessageEvent[] = [];
	let sawToolCall = false;
	let text = "";
	for await (const event of streamSimple(upstreamModel, context, options)) {
		if (event.type === "toolcall_start") sawToolCall = true;
		else if (event.type === "text_delta") text += event.delta;
		captured.push(event);
		if (event.type === "done" || event.type === "error") break;
	}
	const last = captured[captured.length - 1];
	const done = last?.type === "done" ? last : undefined;
	const parsed = done && !sawToolCall ? parseContentToolCall(text, tools) : undefined;
	return { captured, done, parsed, acted: Boolean(done) && (sawToolCall || parsed !== undefined) };
}

/**
 * Buffered retry path (ASSIST_FORCE_TOOLS=1). Each attempt gets the force nudge
 * and a fresh seed and temperature; a prose-only turn is discarded and retried,
 * because for a tiny model re-rolling a step is cheap. The winning attempt is
 * replayed; its content call, if any, is promoted.
 */
function streamForced(
	outer: AssistantMessageEventStream,
	upstreamModel: Model<Api>,
	context: TranscriptContext,
	options: SimpleStreamOptions | undefined,
): void {
	const retries = Math.max(0, Math.trunc(envNum("ASSIST_RETRIES", 2)));
	const tempBase = envNum("ASSIST_TEMP_BASE", 0.2);
	const tempStep = envNum("ASSIST_TEMP_STEP", 0.2);
	const tempCap = envNum("ASSIST_TEMP_CAP", 0.8);
	const seedBase = envNum("ASSIST_SEED", 1);

	// Keep the host's native tool field in the context: it is what the host uses
	// to render tool-result turns and to execute a promoted call. The nudge only
	// adds the output-shape contract and the tool names on top.
	const tools = toolParams(collectTools(context));

	void (async () => {
		try {
			let lastResult: AttemptResult | undefined;
			for (let attempt = 0; attempt <= retries; attempt++) {
				const temperature = Math.min(tempCap, tempBase + attempt * tempStep);
				const seed = seedBase + attempt;
				const attemptOptions: SimpleStreamOptions = {
					...(options ?? {}),
					temperature,
					samplingParams: { ...(options?.samplingParams ?? {}), seed },
				};
				const attemptContext: TranscriptContext = {
					...context,
					messages: [...context.messages, buildForceNudge(context, attempt)],
				};
				const result = await runAttempt(upstreamModel, attemptContext, attemptOptions, tools);
				lastResult = result;

				// A hard error: surface it, no retry.
				const last = result.captured[result.captured.length - 1];
				if (last?.type === "error") {
					for (const event of result.captured) outer.push(event);
					outer.end(last.error);
					return;
				}
				// The turn acted: replay it, promoting a content call if needed.
				if (result.acted && result.done) {
					if (result.parsed) {
						for (const event of result.captured) {
							if (event.type !== "done") outer.push(event);
						}
						emitPromoted(outer, result.done, result.parsed);
					} else {
						for (const event of result.captured) outer.push(event);
						outer.end(result.done.message);
					}
					return;
				}
				// Prose only: discard and retry while attempts remain.
			}
			// Attempts exhausted: surface the last prose turn as-is.
			if (lastResult?.done) {
				for (const event of lastResult.captured) outer.push(event);
				outer.end(lastResult.done.message);
				return;
			}
			if (lastResult) {
				const last = lastResult.captured[lastResult.captured.length - 1];
				for (const event of lastResult.captured) outer.push(event);
				if (last?.type === "error") outer.end(last.error);
			}
		} catch (error) {
			throw error instanceof Error ? error : new Error(String(error));
		}
	})();
}

/** Delegate to openai-completions, then promote a content-embedded tool call if the turn produced none. */
function streamWithAssist(
	model: Model<Api>,
	context: TranscriptContext,
	options?: SimpleStreamOptions,
): AssistantMessageEventStream {
	const outer = createAssistantMessageEventStream();
	const upstreamModel = { ...model, api: UPSTREAM_API } as Model<Api>;
	// ASSIST_FORCE_TOOLS=1 turns on the buffered retry path that pushes a tiny
	// model to tool-call; otherwise stream the one pass through live.
	if (envFlag("ASSIST_FORCE_TOOLS")) streamForced(outer, upstreamModel, context, options);
	else streamLive(outer, upstreamModel, context, options);
	return outer;
}

export default function (pi: ExtensionAPI): void {
	// Endpoint and model are env-configurable so the same plugin can front any
	// small OpenAI-compatible server (oMLX, mlx_lm.server, ...) for a test.
	const baseUrl = process.env.ASSIST_BASE_URL ?? "http://127.0.0.1:8001/v1";
	const modelId = process.env.ASSIST_MODEL_ID ?? "mlx-community--Qwen2.5-Coder-1.5B-Instruct-4bit";
	pi.registerProvider("content-assist", {
		baseUrl,
		// Loopback inference servers here need no auth; a literal placeholder
		// satisfies the "models require a key" check and is ignored upstream.
		apiKey: "not-needed",
		api: ASSIST_API,
		models: [
			{
				id: modelId,
				name: `${modelId} (content-assist)`,
				reasoning: false,
				input: ["text"],
				cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
				contextWindow: 32768,
				maxTokens: 4096,
			},
		],
		streamSimple: streamWithAssist,
	});
}
