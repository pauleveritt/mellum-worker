"""Mediated acceptance test for the medium suite (phases 1-4), written from the
full spec (prompts 01-04), not from the grader. A superset of the hidden oracle:
it pins the same contracts and adds the ones the oracle leaves thin - most of all
the Phase-4 invariant that the complaint id is an automatic default ON the
dataclass, shared by every construction path. Placed outside the workspace and
run by the verify gate (VERIFY_TEST) with PYTHONPATH=cwd.

Pages are read as a document tree, not as a string: a label hidden from the
reader, a brand inside a comment, a control outside its form or a disabled
button is not on show. Qualified against the medium witness builds (valid and
defect) from the 2026-11-09 F.7 matrix; see the 2026-11-13 research note.

Robust to shared module state: every mutating check reads the state before its
change and asserts the delta, never an absolute total, and never assumes a seed
sits at a particular id. SEED is captured at import, before any test runs."""
import dataclasses
import re
from datetime import datetime
from html.parser import HTMLParser

from starlette.testclient import TestClient

import models
from app import app

client = TestClient(app, follow_redirects=False)
SEED = list(models.complaints)
SEED_IDS = [c.id for c in SEED]


# ---- A small document tree (stdlib only) -----------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP = {"script", "style", "template", "head", "title"}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def walk(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def classes(self):
        return (self.attrs.get("class") or "").split()


class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.stack = [self.root]
        self.decls = []
        self.feed(html)
        self.close()

    def handle_decl(self, decl):
        self.decls.append(decl)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def find(self, pred):
        return [n for n in self.root.walk() if pred(n)]


def _hidden_self(node):
    style = re.sub(r"\s", "", (node.attrs.get("style") or "").lower())
    return ("hidden" in node.attrs or node.attrs.get("aria-hidden") == "true"
            or "display:none" in style or "visibility:hidden" in style
            or (node.tag == "input" and (node.attrs.get("type") or "").lower() == "hidden"))


def shown(node):
    """On show to the reader: neither it nor an ancestor is hidden."""
    return not _hidden_self(node) and not any(_hidden_self(a) for a in node.ancestors())


def text(node):
    """The text a reader sees: comments, scripts and hidden elements excluded."""
    out = []

    def go(n):
        for child in n.children:
            if isinstance(child, str):
                out.append(child)
            elif child.tag not in SKIP and not _hidden_self(child):
                go(child)
    if shown(node):
        go(node)
    return " ".join("".join(out).split())


def disabled(node):
    return "disabled" in node.attrs or any(a.tag == "fieldset" and "disabled" in a.attrs for a in node.ancestors())


def page(path):
    r = client.get(path)
    assert r.status_code == 200, f"GET {path} -> {r.status_code}"
    return Tree(r.text)


def form_of(tree, control):
    """The form a control belongs to: its form= attribute, else the enclosing form."""
    owner = control.attrs.get("form")
    if owner:
        return next((f for f in tree.find(lambda n: n.tag == "form") if f.attrs.get("id") == owner), None)
    return next((a for a in control.ancestors() if a.tag == "form"), None)


def submits(tree, form):
    """Enabled, visible submit controls of a form, with the text each shows."""
    out = []
    for n in tree.find(lambda n: n.tag in ("button", "input")):
        kind = (n.attrs.get("type") or ("submit" if n.tag == "button" else "text")).lower()
        if kind == "submit" and form_of(tree, n) is form and shown(n) and not disabled(n):
            out.append(text(n) if n.tag == "button" else (n.attrs.get("value") or ""))
    return out


def posts_to(form, path):
    return (form.attrs.get("method") or "get").lower() == "post" and form.attrs.get("action") == path


def cards(tree):
    """Each visible Bootstrap card (class token `card`), in document order."""
    return [n for n in tree.find(lambda n: "card" in n.classes()) if shown(n)]


