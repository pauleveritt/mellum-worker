"""Page and HTML form semantics; importing this never requires models.py."""

from datetime import datetime
import re

from starlette.testclient import TestClient
from turbohtml import Doctype, Element, Text

from app import app

client = TestClient(app)
client.__enter__()  # run FastAPI lifespan/startup before any seed snapshot

TAGLINE = "Come in. Sit down. Tell us about your human."
SEED_COMPLAINT = "Scope creep never ends."


def _is_visible(element) -> bool:
    for node in [element, *element.ancestors]:
        if not isinstance(node, Element):
            continue
        style = re.sub(r"\s+", "", node.attr("style") or "").casefold()
        if (
            node.tag in {"script", "style", "template", "head"}
            or "hidden" in node.attrs
            or "display:none" in style
            or "visibility:hidden" in style
        ):
            return False
    return True


def _visible_text(node) -> str:
    if isinstance(node, Text):
        return node.text
    if isinstance(node, Element) and not _is_visible(node):
        return ""
    text = "".join(_visible_text(child) for child in node.children)
    if isinstance(node, Element) and node.tag in {
        "br", "div", "p", "nav", "main", "section", "article", "header", "footer",
        "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "form", "fieldset",
        "table", "tr", "td", "th", "blockquote", "pre", "hr",
    }:
        return f" {text} "
    return text


def _normalized_text(element) -> str:
    return " ".join(_visible_text(element).split())


def _has_html5_doctype(document) -> bool:
    nodes = [node for node in document.children if not isinstance(node, Text) or node.text.strip()]
    return bool(nodes) and (
        isinstance(nodes[0], Doctype)
        and nodes[0].name.casefold() == "html"
        and not nodes[0].public_id
        and nodes[0].system_id in {None, "", "about:legacy-compat"}
    )


def _assert_navigation(document) -> None:
    assert any(
        _is_visible(nav)
        and "AgentClinic" in _normalized_text(nav)
        and any(link.attr("href") == "/" and _normalized_text(link).casefold() == "home"
                for link in nav.select("a"))
        and any(link.attr("href") == "/complaints"
                and _normalized_text(link).casefold() == "complaints"
                for link in nav.select("a"))
        for nav in document.select('nav, [role="navigation"], .navbar')
    ), "a visible navbar must contain the brand and both navigation links"


def _enabled(control) -> bool:
    if not _is_visible(control) or "disabled" in control.attrs:
        return False
    for ancestor in control.ancestors:
        if isinstance(ancestor, Element) and ancestor.tag == "fieldset" and "disabled" in ancestor.attrs:
            legends = [child for child in ancestor.children if isinstance(child, Element) and child.tag == "legend"]
            if not legends or legends[0] not in control.ancestors:
                return False
    return True


def _associated_controls(document, form) -> list:
    controls = []
    for control in document.select("input, textarea, button, select"):
        form_id = control.attr("form")
        if form_id is not None:
            associated = bool(form.attr("id")) and form_id == form.attr("id")
        else:
            owner = next((node for node in control.ancestors
                          if isinstance(node, Element) and node.tag == "form"), None)
            associated = owner == form
        if associated and _enabled(control):
            controls.append(control)
    return controls


def _post_forms(document, action: str) -> list:
    """Return usable POST forms and controls, including explicit HTML form owners."""
    result = []
    for form in document.select("form"):
        controls = _associated_controls(document, form)
        submits = []
        for control in controls:
            kind = (control.attr("type") or ("submit" if control.tag == "button" else "text")).casefold()
            if control.tag not in {"input", "button"} or kind != "submit":
                continue
            method = control.attr("formmethod") or form.attr("method") or "get"
            destination = control.attr("formaction") or form.attr("action") or "/complaints"
            if method.casefold() == "post" and destination == action:
                submits.append(control)
        if submits:
            result.append((form, controls, submits))
    return result


def _has_displayed_date(text: str, expected) -> bool:
    """Recognize dates, rather than unrelated year/month/day substring tokens."""
    text = re.sub(r"(\d)(?:st|nd|rd|th)\b", r"\1", text, flags=re.I)
    text = text.replace(",", " ")
    patterns = [
        (r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b", ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]),
        (r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b", ["%d-%m-%Y", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%m.%d.%Y"]),
        (r"\b[A-Za-z]+\s+\d{1,2}\s+\d{4}\b", ["%B %d %Y", "%b %d %Y"]),
        (r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", ["%d %B %Y", "%d %b %Y"]),
        (r"\b\d{4}\s+[A-Za-z]+\s+\d{1,2}\b", ["%Y %B %d", "%Y %b %d"]),
    ]
    for pattern, formats in patterns:
        for candidate in re.findall(pattern, text):
            for format_ in formats:
                try:
                    parsed = datetime.strptime(" ".join(candidate.split()), format_).date()
                except ValueError:
                    continue
                if parsed == expected.date():
                    return True
    return False
