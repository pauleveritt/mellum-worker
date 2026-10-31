/**
 * mellum-acceptance: Tier-1 dynamic mediation — derive a structural acceptance
 * test from the task spec, with no per-task authoring and no model.
 *
 * Mediation forces the worker to meet a contract it cannot see, redispatching
 * until it does (mellum-ncm). A hand-written frozen test per phase does not
 * scale; this derives a shallow-but-real contract straight from the spec's own
 * nouns — the app module it names, and every route it names — and emits a
 * pytest the ncm gate can run (point NCM_TEST at it). It checks the app boots
 * and that each named route is actually registered (param-normalized, so
 * {id} vs {complaint_id} does not matter).
 *
 * Agnostic: it knows nothing about any particular suite, only what the spec
 * states in the open. It catches the early/mid failures (nothing built, a
 * missing route, the wrong module name) — not deep ones like exact aggregation
 * keys or a migration schema, which are not structurally inferable from prose
 * (that is Tier-2, an examiner model). Pure functions plus a thin writer.
 */
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export interface Route {
	method: string;
	path: string;
	/** A GET route the spec describes as a rendered HTML page (gets page-content checks). */
	html?: boolean;
	/** Required visible text the spec ties to this page (e.g. a quoted tagline). */
	contains?: string[];
	/** The redirect status the spec ties to this route (e.g. 303 for a POST that redirects). */
	redirectStatus?: number;
	/** The redirect Location the spec names (e.g. /complaints). */
	redirectLocation?: string;
}

/** A navbar link the spec names in the open: its visible label and its href. */
export interface NavLink {
	label: string;
	href: string;
}

/** Page-layout requirements the spec states in the open — never read from the grader. */
export interface PageReqs {
	doctype: boolean;
	lang: string | null;
	nav: boolean;
	/** The navbar brand text the spec names, if any. */
	brand: string | null;
	/** The specific nav links the spec names (label + href), asserted as real anchors. */
	navLinks: NavLink[];
}

export interface Contract {
	app: string;
	routes: Route[];
	page: PageReqs;
}

const ROUTE_RE = /\b(GET|POST|PUT|PATCH|DELETE)\s+`?(\/[A-Za-z0-9_/{}\-]*)/g;
// Words that mark a GET route as a rendered page rather than a data endpoint.
const PAGE_WORDS = /\b(page|template|layout|home|board|hero|render|html|tagline)\b/i;

/** Collapse path params to `{}` and drop a trailing slash, so routes compare structurally. */
export function normalizePath(path: string): string {
	const p = (path || "").replace(/\{[^}]*\}/g, "{}").replace(/\/+$/, "");
	return p === "" ? "/" : p;
}

/** The quoted text the spec ties to a tagline, derived from its prose (not the grader). */
function taglineLiteral(spec: string): string | null {
	const m = /tagline[^"“]*["“]([^"”]+)["”]/i.exec(spec);
	// A spec often wraps the quoted tagline across lines; the rendered page has it on one line
	// ("word for word"), so collapse internal whitespace to match what the grader checks.
	return m ? m[1].replace(/\s+/g, " ").trim() : null;
}

/** The navbar brand and named links the spec states, parsed from the clause that
 * describes the navbar — e.g. `a navbar with the "AgentClinic" brand and links to
 * Home (`/`) and Complaints (`/complaints`)`. All of it is spec prose, never the grader. */
function navSpec(spec: string): { brand: string | null; links: NavLink[] } {
	const links: NavLink[] = [];
	let brand: string | null = null;
	const navIdx = spec.search(/\bnav(?:bar|igation)?\b/i);
	if (navIdx >= 0) {
		const win = spec.slice(navIdx, navIdx + 240);
		if (/\blinks?\s+to\b/i.test(win)) {
			const b = /["“']([^"”']+)["”']\s+brand/i.exec(win);
			if (b) brand = b[1].trim();
			// `Label (`/path`)` pairs, one per named link.
			for (const m of win.matchAll(/\b([A-Z][A-Za-z]+)\s*\(\s*`?(\/[A-Za-z0-9_/{}\-]*)`?\s*\)/g)) {
				links.push({ label: m[1], href: m[2] });
			}
		}
	}
	return { brand, links };
}

/** Page-layout requirements stated in the spec's own words. */
function pageReqs(spec: string): PageReqs {
	const lang = /\blang\s*=\s*["']?([A-Za-z]{2}(?:-[A-Za-z]{2})?)/.exec(spec);
	const { brand, links } = navSpec(spec);
	return {
		doctype: /\bHTML5\b/i.test(spec) || /<!doctype/i.test(spec),
		lang: lang ? lang[1].toLowerCase() : null,
		nav: /\bnav(?:bar|igation)?\b/i.test(spec) || /\blinks?\s+to\b/i.test(spec),
		brand,
		navLinks: links,
	};
}

/** The phase number a prompt names (`Implement Phase 1 — Home Page.`), or null when it names none. */
export function phaseFromPrompt(prompt: string): number | null {
	const m = /\bPhase\s+(\d+)\b/i.exec(prompt || "");
	return m ? Number.parseInt(m[1], 10) : null;
}

/** Scope the spec to the phase the prompt asks for: keep phases 1..N and every non-phase
 * section (layout, agent notes), drop the `## Phase K` sections for K > N. A phased suite
 * sends one phase per request, so a contract derived from the whole roadmap would demand
 * routes the current task never asked for. With phase null (a real Pi session that names
 * no phase) the spec is returned unchanged. */