def card_for(tree, complaint):
    found = [c for c in cards(tree) if complaint.text in text(c)]
    assert len(found) == 1, f"one card shows {complaint.text!r}, found {len(found)}"
    return found[0]


def date_forms(t):
    """Common written forms of a date showing year, month and day."""
    out = set()
    for m in {f"{t.month:02d}", str(t.month)}:
        for d in {f"{t.day:02d}", str(t.day)}:
            y = t.year
            out |= {f"{y}-{m}-{d}", f"{y}/{m}/{d}", f"{y}.{m}.{d}", f"{d}/{m}/{y}", f"{m}/{d}/{y}",
                    f"{d}-{m}-{y}", f"{d}.{m}.{y}"}
    for month in {t.strftime("%B"), t.strftime("%b")}:
        for d in {f"{t.day:02d}", str(t.day)}:
            out |= {f"{month} {d}, {t.year}", f"{month} {d} {t.year}", f"{d} {month} {t.year}", f"{d} {month}, {t.year}"}
    return out


def board_order(tree):
    """The complaints the board shows, as model ids, in the order shown."""
    shown_cards = cards(tree)
    order = []
    for c in models.complaints:
        idx = [i for i, card in enumerate(shown_cards) if c.text in text(card)]
        assert len(idx) == 1, f"one card shows {c.text!r}"
        order.append((idx[0], c.id))
    return [cid for _, cid in sorted(order)]


def _tags(nodes, limit=6):
    """What the page actually held, for a failure message: each tag as parsed, kept short."""
    out = []
    for n in nodes[:limit]:
        attrs = " ".join(f"{k}={v!r}" if v is not None else k for k, v in n.attrs.items())
        tag = f"<{n.tag} {attrs}>" if attrs else f"<{n.tag}>"
        out.append(tag if len(tag) <= 300 else tag[:300] + "...>")
    more = f" (+{len(nodes) - limit} more)" if len(nodes) > limit else ""
    return (", ".join(out) or "none") + more


def _card_actions(tree, complaint):
    """The forms a card offers, as (action, [submit labels]), for a failure message."""
    card = card_for(tree, complaint)
    return [(f.attrs.get("action"), submits(tree, f)) for f in card.walk() if f.tag == "form"]


# ---- Phase 1: home page + base layout -------------------------------------
def _assert_base_layout(tree):
    found = any(d.strip().lower() == "doctype html" for d in tree.decls)
    assert found, f"HTML5 doctype, got {tree.decls}"
    html = tree.find(lambda n: n.tag == "html")
    assert html and html[0].attrs.get("lang") == "en", f'<html lang="en">, got {_tags(html)}'
    metas = tree.find(lambda n: n.tag == "meta")
    found = any("charset" in m.attrs or "charset" in (m.attrs.get("content") or "").lower() for m in metas)
    assert found, f"a charset meta; the <meta> tags parsed: {_tags(metas)}"
    found = any((m.attrs.get("name") or "").lower() == "viewport" for m in metas)
    assert found, f"a viewport meta; the <meta> tags parsed: {_tags(metas)}"
    links = tree.find(lambda n: n.tag == "link")
    found = any("stylesheet" in (l.attrs.get("rel") or "").lower() and "bootstrap" in (l.attrs.get("href") or "").lower() for l in links)
    assert found, f"Bootstrap 5 CSS: a stylesheet link to Bootstrap; the <link> tags parsed: {_tags(links)}"
    found = any("icon" in (l.attrs.get("rel") or "").lower().split() and l.attrs.get("href") == "https://www.python.org/static/favicon.ico" for l in links)
    assert found, f"the favicon link; the <link> tags parsed: {_tags(links)}"
    scripts = tree.find(lambda n: n.tag == "script")
    found = any("bootstrap" in (s.attrs.get("src") or "").lower() and "bundle" in (s.attrs.get("src") or "").lower() for s in scripts)
    assert found, f"the Bootstrap JS bundle; the <script> tags parsed: {_tags(scripts)}"
    navs = [n for n in tree.find(lambda n: n.tag == "nav") if shown(n)]
    assert navs, "a visible navbar"
    nav_links = {(a.attrs.get("href"), text(a)) for nav in navs for a in nav.walk() if a.tag == "a" and shown(a)}
    found = any(t == "AgentClinic" for _, t in nav_links)
    assert found, f"the AgentClinic brand on show in the navbar; visible nav links (href, text): {sorted(nav_links, key=str)}"
    hrefs = {h for h, t in nav_links if t}
    assert "/" in hrefs and "/complaints" in hrefs, f"navbar links to / and /complaints, got {hrefs}"


