/** Remedy unit: reasoning the server returns as `<think>` text goes back into a thinking block. */
import repairThinkTags from "../../extensions/mellum-think-tags.ts";
import { type PiLike, type UnitMeta } from "../install.ts";

export const meta: UnitMeta = {
	pathology: "Reasoning comes back as `<think>` text and is fed back as speech",
	does: "Turns a leading `<think>` reply back into a thinking block",
	lesson: "E1",
	evidence: "LAN vLLM host: 236 of 244 turns leaked; 0 of 136 on the pinned vLLM 0.32.0",
};

export function install(pi: PiLike): void {
	repairThinkTags(pi);
}

export default install;
