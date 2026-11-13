import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Optional, cast

AgentConfidence = Literal["high", "medium", "low"]
DetectionSource = Literal["environment", "path", "user-agent"]
AgentName = Literal[
    "amp",
    "antigravity",
    "augment-cli",
    "claude-code",
    "codex",
    "copilot-cli",
    "cowork",
    "cursor",
    "cursor-cli",
    "gemini-cli",
    "goose",
    "grok",
    "grok-bot",
    "kiro",
    "opencode",
    "pi",
    "replit",
]

KNOWN_AGENTS: frozenset[AgentName] = frozenset(
    {
        "amp",
        "antigravity",
        "augment-cli",
        "claude-code",
        "codex",
        "copilot-cli",
        "cowork",
        "cursor",
        "cursor-cli",
        "gemini-cli",
        "goose",
        "grok",
        "grok-bot",
        "kiro",
        "opencode",
        "pi",
        "replit",
    }
)

_PI_AGENT_PATH = re.compile(r"(?:^|[\\/])\.pi[\\/]agent(?:[\\/]|$)")


@dataclass(frozen=True)
class DetectionResult:
    """Evidence that an AI coding agent is driving the current process or request."""

    agent: AgentName
    confidence: AgentConfidence
    source: DetectionSource
    signal: str


def detect_agent(
    environ: Optional[Mapping[str, str]] = None,
    *,
    minimum_confidence: AgentConfidence = "low",
) -> Optional[DetectionResult]:
    """Detect the AI coding agent driving the current process, if any.

    Detection is best-effort. A ``None`` result means "unattributed", not "human".

    Values from the environment are inspected locally but are never included in
    the returned result.
    """

    values = os.environ if environ is None else environ

    if minimum_confidence not in ("high", "medium", "low"):
        raise ValueError("minimum_confidence must be 'high', 'medium', or 'low'")

    confidence_order: tuple[AgentConfidence, ...] = ("high", "medium", "low")
    minimum_confidence_index = confidence_order.index(minimum_confidence)
    candidates: list[DetectionResult] = []

    # An explicit known identity is checked before inferred signals.
    explicit_agent = values.get("AI_AGENT", "")
    if explicit_agent in KNOWN_AGENTS:
        candidates.append(
            DetectionResult(cast(AgentName, explicit_agent), "high", "environment", "AI_AGENT")
        )

    # Amp sets CLAUDECODE too, so its more specific signals must win.
    if values.get("AGENT") == "amp":
        candidates.append(DetectionResult("amp", "high", "environment", "AGENT"))
    if values.get("AMP_CURRENT_THREAD_ID"):
        candidates.append(DetectionResult("amp", "medium", "environment", "AMP_CURRENT_THREAD_ID"))

    # OpenAI Codex CLI.
    for signal in ("CODEX_THREAD_ID", "CODEX_CI", "CODEX_SANDBOX"):
        if values.get(signal):
            candidates.append(DetectionResult("codex", "high", "environment", signal))

    # Google Gemini CLI.
    if values.get("GEMINI_CLI"):
        candidates.append(DetectionResult("gemini-cli", "high", "environment", "GEMINI_CLI"))

    # GitHub Copilot CLI. This signal is observed but not publicly documented.
    if values.get("COPILOT_CLI"):
        candidates.append(DetectionResult("copilot-cli", "medium", "environment", "COPILOT_CLI"))

    # OpenCode sets OPENCODE for the running agent. OPENCODE_CLIENT and
    # OPENCODE_CALLER identify its launcher, so they are intentionally ignored.
    if values.get("OPENCODE"):
        candidates.append(DetectionResult("opencode", "high", "environment", "OPENCODE"))

    if values.get("ANTIGRAVITY_AGENT"):
        candidates.append(
            DetectionResult("antigravity", "medium", "environment", "ANTIGRAVITY_AGENT")
        )

    if values.get("AUGMENT_AGENT"):
        candidates.append(DetectionResult("augment-cli", "medium", "environment", "AUGMENT_AGENT"))

    # Cowork and Claude Code share ambient Claude markers. Check Cowork first.
    if values.get("CLAUDE_CODE_IS_COWORK"):
        candidates.append(DetectionResult("cowork", "high", "environment", "CLAUDE_CODE_IS_COWORK"))

    # This specifically marks commands spawned by Claude Code.
    if values.get("CLAUDE_CODE_CHILD_SESSION"):
        candidates.append(
            DetectionResult("claude-code", "high", "environment", "CLAUDE_CODE_CHILD_SESSION")
        )

    # These can also exist in Claude's integrated terminal, so they carry less
    # confidence than the child-session signal.
    for signal in ("CLAUDECODE", "CLAUDE_CODE"):
        if values.get(signal):
            candidates.append(DetectionResult("claude-code", "medium", "environment", signal))

    # Grok Build injects GROK_SESSION_ID into child processes and hooks.
    if values.get("GROK_SESSION_ID"):
        candidates.append(DetectionResult("grok", "high", "environment", "GROK_SESSION_ID"))

    # GROK_AGENT is also a user-facing profile selector, so presence alone is
    # a weaker signal than the session id.
    if values.get("GROK_AGENT"):
        candidates.append(DetectionResult("grok", "medium", "environment", "GROK_AGENT"))

    # Grok Bot runs through Cursor and also sets CURSOR_AGENT. Its observed,
    # undocumented Sand computer IDs distinguish it from Cursor CLI.
    if (
        values.get("CURSOR_AGENT")
        and values.get("SAND_BOX_BOOT_ID")
        and values.get("SAND_BOX_STORE_ID")
    ):
        candidates.append(DetectionResult("grok-bot", "high", "environment", "SAND_BOX_BOOT_ID"))

    # Cursor IDE and Cursor CLI are distinguishable when both signals exist.
    if values.get("CURSOR_TRACE_ID"):
        candidates.append(DetectionResult("cursor", "medium", "environment", "CURSOR_TRACE_ID"))

    if values.get("CURSOR_AGENT"):
        candidates.append(DetectionResult("cursor-cli", "high", "environment", "CURSOR_AGENT"))

    if values.get("CURSOR_EXTENSION_HOST_ROLE") == "agent-exec":
        candidates.append(
            DetectionResult("cursor-cli", "medium", "environment", "CURSOR_EXTENSION_HOST_ROLE")
        )

    # The following signals are broader or have less first-party evidence, so
    # they are checked only after the more specific agent signals above.
    if values.get("TERM_PROGRAM") == "kiro":
        candidates.append(DetectionResult("kiro", "low", "environment", "TERM_PROGRAM"))

    path = values.get("PATH", "")
    if _PI_AGENT_PATH.search(path):
        candidates.append(DetectionResult("pi", "medium", "path", "PATH"))

    if values.get("REPL_ID"):
        candidates.append(DetectionResult("replit", "low", "environment", "REPL_ID"))

    if values.get("GOOSE_PROVIDER"):
        candidates.append(DetectionResult("goose", "low", "environment", "GOOSE_PROVIDER"))

    return next(
        (
            candidate
            for candidate in candidates
            if confidence_order.index(candidate.confidence) <= minimum_confidence_index
        ),
        None,
    )
