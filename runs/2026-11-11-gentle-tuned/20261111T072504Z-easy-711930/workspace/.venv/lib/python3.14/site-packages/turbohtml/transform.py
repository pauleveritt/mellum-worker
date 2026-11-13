"""
turbohtml.transform: XSLT 1.0 transformation, the job ``lxml.etree.XSLT`` does.

An XSLT stylesheet is itself an XML document, so it is parsed with :func:`turbohtml.parse_xml`; the source document is
any parsed tree. :class:`Transform` holds a parsed stylesheet and applies it to a source, mirroring lxml's compile-once,
apply-many shape::

    from turbohtml import parse_xml
    from turbohtml.transform import Transform

    style = parse_xml(stylesheet_source)
    convert = Transform(style)
    result = convert(parse_xml(document_source))

The whole transform runs in the C extension, reusing turbohtml's XPath 1.0 engine for every match pattern and select
expression. It covers XSLT 1.0: ``xsl:template`` (match, name, mode, priority), ``xsl:apply-templates``,
``xsl:call-template``, ``xsl:for-each``, ``xsl:if``, ``xsl:choose``, ``xsl:value-of``, ``xsl:copy``/``xsl:copy-of``,
``xsl:element``/``xsl:attribute``/``xsl:text``, ``xsl:variable``/``xsl:param``, ``xsl:sort``, multi-level
``xsl:number``, ``xsl:key`` and the ``key()`` function, ``xsl:strip-space``/``xsl:preserve-space``,
``xsl:attribute-set``, ``xsl:namespace-alias``, ``xsl:import`` with import precedence, ``xsl:fallback``, simplified
stylesheets, ``cdata-section-elements`` and the ``xml``/``html``/``text`` output methods (html is auto-selected for a
null-namespace ``html`` document element). The documented boundaries are locale-aware ``xsl:sort`` collation (a locale
layer turbohtml does not carry) and ``id()`` over DTD-declared IDs (no DTD layer).

An ``xsl:import`` is resolved relative to ``base_url`` (the stylesheet's own path or file URL): pass it when the
stylesheet imports. Validated against libxslt's XSLT 1.0 Recommendation test corpus (see
``tests/conformance/test_xslt_conformance.py``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from urllib.request import url2pathname

from ._html import _xslt_resolve_imports, _xslt_transform, parse_xml

if TYPE_CHECKING:
    from ._html import Node

__all__ = ["Transform", "transform"]


def _load_import(base: str | Path, href: str) -> tuple[Node, Path, Path]:
    current = _base_path(base).resolve() if isinstance(base, str) else base
    path = _import_path(current.parent, href).resolve()
    return parse_xml(path.read_text(encoding="utf-8")), path, current


def _resolve(stylesheet: Node, base_url: str | None) -> list[Node] | None:
    """Return the imported stylesheets a transform must merge, or None when the stylesheet imports nothing."""
    return _xslt_resolve_imports(stylesheet, base_url, _load_import)


def _base_path(base_url: str) -> Path:
    parsed = urlparse(base_url)
    if parsed.scheme == "file":
        return _file_url_path(parsed.netloc, parsed.path, "base_url")
    if parsed.scheme and not _is_windows_drive_path(base_url):
        msg = "xsl:import base_url must be a local path or file URL"
        raise ValueError(msg)
    return Path(base_url)


def _import_path(base: Path, href: str) -> Path:
    parsed = urlparse(href)
    if parsed.scheme == "file":
        return _file_url_path(parsed.netloc, parsed.path, "href")
    if parsed.scheme or parsed.netloc:
        msg = "xsl:import href must be a local path or file URL"
        raise ValueError(msg)
    return base / url2pathname(href)


def _file_url_path(netloc: str, path: str, name: str) -> Path:
    if netloc not in {"", "localhost"}:
        msg = f"xsl:import {name} file URL must point to a local path"
        raise ValueError(msg)
    return Path(url2pathname(path))


def _is_windows_drive_path(value: str) -> bool:
    return len(value) > 2 and value[1] == ":" and value[2] in "\\/"


class Transform:
    """
    A compiled XSLT 1.0 stylesheet, callable over source documents (lxml's ``etree.XSLT``).

    :param stylesheet: the stylesheet, a tree parsed with :func:`turbohtml.parse_xml`.
    :param base_url: the stylesheet's path or file URL, against which ``xsl:import`` hrefs resolve; required only when
        the stylesheet imports.
    """

    __slots__ = ("_imports", "_stylesheet")

    def __init__(self, stylesheet: Node, *, base_url: str | None = None) -> None:
        """Hold the parsed stylesheet and pre-resolve its imported stylesheets once."""
        self._stylesheet = stylesheet
        self._imports = _resolve(stylesheet, base_url)

    def __call__(self, source: Node, /, **params: str) -> str:
        """
        Transform a source document and return the serialized result.

        :param source: the document to transform, a parsed tree.
        :param params: top-level ``xsl:param`` values, each an XPath expression string (quote a string literal, as
            lxml does: ``convert(doc, title="'Report'")``).
        :raises ValueError: if the stylesheet or an expression is malformed, or a referenced key or named template is
            undeclared.
        :raises RuntimeError: on an ``xsl:message`` with ``terminate="yes"``.
        :returns: the transformed document serialized under the stylesheet's ``xsl:output`` method.
        """
        return _xslt_transform(self._stylesheet, source, params or None, self._imports)


def transform(stylesheet: Node, source: Node, /, *, base_url: str | None = None, **params: str) -> str:
    """
    Apply an XSLT 1.0 stylesheet to a source document in one call.

    Equivalent to ``Transform(stylesheet, base_url=base_url)(source, **params)``; use :class:`Transform` to apply one
    stylesheet to many documents without re-reading it each time.

    :param stylesheet: the stylesheet, a tree parsed with :func:`turbohtml.parse_xml`.
    :param source: the document to transform, a parsed tree.
    :param base_url: the stylesheet's path or file URL, against which ``xsl:import`` hrefs resolve; required only when
        the stylesheet imports.
    :param params: top-level ``xsl:param`` values, each an XPath expression string.
    :returns: the transformed document serialized under the stylesheet's ``xsl:output`` method.
    """
    return _xslt_transform(stylesheet, source, params or None, _resolve(stylesheet, base_url))
