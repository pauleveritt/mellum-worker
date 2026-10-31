/** Remedy unit: reasoning the server returns as `<think>` text goes back into a thinking block. */
import repairThinkTags from "../../extensions/mellum-think-tags.ts";
import { type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "The serving stack returns reasoning as `<think>` text, and the model is fed it back as things it said",
	does: "Moves a leading `<think>…</think>` in a reply into a thinking block, sent back as reasoning; leaves a correctly served reply alone",
	lesson: "E1",
	evidence: "LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0",
};

export function install(pi: PiLike): void {
	repairThinkTags(pi);
}

export default install;
