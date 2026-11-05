/**
 * Deep-merge a JSON fragment into a JSON file, by id for arrays of objects.
 *
 *   node scripts/merge-json.mjs ~/.pi/agent/models.json templates/pi/models.llamacpp.json          # preview
 *   node scripts/merge-json.mjs ~/.pi/agent/models.json templates/pi/models.llamacpp.json --write  # apply
 *
 * --write copies the target to <target>.bak-mellum-<timestamp> first.
 * Only for plain JSON files. JSONC is not supported; it has comments and
 * trailing commas that JSON.parse rejects, so edit that by hand.
 */
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const isObject = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const hasId = (arr) => arr.length > 0 && arr.every((x) => isObject(x) && typeof x.id === "string");
const isObjectArray = (arr) => arr.every(isObject);

// Stable form for deep equality: object keys sorted, so key order does not matter.
function canon(v) {
	if (Array.isArray(v)) return `[${v.map(canon).join(",")}]`;
	if (isObject(v)) return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canon(v[k])}`).join(",")}}`;
	return JSON.stringify(v);
}

export function mergeJson(target, fragment) {
	if (Array.isArray(target) && Array.isArray(fragment)) {
		if (hasId(target) && hasId(fragment)) {
			const out = target.map((x) => structuredClone(x));
			for (const item of fragment) {
				const i = out.findIndex((x) => x.id === item.id);
				if (i === -1) out.push(structuredClone(item));
				else out[i] = mergeJson(out[i], item);
			}
			return out;
		}
		if (isObjectArray(target) && isObjectArray(fragment)) {
			// Mixed or partly id-less object arrays: keep every target entry, append fragment entries not already present.
			const out = target.map((x) => structuredClone(x));
			const seen = new Set(out.map(canon));
			for (const item of fragment) {
				const key = canon(item);
				if (!seen.has(key)) {
					out.push(structuredClone(item));
					seen.add(key);
				}
			}
			return out;
		}
		// Scalar arrays (and mixed scalar/object arrays) are replaced.
		return structuredClone(fragment);
	}
	if (isObject(target) && isObject(fragment)) {
		const out = { ...target };
		for (const [k, v] of Object.entries(fragment)) out[k] = k in target ? mergeJson(target[k], v) : structuredClone(v);
		return out;
	}
	return structuredClone(fragment);
}

function readJsonObject(path, label) {
	let value;
	try {
		value = JSON.parse(readFileSync(path, "utf8"));
	} catch (err) {
		console.error(`${label} ${path} is not valid JSON (JSONC comments are not supported): ${err.message}`);
		process.exit(1);
	}
	if (!isObject(value)) {
		console.error(`${label} ${path} must contain a JSON object at the root`);
		process.exit(1);
	}
	return value;
}

function main(argv) {
	const [targetArg, fragmentArg, flag] = argv;
	if (!targetArg || !fragmentArg) {
		console.error("usage: merge-json.mjs <target.json> <fragment.json> [--write]");
		process.exit(2);
	}
	const target = resolve(targetArg.replace(/^~(?=$|\/)/, process.env.HOME ?? "~"));
	const fragmentPath = resolve(fragmentArg);
	const current = existsSync(target) ? readJsonObject(target, "target") : {};
	const fragment = readJsonObject(fragmentPath, "fragment");
	const merged = mergeJson(current, fragment);
	const before = JSON.stringify(current, null, 2) + "\n";
	const after = JSON.stringify(merged, null, 2) + "\n";
	if (before === after) {
		console.log(`no change: ${target} already contains the fragment`);
		return;
	}
	if (flag !== "--write") {
		// Print only the subtrees the fragment touches, so unrelated secrets stay out of the transcript.
		for (const [k, v] of Object.entries(fragment)) {
			if (isObject(v) && isObject(merged[k])) {
				for (const k2 of Object.keys(v)) console.log(`${k}.${k2} (after merge):\n${JSON.stringify(merged[k][k2], null, 2)}\n`);
			} else console.log(`${k} (after merge):\n${JSON.stringify(merged[k], null, 2)}\n`);
		}
		console.log(`(preview only; add --write to update ${target})`);
		return;
	}
	mkdirSync(dirname(target), { recursive: true });
	if (existsSync(target)) {
		const backup = `${target}.bak-mellum-${new Date().toISOString().replace(/[:.]/g, "")}`;
		copyFileSync(target, backup);
		console.log(`backup: ${backup}`);
	}
	writeFileSync(target, after);
	console.log(`wrote ${target}`);
}

if (process.argv[1] && resolve(process.argv[1]).endsWith("merge-json.mjs")) main(process.argv.slice(2));
