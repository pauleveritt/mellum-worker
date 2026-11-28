import assert from "node:assert/strict";
import test from "node:test";

import { generatePytest, normalizePath, parseContract, phaseFromPrompt, scopeSpecToPhase } from "../extensions/mellum-acceptance.ts";

const SPEC = `
## Phase 1 — Home Page
- Add a \`GET /\` route returning the home template.
- \`app.py\` holds the FastAPI application as \`app\`.

## Phase 3 — Add Complaint
- Add \`POST /complaints\` that appends a complaint and redirects.

## Phase 4 — Resolve and Reopen
- Add \`POST /complaints/{complaint_id}/resolve\` in app.py: redirect with status 303.
- Add \`POST /complaints/{complaint_id}/reopen\`.
`;

test("normalizePath collapses path params and trailing slashes", () => {
	assert.equal(normalizePath("/complaints/{complaint_id}/resolve"), "/complaints/{}/resolve");
	assert.equal(normalizePath("/complaints/"), "/complaints");
	assert.equal(normalizePath("/"), "/");
});

test("parseContract extracts the app module and every route the spec names", () => {
	const c = parseContract(SPEC);
	assert.equal(c.app, "app");
	const got = c.routes.map((r) => `${r.method} ${r.path}`);
	assert.ok(got.includes("GET /"), got);
	assert.ok(got.includes("POST /complaints"), got);
	assert.ok(got.includes("POST /complaints/{complaint_id}/resolve"), got);
	assert.ok(got.includes("POST /complaints/{complaint_id}/reopen"), got);
});

test("parseContract dedupes routes and defaults the app module to 'app'", () => {
	const c = parseContract("GET / and again GET / here");
	assert.equal(c.routes.length, 1);
	assert.equal(c.app, "app");
});

