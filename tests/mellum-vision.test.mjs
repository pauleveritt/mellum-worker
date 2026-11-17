import { test } from "node:test";
import assert from "node:assert/strict";

import {
	isImage,
	visionArgs,
	parseVisionOutput,
	DEFAULT_VISION_MODEL,
} from "../extensions/mellum-vision.ts";

test("isImage: common raster formats, case-insensitive; not a document", () => {
	assert.equal(isImage("shot.PNG"), true);
	assert.equal(isImage("photo.jpeg"), true);
	assert.equal(isImage("scan.tiff"), true);
	assert.equal(isImage("report.pdf"), false);
	assert.equal(isImage("notes.txt"), false);
});

test("visionArgs: the model id is passed as --model (so mlx_vlm auto-downloads it)", () => {
	const args = visionArgs(DEFAULT_VISION_MODEL, ["/a.png", "/b.png"], "what is this?", 128);
	assert.deepEqual(args.slice(0, 4), ["-m", "mlx_vlm.generate", "--model", DEFAULT_VISION_MODEL]);
	assert.ok(args.includes("--image") && args.includes("/a.png") && args.includes("/b.png"));
	assert.equal(args[args.indexOf("--max-tokens") + 1], "128");
	assert.equal(args[args.indexOf("--prompt") + 1], "what is this?");
});

test("parseVisionOutput: keeps the fenced answer when the CLI frames it", () => {
	const out = "Fetching 11 files: 100%\n==========\nA red square on white.\n==========\nPrompt: 12 tokens\nGeneration: 8 tokens";
	assert.equal(parseVisionOutput(out), "A red square on white.");
});

test("parseVisionOutput: drops progress/stats lines when unfenced (real mlx_vlm sample)", () => {
	const real =
		"Fetching 11 files:   0%|          | 0/11 [00:00<?, ?it/s]Fetching 11 files: 100%|██████████| 11/11 [00:00<00:00, 3688.63it/s]\n" +
		"This dashboard shows the status of multiple runs in a testing environment, including successful and failed tests.\n";
	assert.equal(
		parseVisionOutput(real),
		"This dashboard shows the status of multiple runs in a testing environment, including successful and failed tests.",
	);
});

test("parseVisionOutput: a multi-line answer is preserved", () => {
	const out = "Fetching 11 files: 100%\nLine one.\nLine two.\n";
	assert.equal(parseVisionOutput(out), "Line one.\nLine two.");
});
