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

/** The remedies table: one row per unit, switched on in a live Pi with `/remedy on <unit>`. */
export function renderTable(units) {
	const rows = units.map(({ name, meta }) =>
		`| ${cell(meta.pathology)} | \`${name}\`: ${cell(meta.does)} | ${cell(meta.evidence)} | \`/remedy on ${name}\` |`);
	return [START, "", "| Pathology | Remedy unit | Evidence | Switch on |", "| --- | --- | --- | --- |", ...rows, "", END].join("\n");
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