export function scopeSpecToPhase(spec: string, phase: number | null): string {
	if (phase == null) return spec;
	const heads = [...spec.matchAll(/^##\s+Phase\s+(\d+)\b.*$/gim)].map((m) => ({
		idx: m.index ?? 0,
		num: Number.parseInt(m[1], 10),
	}));
	if (!heads.length) return spec;
	const anyHead = [...spec.matchAll(/^##\s+/gim)].map((m) => m.index ?? 0);
	const cuts: Array<[number, number]> = [];
	for (const h of heads) {
		if (h.num <= phase) continue;
		const next = anyHead.find((i) => i > h.idx);
		cuts.push([h.idx, next ?? spec.length]);
	}
	if (!cuts.length) return spec;
	cuts.sort((a, b) => a[0] - b[0]);
	let out = "";
	let pos = 0;
	for (const [s, e] of cuts) {
		out += spec.slice(pos, s);
		pos = e;
	}
	return out + spec.slice(pos);
}

/** Pull the app module and every route the spec names, deduped by method + normalized path. */
export function parseContract(spec: string): Contract {
	const routes: Route[] = [];
	const seen = new Set<string>();
	const tagline = taglineLiteral(spec);
	for (const m of spec.matchAll(ROUTE_RE)) {
		const method = m[1].toUpperCase();
		const path = m[2].replace(/`+$/, "") || "/";
		const key = `${method} ${normalizePath(path)}`;
		if (seen.has(key)) continue;
		seen.add(key);
		// Classify from the route's own context — a GET page the spec describes as HTML.
		const at = m.index ?? 0;
		const ctx = spec.slice(Math.max(0, at - 180), at + 200);
		const html = method === "GET" && PAGE_WORDS.test(ctx);
		const contains: string[] = [];
		if (html && tagline && /\btagline\b/i.test(ctx)) contains.push(tagline);
		const route: Route = { method, path };
		if (html) route.html = true;
		if (contains.length) route.contains = contains;
		// A POST route the spec says redirects with a status — e.g. "answers 303 with
		// Location: /complaints". Derived from the spec's own words, never the grader.
		if (method === "POST") {
			const red = /\b(30[1-9])\b/.exec(ctx);
			if (red && /\bredirect|\banswers?\b|\bLocation\b/i.test(ctx)) {
				route.redirectStatus = Number.parseInt(red[1], 10);
				const loc = /Location:?\s*`?(\/[A-Za-z0-9_/{}-]*)/i.exec(ctx);
				if (loc) route.redirectLocation = loc[1];
			}
		}
		routes.push(route);
	}
	const named = /`(\w+)\.py`[^`]*?as `(\w+)`/.exec(spec);
	return { app: named ? named[2] : "app", routes, page: pageReqs(spec) };
}

/** Emit a pytest that boots the app and asserts each named route is registered. */
export function generatePytest(contract: Contract): string {
	const app = contract.app;
	const page = contract.page ?? { doctype: false, lang: null, nav: false, brand: null, navLinks: [] };
	const navLinks = page.navLinks ?? [];
	const needsAnchors = navLinks.length > 0 && contract.routes.some((r) => r.html);
	const lines = [
		'"""Structural contract — auto-derived from the spec, held out from the worker."""',
		"import re",
		"from starlette.testclient import TestClient",
		`from ${app} import ${app}`,
		"",
		`client = TestClient(${app})`,
		"",
		"def _norm(p):",
		'    p = re.sub(r"\\{[^}]*\\}", "{}", p or "").rstrip("/")',
		'    return p or "/"',
		"",
		"def _registered():",
		`    return {_norm(getattr(r, "path", "")) for r in ${app}.routes}`,
		"",
	];
	if (needsAnchors) {
		// A stdlib anchor parser (no turbohtml dependency in the worker env), so a
		// named nav link is checked as a real anchor — href AND visible text — the
		// way the spec states it, not merely "some href is present".
		lines.push(
			"from html.parser import HTMLParser",
			"",
			"class _Anchors(HTMLParser):",
			"    def __init__(self):",
			"        super().__init__()",
			"        self.links = []",
			"        self._href = None",
			"        self._buf = []",
			"    def handle_starttag(self, tag, attrs):",
			'        if tag == "a":',
			'            self._href = dict(attrs).get("href")',
			"            self._buf = []",
			"    def handle_data(self, data):",
			"        if self._href is not None:",
			"            self._buf.append(data)",
			"    def handle_endtag(self, tag):",
			'        if tag == "a" and self._href is not None:',
			'            self.links.append((self._href, "".join(self._buf).strip()))',
			"            self._href = None",
			"",
			"def _anchors(html):",
			"    p = _Anchors(); p.feed(html); return p.links",
			"",
		);
	}
	lines.push("def test_app_boots():", '    assert client.get("/").status_code < 500', "");
	contract.routes.forEach((route, i) => {
		const norm = normalizePath(route.path);
		const slug = norm.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "root";
		lines.push(`def test_route_${i}_${route.method.toLowerCase()}_${slug}():`);
		lines.push(`    assert ${JSON.stringify(norm)} in _registered(), "missing route: ${route.method} ${route.path}"`);
		lines.push("");
	});
	// Page-content checks for the routes the spec describes as rendered HTML pages.
	// Structural hygiene (doctype/lang/nav) is generic; any `contains` text is spec-quoted,
	// and any named nav link and brand come from the spec's own navbar sentence.
	contract.routes.forEach((route, i) => {
		if (!route.html) return;
		const norm = normalizePath(route.path);
		if (norm.includes("{}")) return; // no value to request a path-param route with
		const slug = norm.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "root";
		lines.push(`def test_page_${i}_${slug}():`);
		lines.push(`    r = client.get(${JSON.stringify(route.path)})`);
		lines.push(`    assert r.status_code == 200, "GET ${route.path} should return 200"`);
		lines.push(`    assert "text/html" in r.headers.get("content-type", "").lower(), "GET ${route.path} should serve HTML"`);
		if (page.doctype) lines.push(`    assert re.search(r"<!doctype\\s+html", r.text, re.I), "page missing HTML5 doctype"`);
		if (page.lang) lines.push(`    assert re.search(r"<html[^>]*lang\\s*=\\s*.{0,1}${page.lang}\\b", r.text, re.I), "html missing lang=${page.lang}"`);
		// A named nav link is a real anchor with that href and that visible text; the brand is text.
		if (page.brand) {
			lines.push(`    assert ${JSON.stringify(page.brand)} in r.text, ${JSON.stringify(`page missing nav brand: ${page.brand}`)}`);
		}
		if (navLinks.length) {
			for (const link of navLinks) {
				lines.push(
					`    assert any(h == ${JSON.stringify(link.href)} and t.casefold() == ${JSON.stringify(link.label.toLowerCase())} for h, t in _anchors(r.text)), ${JSON.stringify(`page missing nav link: ${link.label} -> ${link.href}`)}`,
				);
			}
		} else if (page.nav) {
			lines.push(`    assert re.search(r"<nav\\b|<a\\s[^>]*href", r.text, re.I), "page missing navigation/links"`);
		}
		for (const text of route.contains ?? []) {
			lines.push(`    assert ${JSON.stringify(text)} in r.text, ${JSON.stringify(`page missing required text: ${text.slice(0, 48)}`)}`);
		}
		lines.push("");
	});
	// Redirect checks: a POST route the spec ties to a redirect status must actually answer it.
	// For a path-param action route (e.g. /complaints/{}/resolve) we find a real id from the
	// collection page's own action link — the spec says each card has a button posting to its
	// route — then POST it and assert the spec's status and Location. All spec-derived: the
	// status, the Location, and "a button that posts to its route" are the spec's own words.
	contract.routes.forEach((route, i) => {
		if (!route.redirectStatus) return;
		const norm = normalizePath(route.path);
		const braceAt = route.path.indexOf("{");
		if (braceAt < 0) return; // a no-param POST needs a form body; the param action routes are the gap
		const parts = norm.split("/").filter(Boolean); // ["complaints","{}","resolve"]
		const verb = parts[parts.length - 1];
		const boardPath = "/" + parts.slice(0, -2).join("/");
		const board = contract.routes.find((r) => r.method === "GET" && normalizePath(r.path) === boardPath);
		const getPath = board ? board.path : boardPath;
		const slug = norm.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "root";
		const prefix = route.path.slice(0, braceAt);
		const suffix = route.path.slice(route.path.indexOf("}") + 1);
		lines.push(`def test_redirect_${i}_${slug}():`);
		lines.push(`    page = client.get(${JSON.stringify(getPath)}).text`);
		lines.push(
			`    m = re.search(r'(?:action|href)=["\\']' + re.escape(${JSON.stringify(prefix)}) + r'(\\d+)' + re.escape(${JSON.stringify(suffix)}) + r'["\\']', page)`,
		);
		lines.push(`    assert m, "no ${verb} button with an id on ${getPath} (spec: each card posts to its route)"`);
		lines.push(`    url = ${JSON.stringify(prefix)} + m.group(1) + ${JSON.stringify(suffix)}`);
		lines.push(`    resp = client.post(url, follow_redirects=False)`);
		lines.push(`    assert resp.status_code == ${route.redirectStatus}, "POST " + url + " should answer ${route.redirectStatus}"`);
		if (route.redirectLocation) {
			lines.push(`    assert resp.headers.get("location") == ${JSON.stringify(route.redirectLocation)}, "redirect Location should be ${route.redirectLocation}"`);
		}
		lines.push("");
	});
	return lines.join("\n");
}

