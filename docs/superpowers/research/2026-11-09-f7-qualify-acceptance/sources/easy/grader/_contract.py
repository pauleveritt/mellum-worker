"""Shared fixtures for the phased acceptance checks.

Extracted from agentclinic-repair-depth-3/overlay/test_acceptance.py so
that phase 1 is independently collectable: that module imports `models`
at load, and collection imports before selection, so a phase-1 workspace
with no models.py fails at import for every selector.

Nothing here touches models. Assertion bodies in the sibling test modules
are copied verbatim from the source; only the module structure differs.
"""

from starlette.testclient import TestClient
from turbohtml import Doctype

from app import app

client = TestClient(app)
client.__enter__()  # run FastAPI lifespan/startup before any snapshot

TAGLINE = "Come in. Sit down. Tell us about your human."
SEED_COMPLAINT = "Scope creep never ends."


def _normalized_text(element) -> str:
    return " ".join(element.text.split())


def _has_html5_doctype(document) -> bool:
    return any(
        isinstance(node, Doctype) and node.name.casefold() == "html"
        for node in document.children
    )
