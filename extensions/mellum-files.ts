/**
 * mellum-files — understand documents the worker otherwise cannot read: PDF,
 * Word (.docx) and Excel (.xlsx), plus plain text (a Pi extension; agnostic).
 *
 * Office files are ZIP archives of XML; this reads them with a small pure-Node
 * zip reader (the central directory, so Office's streamed data-descriptor files
 * work) and `node:zlib` — no npm dependency, no external tool. PDF text is
 * pulled best-effort from the page content streams (FlateDecode inflated, text
 * operators read). A scanned, image-only PDF has no text to pull; that is what
 * `mellum-vision` is for.
 *
 * Extracted text is indexed into the `mellum-context` store, so a large
 * document becomes searchable context instead of being loaded whole.
 *
 *   /read-file <path>   extract text from a document and index it for /context
 *
 * Self-contained: `node:zlib` + `node:fs` + Pi hooks; loads with `-e` or
 * `--pi-extension`.
 */
import { inflateRawSync, inflateSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { extname, resolve } from "node:path";
import { openIndex, indexDoc } from "./mellum-context.ts";

/** Decode the XML entities that appear in document text. */
export function decodeEntities(s: string): string {
	return s
		.replace(/&lt;/g, "<")
		.replace(/&gt;/g, ">")
		.replace(/&quot;/g, '"')
		.replace(/&apos;/g, "'")
		.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
		.replace(/&#x([0-9a-fA-F]+);/g, (_, n) => String.fromCodePoint(parseInt(n, 16)))
		.replace(/&amp;/g, "&"); // last, so "&amp;lt;" does not double-decode
}

/** Strip XML tags to their text, decoding entities and collapsing blank runs. */
export function stripXml(xml: string): string {
	return decodeEntities(xml.replace(/<[^>]*>/g, ""))
		.replace(/[ \t]+\n/g, "\n")
		.replace(/\n{3,}/g, "\n\n")
		.trim();
}

/** Read a ZIP buffer's entries via its central directory → name -> decompressed bytes. */
export function readZip(buf: Buffer): Map<string, Buffer> {
	const out = new Map<string, Buffer>();
	// End of Central Directory: scan back for the signature 0x06054b50.
	let eocd = -1;
	for (let i = buf.length - 22; i >= 0; i--) {
		if (buf.readUInt32LE(i) === 0x06054b50) {
			eocd = i;
			break;
		}
	}
	if (eocd < 0) return out;
	const count = buf.readUInt16LE(eocd + 10);
	let p = buf.readUInt32LE(eocd + 16); // central directory offset
	for (let n = 0; n < count && p + 46 <= buf.length; n++) {
		if (buf.readUInt32LE(p) !== 0x02014b50) break;
		const method = buf.readUInt16LE(p + 10);
		const compSize = buf.readUInt32LE(p + 20);
		const nameLen = buf.readUInt16LE(p + 28);
		const extraLen = buf.readUInt16LE(p + 30);
		const commentLen = buf.readUInt16LE(p + 32);
		const localOff = buf.readUInt32LE(p + 42);
		const name = buf.toString("utf8", p + 46, p + 46 + nameLen);
		// Jump to the local header to find where the data actually starts.
		if (buf.readUInt32LE(localOff) === 0x04034b50) {
			const lNameLen = buf.readUInt16LE(localOff + 26);
			const lExtraLen = buf.readUInt16LE(localOff + 28);
			const dataStart = localOff + 30 + lNameLen + lExtraLen;
			const data = buf.subarray(dataStart, dataStart + compSize);
			try {
				out.set(name, method === 0 ? Buffer.from(data) : inflateRawSync(data));
			} catch {
				// skip an entry that will not inflate
			}
		}
		p += 46 + nameLen + extraLen + commentLen;
	}
	return out;
}

/** The visible text of a .docx buffer, paragraph by paragraph. */
export function docxText(buf: Buffer): string {
	const xml = readZip(buf).get("word/document.xml");
	if (!xml) return "";
	const withBreaks = xml
		.toString("utf8")
		.replace(/<\/w:p>/g, "\n")
		.replace(/<w:tab\/?>/g, "\t")
		.replace(/<w:br\/?>/g, "\n");
	return stripXml(withBreaks);
}

/** The shared-strings table of a .xlsx (index -> string). */
export function sharedStrings(xml: string): string[] {
	return (xml.match(/<si>[\s\S]*?<\/si>/g) || []).map((si) =>
		stripXml(si).replace(/\n+/g, " ").trim(),
	);
}

/** The cells of one worksheet as rows of text, resolving shared-string refs. */
export function sheetRows(sheetXml: string, strings: string[]): string[][] {
	const rows: string[][] = [];
	for (const row of sheetXml.match(/<row[\s>][\s\S]*?<\/row>/g) || []) {
		const cells: string[] = [];
		for (const c of row.match(/<c\b[^>]*>[\s\S]*?<\/c>|<c\b[^>]*\/>/g) || []) {
			const type = /\bt="([^"]+)"/.exec(c)?.[1];
			const v = /<v>([\s\S]*?)<\/v>/.exec(c)?.[1];
			if (type === "s" && v !== undefined) {
				cells.push(strings[Number(v)] ?? "");
			} else if (type === "inlineStr" || type === "str") {
				cells.push(stripXml(c));
			} else if (v !== undefined) {
				cells.push(decodeEntities(v));
			} else {
				cells.push("");
			}
		}
		rows.push(cells);
	}
	return rows;
}