def test_home_renders_the_tagline_and_base_layout():
    r = client.get("/")
    assert r.status_code == 200
    tree = Tree(r.text)
    assert "Come in. Sit down. Tell us about your human." in text(tree.root)
    titles = tree.find(lambda n: n.tag == "title")
    assert titles and "AgentClinic" in "".join(c for c in titles[0].children if isinstance(c, str))
    _assert_base_layout(tree)


# ---- Phase 2: complaints board -------------------------------------------
def test_seed_complaints_include_the_exact_scope_creep_text():
    assert 3 <= len(SEED) <= 5
    assert "Scope creep never ends." in [c.text for c in SEED]
    assert len(set(SEED_IDS)) == len(SEED_IDS)


def test_board_lists_seed_complaints_with_name_date_and_text():
    tree = page("/complaints")
    assert "Complaints Board" in text(tree.root)
    _assert_base_layout(tree)
    for c in SEED:
        body = text(card_for(tree, c))
        assert c.agent_name in body
        assert any(f in body for f in date_forms(c.timestamp)), f"a date with year, month and day in {body!r}"


def test_complaint_dataclass_carries_the_spec_fields():
    assert dataclasses.is_dataclass(models.Complaint)
    names = [f.name for f in dataclasses.fields(models.Complaint)]
    assert names[:3] == ["agent_name", "text", "timestamp"]
    a = models.Complaint("tester", "a gripe")
    b = models.Complaint("tester", "another gripe")
    assert a.agent_name == "tester" and a.text == "a gripe"
    assert isinstance(a.timestamp, datetime) and a.timestamp is not b.timestamp
    assert a.timestamp.utcoffset() is not None and a.timestamp.utcoffset().total_seconds() == 0, "a UTC timestamp"


# ---- Phase 3: add complaint ----------------------------------------------
def _add(name, gripe):
    before = {c.id: (c.agent_name, c.text) for c in models.complaints}
    r = client.post("/complaints", data={"agent_name": name, "text": gripe})
    assert r.status_code == 303
    assert r.headers["location"] == "/complaints"
    after = {c.id: (c.agent_name, c.text) for c in models.complaints}
    assert len(models.complaints) == len(before) + 1, "the new complaint is appended, nothing removed"
    assert all(after.get(k) == v for k, v in before.items()), "existing complaints keep their ids"
    new = [c for c in models.complaints if c.text == gripe]
    assert len(new) == 1 and new[0].agent_name == name and models.complaints[-1] is new[0]
    return new[0]


def test_add_complaint_redirects_303_to_the_board_and_appears():
    added = [_add(f"Zed {i}", f"a brand new gripe number {i}") for i in range(3)]
    tree = page("/complaints")
    for c in added:
        assert c.agent_name in text(card_for(tree, c))


def test_add_form_posts_to_complaints_with_the_named_fields():
    tree = page("/complaints")
    forms = [f for f in tree.find(lambda n: n.tag == "form") if posts_to(f, "/complaints") and shown(f)]
    assert forms, "a visible form posting to /complaints"

    def usable(name, tags):
        for n in tree.find(lambda n: n.tag in tags and n.attrs.get("name") == name):
            kind = (n.attrs.get("type") or "text").lower()
            if form_of(tree, n) in forms and shown(n) and not disabled(n) and kind != "hidden":
                return form_of(tree, n)
        return None
    owner = usable("agent_name", ("input",))
    assert owner is not None, "a usable agent_name input inside the form"
    assert usable("text", ("textarea",)) is owner, "a usable textarea named text in the same form"
    assert submits(tree, owner), "the form has a submit button"


