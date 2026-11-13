/**
 * mellum-vision — let the worker see: describe or read text out of images and
 * screenshots with a small local vision model (a Pi extension; agnostic).
 *
 * JetBrains ships no vision model — Mellum is code and text only — so this
 * leans on a small open vision-language model served through MLX. The default
 * is `empero-ai/Qwen3.8-2B-Distill` (~2 B, a Qwen3.5 VLM). The model id is a
 * Hugging Face repo id, so `mlx_vlm` downloads it automatically on first use
 * when it is missing; nothing has to be fetched by hand. Point
 * `MELLUM_VISION_MODEL` at a local 4-bit copy for a smaller, faster load, or at
 * any other MLX vision model.
 *
 * Its natural partner is `mellum-files`: a scanned, image-only PDF or a
 * screenshot has no text to pull, so it comes here. Descriptions are indexed
 * into the `mellum-context` store, so what an image says becomes searchable.
 *
 *   /see <image> [question]   describe an image, or answer a question about it
 *
 * Self-contained Pi hooks; shells a Python MLX sidecar (`mlx_vlm.generate`).
 * The pure core (argv building, output parsing) is unit-tested.
 */
import { spawnSync } from "node:child_process";
import { extname, resolve } from "node:path";
import { openIndex, indexDoc } from "./mellum-context.ts";

export const DEFAULT_VISION_MODEL = "empero-ai/Qwen3.8-2B-Distill";
const IMAGE_EXTS = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff"]);

/** Whether a path is an image this model can read. */
export function isImage(path: string): boolean {
	return IMAGE_EXTS.has(extname(path).toLowerCase());
}

/** The argv for the MLX vision sidecar. The model id doubles as the download id. */
export function visionArgs(
	model: string,
	images: string[],
	prompt: string,
	maxTokens = 400,
): string[] {
	return [
		"-m",
		"mlx_vlm.generate",
		"--model",
		model,
		"--max-tokens",
		String(maxTokens),
		"--temperature",
		"0",
		"--image",
		...images,
		"--prompt",
		prompt,
	];
}

/**
 * Pull the model's answer out of `mlx_vlm.generate` stdout. The CLI frames the
 * response between `==========` rules and prints a stats block after it; this
 * keeps only the framed text, or, if the rules are absent, drops the known
 * stats / progress lines and returns the rest.
 */
export function parseVisionOutput(stdout: string): string {
	const text = stdout.replace(/\r/g, "");
	const fenced = text.match(/={6,}\s*\n([\s\S]*?)\n={6,}/);
	if (fenced) return fenced[1].trim();
	const dropped =
		/^\s*(Prompt:|Generation:|Peak memory:|Files:|Fetching|Prompt tokens|Generation tokens|==========|\d+\s+tokens-per-sec)/;
	return text
		.split("\n")
		.filter((line) => line.trim() && !dropped.test(line))
		.join("\n")
		.trim();
}

function model(): string {
	return process.env.MELLUM_VISION_MODEL || DEFAULT_VISION_MODEL;
}

function python(): string {
	return process.env.MELLUM_VISION_PYTHON || process.env.MLX_VLM_PYTHON || "python3";
}

/** Run the vision model on one or more images; returns its text answer. */
export function runVision(
	images: string[],
	prompt: string,
	opts: { model?: string; maxTokens?: number; python?: string } = {},
): string {
	const r = spawnSync(
		opts.python ?? python(),
		visionArgs(opts.model ?? model(), images.map((p) => resolve(p)), prompt, opts.maxTokens),
		{ encoding: "utf8", timeout: 600_000 },
	);
	if (r.status !== 0) {
		return `mellum-vision: the vision model failed: ${(r.stderr || r.stdout || "").trim().slice(-300)}`;
	}
	return parseVisionOutput(r.stdout || "");
}

export default function (pi: any) {
	pi.registerCommand?.("see", {
		description: "describe an image/screenshot, or answer a question about it, with the local vision model",
		handler: async (args: string, ctx: any) => {
			const parts = (args || "").trim().split(/\s+/);
			const image = parts.shift() || "";
			if (!image) {
				ctx?.ui?.notify?.("mellum-vision: /see <image> [question]", "warning");
				return;
			}
			const prompt = parts.join(" ") || "Describe this image in detail. Transcribe any text you can read.";
			ctx?.ui?.notify?.("mellum-vision: looking (the model downloads on first use)…", "info");
			const answer = runVision([image], prompt);
			try {
				const db = openIndex(process.env.MELLUM_CONTEXT_DB || `${process.env.HOME}/.pi/agent/mellum-context.db`);
				indexDoc(db, `vision:${image}`, answer);
				db.close();
			} catch {
				// indexing is a bonus; the answer still goes to the UI
			}
			ctx?.ui?.notify?.(answer, "info");
		},
	});

	pi.registerTool?.("describe_image", {
		description:
			"Describe an image or screenshot, or read the text in it, using a local vision model. " +
			"Use this for a picture, a diagram, or a scanned/image-only page the file tools cannot read.",
		parameters: {
			type: "object",
			properties: { path: { type: "string" }, question: { type: "string" } },
			required: ["path"],
		},
		handler: async (input: { path: string; question?: string }) => {
			if (!isImage(input?.path || "")) return `mellum-vision: ${input?.path} is not an image file`;
			return runVision(
				[input.path],
				input.question || "Describe this image in detail. Transcribe any text you can read.",
			);
		},
	});
}
