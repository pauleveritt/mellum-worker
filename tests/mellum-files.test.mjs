import { test } from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";
import { Buffer } from "node:buffer";

import {
	decodeEntities,
	stripXml,
	readZip,
	docxText,
	sharedStrings,
	sheetRows,
	xlsxText,
	pdfTextFromContent,
	pdfText,
	docKind,
} from "../extensions/mellum-files.ts";

/** Build a minimal STORED (uncompressed) zip the reader can parse. */
function storedZip(files) {
	const locals = [];
	let offset = 0;
	for (const f of files) {
		const name = Buffer.from(f.name);
		const data = Buffer.isBuffer(f.data) ? f.data : Buffer.from(f.data);
		const lh = Buffer.alloc(30);
		lh.writeUInt32LE(0x04034b50, 0);
		lh.writeUInt16LE(20, 4);
		lh.writeUInt32LE(data.length, 18);
		lh.writeUInt32LE(data.length, 22);
		lh.writeUInt16LE(name.length, 26);
		locals.push({ buf: Buffer.concat([lh, name, data]), offset, name, size: data.length });
		offset += lh.length + name.length + data.length;
	}
	const localBuf = Buffer.concat(locals.map((l) => l.buf));
	const centrals = [];
	for (const l of locals) {
		const ch = Buffer.alloc(46);
		ch.writeUInt32LE(0x02014b50, 0);
		ch.writeUInt16LE(20, 4);
		ch.writeUInt16LE(20, 6);
		ch.writeUInt16LE(0, 10); // method = stored
		ch.writeUInt32LE(l.size, 20);
		ch.writeUInt32LE(l.size, 24);
		ch.writeUInt16LE(l.name.length, 28);
		ch.writeUInt32LE(l.offset, 42);
		centrals.push(Buffer.concat([ch, l.name]));
	}
	const cdBuf = Buffer.concat(centrals);
	const eocd = Buffer.alloc(22);
	eocd.writeUInt32LE(0x06054b50, 0);
	eocd.writeUInt16LE(files.length, 8);
	eocd.writeUInt16LE(files.length, 10);
	eocd.writeUInt32LE(cdBuf.length, 12);
	eocd.writeUInt32LE(localBuf.length, 16);
	return Buffer.concat([localBuf, cdBuf, eocd]);
}

test("decodeEntities: named, numeric and ampersand-last", () => {
	assert.equal(decodeEntities("a &lt;b&gt; &amp; &#65; &quot;c&quot;"), 'a <b> & A "c"');
});

test("stripXml: tags gone, entities decoded, blank runs collapsed", () => {
	assert.equal(stripXml("<a>Hello</a>\n\n\n<b>&amp;</b> world"), "Hello\n\n& world");
});

test("docKind: by extension, defaulting to text", () => {
	assert.equal(docKind("report.PDF"), "pdf");
	assert.equal(docKind("notes.docx"), "docx");
	assert.equal(docKind("data.xlsx"), "xlsx");
	assert.equal(docKind("readme.md"), "text");
});

test("readZip: central-directory walk returns each member's bytes", () => {
	const zip = storedZip([
		{ name: "a.txt", data: "alpha" },
		{ name: "dir/b.txt", data: "beta" },
	]);
	const entries = readZip(zip);
	assert.equal(entries.get("a.txt").toString(), "alpha");
	assert.equal(entries.get("dir/b.txt").toString(), "beta");
});

test("docxText: paragraphs become lines", () => {
	const document =
		"<w:document><w:body>" +
		"<w:p><w:r><w:t>Hello</w:t></w:r></w:p>" +
		"<w:p><w:r><w:t>World</w:t></w:r></w:p>" +
		"</w:body></w:document>";
	const buf = storedZip([{ name: "word/document.xml", data: document }]);
	assert.equal(docxText(buf), "Hello\nWorld");
});

test("sharedStrings + sheetRows: shared-string refs resolve to their text", () => {
	const strings = sharedStrings("<sst><si><t>Name</t></si><si><t>Age</t></si></sst>");
	assert.deepEqual(strings, ["Name", "Age"]);
	const rows = sheetRows(
		"<worksheet><sheetData>" +
			'<row><c t="s"><v>0</v></c><c t="s"><v>1</v></c></row>' +
			"<row><c><v>42</v></c></row>" +
			"</sheetData></worksheet>",
		strings,
	);
	assert.deepEqual(rows, [["Name", "Age"], ["42"]]);
});

test("xlsxText: a workbook renders as tab-separated rows", () => {
	const buf = storedZip([
		{ name: "xl/sharedStrings.xml", data: "<sst><si><t>Name</t></si><si><t>Age</t></si></sst>" },
		{
			name: "xl/worksheets/sheet1.xml",
			data:
				"<worksheet><sheetData>" +
				'<row><c t="s"><v>0</v></c><c t="s"><v>1</v></c></row>' +
				"<row><c><v>42</v></c></row>" +
				"</sheetData></worksheet>",
		},
	]);
	assert.equal(xlsxText(buf), "Name\tAge\n42");
});

test("pdfTextFromContent: Tj and TJ operators", () => {
	assert.equal(pdfTextFromContent("BT (Hello) Tj ET"), "Hello");
	assert.equal(pdfTextFromContent("[(Wor) -250 (ld)] TJ"), "World");
});

test("pdfText: reads an uncompressed content stream", () => {
	const pdf = "%PDF-1.4\n1 0 obj\n<<>>\nstream\nBT (Hello PDF) Tj ET\nendstream\nendobj\n";
	assert.match(pdfText(Buffer.from(pdf, "latin1")), /Hello PDF/);
});

test("pdfText: inflates a FlateDecode content stream", () => {
	const content = deflateSync(Buffer.from("BT (Hi Flate) Tj ET"));
	const head = Buffer.from("%PDF-1.4\n1 0 obj\n<</Filter/FlateDecode>>\nstream\n", "latin1");
	const tail = Buffer.from("\nendstream\nendobj\n", "latin1");
	assert.match(pdfText(Buffer.concat([head, content, tail])), /Hi Flate/);
});