/** The visible text of a .xlsx buffer: every sheet, rows tab-separated. */
export function xlsxText(buf: Buffer): string {
	const zip = readZip(buf);
	const strings = sharedStrings(zip.get("xl/sharedStrings.xml")?.toString("utf8") || "");
	const sheets = [...zip.keys()].filter((k) => /^xl\/worksheets\/sheet\d+\.xml$/.test(k)).sort();
	const blocks: string[] = [];
	for (const name of sheets) {
		const rows = sheetRows(zip.get(name)!.toString("utf8"), strings);
		blocks.push(rows.map((r) => r.join("\t")).join("\n"));
	}
	return blocks.join("\n\n").trim();
}

/** Decode the string operands of a PDF text object (handles \( \) escapes). */
export function pdfTextFromContent(content: string): string {
	const out: string[] = [];
	// (string) Tj  and  [ (a) -250 (b) ] TJ
	for (const m of content.matchAll(/\(((?:\\.|[^\\()])*)\)\s*Tj/g)) out.push(unescapePdf(m[1]));
	for (const m of content.matchAll(/\[((?:[^\][]|\\.)*)\]\s*TJ/g)) {
		const parts = [...m[1].matchAll(/\(((?:\\.|[^\\()])*)\)/g)].map((x) => unescapePdf(x[1]));
		out.push(parts.join(""));
	}
	return out.join("\n");
}

function unescapePdf(s: string): string {
	return s
		.replace(/\\n/g, "\n")
		.replace(/\\r/g, "\r")
		.replace(/\\t/g, "\t")
		.replace(/\\([()\\])/g, "$1");
}

/** Best-effort text of a PDF buffer: inflate FlateDecode streams, read text ops. */
export function pdfText(buf: Buffer): string {
	const raw = buf.toString("latin1");
	const chunks: string[] = [];
	const re = /stream\r?\n/g;
	let m: RegExpExecArray | null;
	while ((m = re.exec(raw))) {
		const start = m.index + m[0].length;
		const end = raw.indexOf("endstream", start);
		if (end < 0) continue;
		const bytes = Buffer.from(raw.slice(start, end), "latin1");
		let text = "";
		try {
			text = inflateSync(bytes).toString("latin1");
		} catch {
			text = bytes.toString("latin1"); // uncompressed content stream
		}
		if (text.includes("Tj") || text.includes("TJ")) chunks.push(pdfTextFromContent(text));
	}
	return chunks.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export type DocKind = "pdf" | "docx" | "xlsx" | "text";

/** Which extractor a path maps to. */
export function docKind(path: string): DocKind {
	const ext = extname(path).toLowerCase();
	if (ext === ".pdf") return "pdf";
	if (ext === ".docx") return "docx";
	if (ext === ".xlsx") return "xlsx";
	return "text";
}

/** Extract text from a document file by kind. */
export function extractDocument(path: string): string {
	const kind = docKind(path);
	if (kind === "text") return readFileSync(resolve(path), "utf8");
	const buf = readFileSync(resolve(path));
	if (kind === "docx") return docxText(buf);
	if (kind === "xlsx") return xlsxText(buf);
	return pdfText(buf);
}

export default function (pi: any) {
	pi.registerCommand?.("read-file", {
		description: "extract text from a PDF / Word / Excel / text file and index it for /context",
		handler: async (args: string, ctx: any) => {
			const path = (args || "").trim();
			if (!path) {
				ctx?.ui?.notify?.("mellum-files: /read-file <path>", "warning");
				return;
			}
			let text = "";
			try {
				text = extractDocument(path);
			} catch (e: any) {
				ctx?.ui?.notify?.(`mellum-files: cannot read ${path}: ${e?.message}`, "warning");
				return;
			}
			if (!text.trim()) {
				ctx?.ui?.notify?.(
					`mellum-files: no text found in ${path} (a scanned PDF? try mellum-vision)`,
					"warning",
				);
				return;
			}
			try {
				const db = openIndex(
					process.env.MELLUM_CONTEXT_DB || `${process.env.HOME}/.pi/agent/mellum-context.db`,
				);
				const n = indexDoc(db, path, text);
				db.close();
				ctx?.ui?.notify?.(`mellum-files: indexed ${n} chunks from ${path} — search with /context`, "info");
			} catch {
				ctx?.ui?.notify?.(`mellum-files: extracted ${text.length} chars from ${path}`, "info");
			}
		},
	});

	pi.registerTool?.("read_document", {
		description:
			"Extract the text of a PDF, Word (.docx), Excel (.xlsx) or text file. " +
			"Use this to read a document the normal file tools cannot.",
		parameters: {
			type: "object",
			properties: { path: { type: "string" } },
			required: ["path"],
		},
		handler: async (input: { path: string }) => {
			try {
				const text = extractDocument(input?.path || "");
				return text.trim() || `mellum-files: no text found in ${input?.path} (a scanned PDF? try mellum-vision)`;
			} catch (e: any) {
				return `mellum-files: cannot read ${input?.path}: ${e?.message}`;
			}
		},
	});
}