test("generatePytest imports the app, boots it, and checks each route is registered", () => {
	const py = generatePytest(parseContract(SPEC));
	assert.match(py, /from app import app/);
	assert.match(py, /TestClient\(app\)/);
	assert.match(py, /def test_app_boots\(/);
	// a check per route, param-normalized, with a helpful message
	assert.match(py, /\/complaints\/\{\}\/resolve/);
	assert.match(py, /missing route: POST \/complaints\/\{complaint_id\}\/resolve/);
	// one registration test per parsed route, plus the boot test
	const defs = [...py.matchAll(/^def test_(?:route_|app_boots)/gm)].length;
	assert.equal(defs, parseContract(SPEC).routes.length + 1, py);
});

test("generatePytest marks the file as held-out, auto-derived", () => {
	const py = generatePytest({ app: "app", routes: [], page: { doctype: false, lang: null, nav: false } });
	assert.match(py, /auto-derived|structural contract/i);
});

// --- page-HTML contract (spec-derived: structural hygiene + spec-quoted tagline) ---

const PAGE_SPEC = `
## Phase 1 — Home Page
- A shared Jinja2 layout, \`templates/base.html\`: HTML5 with \`lang="en"\`, a navbar with
  the "AgentClinic" brand and links to Home (\`/\`) and Complaints (\`/complaints\`).
- The home page at \`/\` uses that layout: a hero section with the tagline
  *"Come in. Sit down. Tell us about your human."* and a short welcoming paragraph.
- \`app.py\` holds the FastAPI application as \`app\`.
- Tests: \`GET /\` returns 200 and contains the tagline.
`;

test("parseContract reads page layout requirements from the spec's own words", () => {
	const c = parseContract(PAGE_SPEC);
	assert.equal(c.page.doctype, true, "HTML5 -> doctype");
	assert.equal(c.page.lang, "en", 'lang="en"');
	assert.equal(c.page.nav, true, "navbar/links -> nav");
});

test("parseContract classifies a GET page route as html and derives its required tagline", () => {
	const c = parseContract(PAGE_SPEC);
	const home = c.routes.find((r) => r.method === "GET" && normalizePath(r.path) === "/");
	assert.ok(home, "home route parsed");
	assert.equal(home.html, true, "GET / is an html page");
	assert.ok(
		(home.contains || []).includes("Come in. Sit down. Tell us about your human."),
		JSON.stringify(home.contains),
	);
});

test("generatePytest emits page assertions (200, doctype, lang, nav, tagline) for html routes", () => {
	const py = generatePytest(parseContract(PAGE_SPEC));
	assert.match(py, /def test_page_\d+_root\(/, py);
	assert.match(py, /status_code == 200/);
	assert.match(py, /<!doctype/i);
	assert.match(py, /lang/);
	// PAGE_SPEC names its nav links, so the nav check is the anchor-based named-link
	// assertion (stronger than the generic "<nav or some href" regex).
	assert.match(py, /_anchors\(/);
	assert.match(py, /Come in\. Sit down\. Tell us about your human\./);
});

test("generatePytest emits no page test for a non-html route", () => {
	const py = generatePytest(parseContract("Add a \`POST /complaints\` that appends a complaint."));
	assert.doesNotMatch(py, /def test_page_/);
});

// --- phase scoping: the contract must cover only the phase(s) the prompt asks for ---

const ROADMAP = `
## Layout
- \`app.py\` holds the FastAPI application as \`app\`.

## Phase 1 — Home Page
- The home page at \`GET /\` has a navbar with the "AgentClinic" brand and links to Home (\`/\`) and Complaints (\`/complaints\`).

## Phase 2 — Complaints Board
- \`GET /complaints\` shows a board.

## Phase 3 — Add Complaint
- \`POST /complaints\` appends a complaint.

## Phase 4 — Resolve and Reopen
- \`POST /complaints/{id}/resolve\` and \`POST /complaints/{id}/reopen\`.

# AgentClinic — agent notes
## Mellum
- Do not: start servers
`;

test("phaseFromPrompt reads the phase number the prompt names", () => {
	assert.equal(phaseFromPrompt("Implement Phase 1 — Home Page."), 1);
	assert.equal(phaseFromPrompt("Implement Phase 3 — Add Complaint."), 3);
	assert.equal(phaseFromPrompt("do the whole thing"), null);
});

test("scopeSpecToPhase keeps phases up to N, drops later ones, keeps non-phase sections", () => {
	const scoped = scopeSpecToPhase(ROADMAP, 1);
	assert.match(scoped, /## Phase 1 — Home Page/);
	assert.doesNotMatch(scoped, /## Phase 2/);
	assert.doesNotMatch(scoped, /## Phase 4/);
	// preamble and the agent-notes rules survive the scoping
	assert.match(scoped, /## Layout/);
	assert.match(scoped, /Do not: start servers/);
});

test("a Phase-1 scope yields only the phase-1 route, not the later-phase ones", () => {
	const c = parseContract(scopeSpecToPhase(ROADMAP, 1));
	const got = c.routes.map((r) => `${r.method} ${normalizePath(r.path)}`);
	assert.ok(got.includes("GET /"), got);
	assert.ok(!got.some((g) => g.includes("/complaints")), `no complaints routes in phase-1 scope: ${got}`);
});

test("scopeSpecToPhase returns the spec unchanged when the phase is null (real Pi session)", () => {
	assert.equal(scopeSpecToPhase(ROADMAP, null), ROADMAP);
});

// --- nav completeness: assert the spec-named links as anchors, not merely 'some href' ---

test("parseContract derives the spec-named nav links and the brand", () => {
	const c = parseContract(PAGE_SPEC);
	assert.equal(c.page.brand, "AgentClinic");
	const links = (c.page.navLinks || []).map((l) => `${l.label} ${l.href}`);
	assert.ok(links.includes("Home /"), links);
	assert.ok(links.includes("Complaints /complaints"), links);
});

test("generatePytest asserts each named nav link as an anchor with matching href and text, and the brand", () => {
	const py = generatePytest(parseContract(PAGE_SPEC));
	// a stdlib anchor parser, not a lax 'any href' regex
	assert.match(py, /html\.parser|HTMLParser/);
	// the specific named links the spec states
	assert.match(py, /\/complaints/);
	assert.match(py, /Complaints/);
	assert.match(py, /Home/);
	// the brand text
	assert.match(py, /AgentClinic/);
	// the message points at the missing named link, not a generic 'navigation/links'
	assert.match(py, /nav link|named link|href/i);
});

// --- phase-4 redirect contract: a POST route the spec ties to 303 must actually answer 303 ---

const REDIRECT_SPEC = `
## Phase 3 — Add Complaint
- The board ends with a form that posts to \`/complaints\`.
- \`POST /complaints\` appends the complaint and answers 303 with \`Location: /complaints\`.

## Phase 4 — Resolve and Reopen
- \`GET /complaints\` shows the board, one card per complaint.
- Each card shows Open or Resolved and a button that posts to its route.
- \`POST /complaints/{id}/resolve\` marks that complaint resolved and answers 303 with \`Location: /complaints\`.
- \`POST /complaints/{id}/reopen\` marks it open and answers the same way.
- \`app.py\` holds the FastAPI application as \`app\`.
`;

test("parseContract reads the redirect status and Location for a POST route the spec ties to 303", () => {
	const c = parseContract(REDIRECT_SPEC);
	const resolve = c.routes.find((r) => r.method === "POST" && normalizePath(r.path) === "/complaints/{}/resolve");
	assert.ok(resolve, "resolve route parsed");
	assert.equal(resolve.redirectStatus, 303);
	assert.equal(resolve.redirectLocation, "/complaints");
});

test("generatePytest emits a redirect check that posts a board action link and asserts the 303 + Location", () => {
	const py = generatePytest(parseContract(REDIRECT_SPEC));
	assert.match(py, /def test_redirect_\d+_/, py);
	assert.match(py, /follow_redirects=False/);
	assert.match(py, /status_code == 303/);
	assert.match(py, /resolve/);
	assert.match(py, /\\d\+/, "regex to pull the id from a board action link");
	assert.match(py, /location/i);
});

test("a tagline the spec wrapped across lines is normalized to one line in the contract", () => {
	const spec = "## Phase 1\n- The `GET /` home page has a hero and the tagline \"Come in. Sit down.\n  Tell us about your human.\" and a welcome.\n- `app.py` holds the FastAPI application as `app`.";
	const py = generatePytest(parseContract(spec));
	assert.match(py, /"Come in\. Sit down\. Tell us about your human\." in r\.text/, py);
	assert.doesNotMatch(py, /Sit down\.\\n/, "no raw newline left in the tagline literal");
});
