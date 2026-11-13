/**
 * mellum-think-tags: reasoning that comes back as `<think>` text becomes a thinking block again.
 *
 * Pi reads reasoning from the server's reasoning field and never scans reply text for tags; that
 * split is the serving stack's job (vLLM's reasoning parser). A host whose streaming parser misses
 * every turn after the first returns the reasoning as text instead, opened by a literal `<think>`
 * (docs/superpowers/research/2026-10-29-lan-reasoning-leak.md). Pi then shows it as the reply and
 * sends it back as things the model said. At `message_end` this moves a leading `<think>…</think>`
 * into a thinking block, so the session, the display and the next request match a correctly
 * served one. A reply without a leading tag is returned unchanged: on a correct host it does
 * nothing. Not a remedy: it repairs serving, not the model's behaviour.
 */

type Part = { type: string; text?: string; thinking?: string; [key: string]: unknown };
type Message = { role: string; content?: Part[] | string; [key: string]: unknown };

const OPEN = "<think>";
const CLOSE = "</think>";

/** The message with each text part that opens with `<think>` split into thinking and text. */
export function splitThinkTags<M extends Message>(message: M): M {
	if (message.role !== "assistant" || !Array.isArray(message.content)) return message;
	let changed = false;
	const content: Part[] = [];
	for (const part of message.content) {
		const text = part.type === "text" ? part.text ?? "" : "";
		if (!text.trimStart().startsWith(OPEN)) {
			content.push(part);
			continue;
		}
		changed = true;
		const body = text.trimStart().slice(OPEN.length);
		const end = body.indexOf(CLOSE);
		// Labelled with the reasoning field, as Pi labels reasoning it streamed: Pi sends a thinking
		// block back to the server under that field, and drops an unlabelled one.
		content.push({ type: "thinking", thinkingSignature: "reasoning", thinking: end < 0 ? body : body.slice(0, end) });
		const rest = end < 0 ? "" : body.slice(end + CLOSE.length).replace(/^\s+/, "");
		if (rest) content.push({ type: "text", text: rest });
	}
	return changed ? { ...message, content } : message;
}

export default function (pi: any): void {
	pi.on("message_end", (event: { message: Message }) => {
		const fixed = splitThinkTags(event.message);
		return fixed === event.message ? undefined : { message: fixed };
	});
}
