import re
from typing import Optional, cast

from agent_detector._detector import KNOWN_AGENTS, AgentName, DetectionResult

# The product token that carries the agent identity, e.g. ``AI-Agent/codex``.
# It mirrors the ``AI_AGENT`` environment variable used for explicit identities.
AGENT_MARKER = "AI-Agent"

# RFC 9110 ``token`` characters, used for the client product name and version.
_TOKEN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def parse_invoking_agent(
    user_agent: Optional[str],
    *,
    expected_product: Optional[str] = None,
) -> Optional[DetectionResult]:
    """Parse an explicit coding-agent identity from a User-Agent value.

    The value must be exactly two whitespace-separated products::

        <product>/<version> AI-Agent/<agent>

    ``product`` and ``version`` must be non-empty RFC 9110 tokens, the marker
    must be exactly ``AI-Agent``, and ``agent`` must be one of
    ``KNOWN_AGENTS``. Matching is case-sensitive. Leading and trailing
    whitespace is ignored; comments and additional products are rejected.

    Pass ``expected_product`` to ignore identities that were not sent by a
    specific client. This only filters out unrelated User-Agent values; it does
    not authenticate the caller, who can send any header they like.

    Returns a ``DetectionResult`` with ``confidence="high"`` and
    ``source="user-agent"``, or ``None`` when the value does not match.
    """

    if expected_product is not None and not expected_product:
        raise ValueError("expected_product must be a non-empty string or None")

    if not user_agent:
        return None

    parts = user_agent.split()
    if len(parts) != 2:
        return None

    client_product, agent_product = parts

    product, _, version = client_product.partition("/")
    if not _TOKEN.match(product) or not _TOKEN.match(version):
        return None

    if expected_product is not None and product != expected_product:
        return None

    marker, _, agent = agent_product.partition("/")
    if marker != AGENT_MARKER or agent not in KNOWN_AGENTS:
        return None

    return DetectionResult(cast(AgentName, agent), "high", "user-agent", "User-Agent")
