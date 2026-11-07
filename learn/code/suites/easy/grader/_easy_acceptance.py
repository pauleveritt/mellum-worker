"""Small HTML helpers for Easy's additional written Phase 1 acceptance."""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlsplit


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    parent: "Element | None" = None
    children: list = field(default_factory=list)

    def elements(self, tag=None):
        for child in self.children:
            if isinstance(child, Element):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.elements(tag)

    def text(self):
        if not self.visible():
            return ""
        return " ".join("".join(child.text() if isinstance(child, Element) else child for child in self.children).split())

    def visible(self):
        if self.tag in {"script", "style", "template"} or "hidden" in self.attrs:
            return False
        style = re.sub(r"\s+", "", self.attrs.get("style") or "").casefold()
        if "display:none" in style or "visibility:hidden" in style:
            return False
        return self.parent is None or self.parent.visible()

    def within(self, tag):
        return self.tag == tag or self.parent is not None and self.parent.within(tag)


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.current = self.root
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        element = Element(tag, dict(attrs), self.current)
        self.current.children.append(element)
        if tag not in self.VOID:
            self.current = element

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        element = self.current
        while element.parent is not None:
            if element.tag == tag:
                self.current = element.parent
                return
            element = element.parent

    def handle_data(self, data):
        self.current.children.append(data)

    def all(self, tag):
        return list(self.root.elements(tag))


def bootstrap5_url(value, *, bundle=False):
    parsed = urlsplit(value or "")
    if parsed.scheme not in {"", "http", "https"} or not parsed.hostname:
        return False
    if parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return False
    path = parsed.path.casefold()
    version5 = re.search(r"bootstrap(?:[/@-])v?5(?:[./-]|$)", path)
    asset = r"bootstrap\.bundle(?:\.min)?\.js$" if bundle else r"bootstrap(?:\.min)?\.css$"
    return bool(version5 and re.search(asset, path))


def title(html):
    titles = Document(html).all("title")
    assert len(titles) == 1, "A document must have one title"
    return titles[0].text()
