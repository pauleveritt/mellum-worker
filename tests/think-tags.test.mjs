import { test } from "node:test";
import assert from "node:assert/strict";

// A serving host whose streaming reasoning parser misses turns after the first returns the
// reasoning as text, opened by a literal <think> (docs/superpowers/research/2026-10-29-lan-reasoning-leak.md).
const adapter = () => import("../extensions/mellum-think-tags.ts");

test("reasoning returned as <think> text becomes a thinking block; the answer stays text", async () => {
	const { splitThinkTags } = await adapter();
	const call = { type: "toolCall", id: "c1", name: "bash", arguments: { command: "ls" } };
	const m = { role: "assistant", content: [{ type: "text", text: "<think>\nList first.\n</think>\n\nHere goes." }, call] };
	assert.deepEqual(splitThinkTags(m).content, [
		{ type: "thinking", thinkingSignature: "reasoning", thinking: "\nList first.\n" },
		{ type: "text", text: "Here goes." },
		call,
	]);
});

test("a reply that is only reasoning, or reasoning cut off before </think>, keeps no empty text", async () => {
	const { splitThinkTags } = await adapter();
	assert.deepEqual(splitThinkTags({ role: "assistant", content: [{ type: "text", text: "<think>\n\n</think>\n\n" }] }).content,
		[{ type: "thinking", thinkingSignature: "reasoning", thinking: "\n\n" }]);
	assert.deepEqual(splitThinkTags({ role: "assistant", content: [{ type: "text", text: "<think>\nstill going" }] }).content,
		[{ type: "thinking", thinkingSignature: "reasoning", thinking: "\nstill going" }]);
});

test("a correctly served reply, a user message, and text that only mentions <think> are left alone", async () => {
	const { splitThinkTags } = await adapter();
	const served = { role: "assistant", content: [{ type: "thinking", thinkingSignature: "reasoning", thinking: "x" }, { type: "text", text: "Done." }] };
	assert.equal(splitThinkTags(served), served);
	const user = { role: "user", content: [{ type: "text", text: "<think>hi</think>" }] };
	assert.equal(splitThinkTags(user), user);
	const mention = { role: "assistant", content: [{ type: "text", text: "The tag <think> marks reasoning." }] };
	assert.equal(splitThinkTags(mention), mention);
});

test("the extension replaces the finished message only when it changed", async () => {
	const { default: install } = await adapter();
	const handlers = {};
	install({ on: (event, fn) => { handlers[event] = fn; } });
	assert.deepEqual(Object.keys(handlers), ["message_end"]);
	const leaked = { role: "assistant", content: [{ type: "text", text: "<think>r</think>ok" }] };
	assert.deepEqual(handlers.message_end({ type: "message_end", message: leaked }).message.content,
		[{ type: "thinking", thinkingSignature: "reasoning", thinking: "r" }, { type: "text", text: "ok" }]);
	assert.equal(handlers.message_end({ type: "message_end", message: { role: "assistant", content: [{ type: "text", text: "ok" }] } }), undefined);
});

test("the thinking block is labelled with the reasoning field, so Pi sends it back as reasoning", async () => {
	// Pi's openai-completions provider returns a thinking block to the server under the field named by
	// its thinkingSignature; an unlabelled block is dropped from the next request.
	const { splitThinkTags } = await adapter();
	const [thinking] = splitThinkTags({ role: "assistant", content: [{ type: "text", text: "<think>r</think>ok" }] }).content;
	assert.equal(thinking.thinkingSignature, "reasoning");
});