# ---- Phase 4: resolve / reopen (the deep contract) ------------------------
def test_new_complaints_default_open_with_distinct_auto_ids():
    # The id is an AUTOMATIC default on the dataclass, so a direct construction
    # gets one too, and the add route uses the same sequence (never a second
    # counter, never recomputed from the list).
    names = [f.name for f in dataclasses.fields(models.Complaint)]
    assert names.index("id") > names.index("timestamp") and "status" in names
    a = models.Complaint("x", "first direct")
    routed = _add("Route", "created through the add route")
    b = models.Complaint("x", "second direct")
    ids = [max(SEED_IDS), a.id, routed.id, b.id]
    assert all(type(i) is int for i in ids), ids
    assert ids == sorted(set(ids)), f"one increasing id sequence across direct and route creation: {ids}"
    assert a.status == b.status == routed.status == "open"
    assert [c.id for c in SEED] == SEED_IDS, "seed ids never change"


def _status_shown(tree, complaint):
    """The status word a card shows: exactly one of Open / Resolved, not negated."""
    body = text(card_for(tree, complaint))
    found = re.findall(r"(?<![\w-])(Open|Resolved)(?![\w-])", body)
    assert not re.search(r"\bnot\s+(open|resolved)\b", body, re.I), f"a negated status in {body!r}"
    assert len(found) == 1, f"one status badge reading Open or Resolved, got {found} in {body!r}"
    return found[0]


def _action(tree, complaint, verb):
    card = card_for(tree, complaint)
    path = f"/complaints/{complaint.id}/{verb}"
    forms = [f for f in card.walk() if f.tag == "form" and posts_to(f, path)]
    forms += [f for f in tree.find(lambda n: n.tag == "form" and posts_to(n, path)) if f not in forms]
    return any(verb.capitalize() in s for f in forms for s in submits(tree, f))


def _post(path):
    r = client.post(path)
    assert r.status_code == 303 and r.headers["location"] == "/complaints", f"POST {path} -> {r.status_code}"


def test_resolve_then_reopen_sets_status_303_and_keeps_order():
    target = models.complaints[0]
    others = {c.id: c.status for c in models.complaints if c is not target}
    ids_before = [c.id for c in models.complaints]
    shown_before = board_order(page("/complaints"))

    _post(f"/complaints/{target.id}/resolve")
    assert target.status == "resolved"
    assert {c.id: c.status for c in models.complaints if c is not target} == others, "only that complaint changes"
    assert [c.id for c in models.complaints] == ids_before, "resolving does not move it"
    tree = page("/complaints")
    assert board_order(tree) == shown_before
    assert _status_shown(tree, target) == "Resolved"
    offers = _action(tree, target, "reopen") and not _action(tree, target, "resolve")
    assert offers, (
        f"a resolved card offers Reopen and not Resolve; its forms (action, buttons): {_card_actions(tree, target)}")

    _post(f"/complaints/{target.id}/reopen")
    assert target.status == "open"
    assert [c.id for c in models.complaints] == ids_before, "reopening does not move it"
    tree = page("/complaints")
    assert board_order(tree) == shown_before
    assert _status_shown(tree, target) == "Open"


def test_board_shows_status_badge_and_the_action_forms():
    tree = page("/complaints")
    assert board_order(tree) == [c.id for c in models.complaints], "the board shows complaints in list order"
    for c in models.complaints:
        assert c.status == "open"
        assert _status_shown(tree, c) == "Open"
        offers = _action(tree, c, "resolve") and not _action(tree, c, "reopen")
        assert offers, (
            f"an open card offers Resolve and not Reopen; its forms (action, buttons): {_card_actions(tree, c)}")
