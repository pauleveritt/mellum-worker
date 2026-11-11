"""
Drop-in compatibility shims for moving an existing codebase onto turbohtml.

Each submodule mirrors the public API of the library it replaces, so a migration is an import
swap rather than a rewrite: :mod:`turbohtml.migration.bleach` for ``bleach``,
:mod:`turbohtml.migration.markupsafe` for ``markupsafe``, and :mod:`turbohtml.migration.stdlib`
for the standard library's :class:`html.parser.HTMLParser`.
"""

from __future__ import annotations
