/**
 * improve_distill — the writable carry-forward step for the improvement loop.
 *
 * `scripts/mellum.mjs learn` reports what the runs would add to AGENTS.md but never writes.
 * The improvement loop needs the write: after a rep, fold what the run records teach into the
 * carried `## Mellum` section so the next rep starts knowing it. This is pure
 * `learnFromTexts` + `mergeSuggestion` (both from mellum-learn, both tested there) plus a thin
 * file writer. It is independent of the measurement path — it only reads records and writes a
 * carried AGENTS.md the loop owns, never the frozen suite.
 *
 * CLI:
 *   node improve_distill.mjs --records <jsonl> --agents <AGENTS.md> --cwd <ancestor> [--n 20]
 * reads the records, merges the lesson bullets into the AGENTS.md at --agents, writes it back.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

import { learnFromTexts, mergeSuggestion } from "../../extensions/mellum-learn.ts";

/** Distil the records' lessons and merge them into the carried AGENTS.md text. Pure. */
export function distill({ recordsText, agentsMd, cwd, n = 20 }) {
	const report = learnFromTexts([recordsText], { cwd, n });
	const merged = mergeSuggestion(agentsMd, report.suggestion);
	return {
		text: merged.text || agentsMd || "",
		added: merged.added,
		conflicts: merged.conflicts,
		suggestion: report.suggestion,
	};
}

/**
 * Lessons from a graded run (`run.json`), not the mode-record file. The harness always writes
 * run.json, and it carries the verdicts the mode records miss — `out_of_layout` (the run left
 * files the layout does not name) and `contaminated` (it touched the tests or the grader). These
 * are the failures the first live loop actually hit, and the channel that is reliably present.
 * The bullets are general discipline, derived from the harness verdict, with no suite-specific
 * route, table or value.
 */
export function lessonsFromVerdict(run) {
	const bullets = [];
	if ((run?.out_of_layout || []).length > 0) {
		bullets.push("Do not: add files the project layout does not name; keep changes to the files the spec lists");
	}
	if (run?.contaminated) {
		bullets.push("Do not: add, edit or delete tests; the acceptance tests are provided and run after you finish");
	}
	return bullets;
}

/** Merge a graded run's verdict lessons into the carried AGENTS.md text. Pure. */
export function distillFromRun({ run, agentsMd }) {
	const bullets = lessonsFromVerdict(run);
	const merged = mergeSuggestion(agentsMd, bullets);
	return {
		text: merged.text || agentsMd || "",
		added: merged.added,
		conflicts: merged.conflicts,
		bullets,
	};
}

function parseArgs(argv) {
	const o = { n: 20 };
	for (let i = 0; i < argv.length; i++) {
		if (argv[i] === "--records") o.records = argv[++i];
		else if (argv[i] === "--agents") o.agents = argv[++i];
		else if (argv[i] === "--cwd") o.cwd = argv[++i];
		else if (argv[i] === "--run") o.run = argv[++i];
		else if (argv[i] === "--n") o.n = Number.parseInt(argv[++i] ?? "20", 10) || 20;
	}
	return o;
}

const read = (p) => {
	try {
		return readFileSync(p, "utf8");
	} catch {
		return undefined;
	}
};

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
	const o = parseArgs(process.argv.slice(2));
	if (!o.agents || (!o.records && !o.run)) {
		console.error("usage: improve_distill.mjs --agents <AGENTS.md> [--records <jsonl> --cwd <ancestor>] [--run <run.json>] [--n N]");
		process.exit(2);
	}
	let text = read(o.agents);
	const added = [];
	// Mode records (when present) via mellum-learn's patterns...
	if (o.records && o.cwd) {
		const r = distill({ recordsText: read(o.records) ?? "", agentsMd: text, cwd: o.cwd, n: o.n });
		text = r.text;
		added.push(...r.added);
	}
	// ...and the graded run's verdicts (the channel the harness always writes).
	if (o.run) {
		let run = {};
		try {
			run = JSON.parse(read(o.run) ?? "{}");
		} catch {
			run = {};
		}
		const r = distillFromRun({ run, agentsMd: text });
		text = r.text;
		added.push(...r.added);
	}
	writeFileSync(o.agents, text);
	if (added.length) console.log(`carried forward ${added.length} lesson(s):\n${added.map((b) => `  - ${b}`).join("\n")}`);
	else console.log("nothing new to carry forward");
}
