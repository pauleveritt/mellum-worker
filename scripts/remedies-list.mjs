#!/usr/bin/env node
// The remedies list: one table of pathologies and the remedy units that address them, generated
// from each unit's `meta` export and written into the Lessons index and The Challenge between
// `<!-- remedies:start -->` and `<!-- remedies:end -->`. `--check` exits 1 when a page is stale.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
export const PAGES = ["learn/challenge/remedies.md"];
const START = "<!-- remedies:start -->";
const END = "<!-- remedies:end -->";
const KINDS = ["guard", "nudge", "context", "prompt", "tool", "check", "workflow"];

/** Every unit under remedies/<kind>/<name>.ts, in kind order, with its meta. */
export async function listUnits() {
	const units = [];
	for (const kind of KINDS) {
		let files = [];
		try {
			files = readdirSync(join(ROOT, "remedies", kind)).filter((f) => f.endsWith(".ts")).sort();
		} catch {
			continue;
		}
		for (const file of files) {
			const { meta } = await import(pathToFileURL(join(ROOT, "remedies", kind, file)).href);
			units.push({ name: `${kind}/${file.replace(/\.ts$/, "")}`, meta });
		}
	}
	return units;
}

const cell = (text) => text.replace(/\|/g, "\\|");

/** A readable heading for each kind, in the order units are listed. */
const KIND_LABELS = {
	guard: "Guards",
	nudge: "Nudges",
	context: "Context",
	prompt: "Prompts",
	tool: "Tools",
	check: "Checks",
	workflow: "Workflows",
};

/** The remedies table, grouped by kind: a `###` section per category, each its own table. */
export function renderTable(units) {
	const out = [START, ""];
	for (const kind of KINDS) {
		const group = units.filter((u) => u.name.startsWith(`${kind}/`));
		if (!group.length) continue;
		out.push(`### ${KIND_LABELS[kind] ?? kind}`, "", "| Pathology | Remedy unit | Evidence | Switch on |", "| --- | --- | --- | --- |");
		for (const { name, meta } of group) {
			out.push(`| ${cell(meta.pathology)} | \`${name}\`: ${cell(meta.does)} | ${cell(meta.evidence)} | \`/remedy on ${name}\` |`);
		}
		out.push("");
	}
	out.push(END);
	return out.join("\n");
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
	const check = process.argv.includes("--check");
	const units = await listUnits();
	let stale = false;
	for (const page of PAGES) {
		const path = join(ROOT, page);
		const text = readFileSync(path, "utf8");
		const table = renderTable(units);
		const at = text.indexOf(START);
		const end = text.indexOf(END);
		if (at < 0 || end < 0) {
			console.error(`${page}: no ${START} … ${END} markers`);
			stale = true;
			continue;
		}
		const next = text.slice(0, at) + table + text.slice(end + END.length);
		if (next !== text) {
			stale = true;
			if (!check) writeFileSync(path, next);
		}
		console.log(`${page}: ${next === text ? "current" : check ? "STALE" : "updated"}`);
	}
	process.exit(check && stale ? 1 : 0);
}