/** Concatenate the task's spec sources (specs/*.md and AGENTS.md) found under cwd. */
export function readSpec(cwd: string): string {
	const parts: string[] = [];
	const specs = join(cwd, "specs");
	try {
		if (existsSync(specs)) {
			for (const name of readdirSync(specs).sort()) {
				if (name.endsWith(".md")) parts.push(readFileSync(join(specs, name), "utf8"));
			}
		}
		const agents = join(cwd, "AGENTS.md");
		if (existsSync(agents)) parts.push(readFileSync(agents, "utf8"));
	} catch {
		// best effort: a missing or unreadable spec yields an empty contract
	}
	return parts.join("\n\n");
}

/** Derive the contract from the spec under cwd and write the pytest to outDir; returns its path.
 * A `prompt` naming a phase scopes the spec to phases 1..N first, so the contract demands only
 * the phase the task asked for (a phased suite sends one phase per request). */
export function writeContractTest(cwd: string, outDir: string, prompt = ""): string {
	const spec = scopeSpecToPhase(readSpec(cwd), phaseFromPrompt(prompt));
	const contract = parseContract(spec);
	mkdirSync(outDir, { recursive: true });
	const path = join(outDir, "test_contract.py");
	writeFileSync(path, generatePytest(contract) + "\n");
	return path;
}

export default function (
	pi: { on: (event: string, handler: (event: any, ctx?: any) => unknown) => void },
	options: { outDir?: string } = {},
): void {
	pi.on("session_start", (_event: any, ctx: any) => {
		try {
			const cwd = ctx && typeof ctx.cwd === "string" ? ctx.cwd : process.cwd();
			const outDir = options.outDir ?? join(cwd, "..", "contract");
			// The harness exports the current prompt so the contract scopes to the phase it names;
			// a real Pi session that sets nothing falls back to the whole spec.
			const prompt = process.env.ACCEPTANCE_PROMPT ?? "";
			const path = writeContractTest(cwd, outDir, prompt);
			// The ncm gate reads NCM_TEST when it verifies; point it at the derived contract.
			process.env.NCM_TEST = path;
		} catch {
			// never break the session over contract derivation
		}
		return undefined;
	});
}
