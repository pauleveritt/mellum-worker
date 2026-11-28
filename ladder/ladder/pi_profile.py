"""A temporary Pi agent directory mirroring the operator's, and the ladder's workspace `.pi/`.

Delegated runs launch the parent with ``PI_CODING_AGENT_DIR`` pointing at the
mirror, so the parent has its normal settings, models, credentials, and
packages while nothing under ``~/.pi/agent`` is written to. The scratch
workspace gets the worker definition rendered from this checkout's template
with the ladder's recorder appended, because pi-subagents overrides cannot
add extensions.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .omlx_profiles import effective_request

LADDER_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LADDER_ROOT.parent
MODEL_ID = "Mellum2.1-12B-A2.5B-Thinking-6bit"
DEFAULT_BASE_URL = "http://127.0.0.1:8001/v1"
COPIED_FILES = ("settings.json", "models.json", "auth.json", "AGENTS.md")
LINKED_DIRS = ("git", "npm")


def mirror_agent_dir(
    source: Path,
    dest: Path,
    trusted: list[Path],
    exclude_packages: tuple[str, ...] = (),
) -> Path:
    """Copy the parent's configuration, link its packages, trust the given workspaces.

    `exclude_packages` drops settings.json `packages` entries naming any of the
    given substrings from the mirror's copy, so an installed copy of this
    package does not load beside the checkout under test.
    """
    dest.mkdir(parents=True, exist_ok=True)
    for name in COPIED_FILES:
        if (source / name).exists():
            shutil.copy2(source / name, dest / name)
    if (source / "extensions").is_dir():
        shutil.copytree(source / "extensions", dest / "extensions", dirs_exist_ok=True)
    settings = dest / "settings.json"
    if exclude_packages and settings.exists():
        data = json.loads(settings.read_text())
        data["packages"] = [
            p
            for p in data.get("packages", [])
            if not any(needle in json.dumps(p) for needle in exclude_packages)
        ]
        settings.write_text(json.dumps(data, indent=2))
    for name in LINKED_DIRS:
        if (source / name).exists():
            os.symlink(source / name, dest / name, target_is_directory=True)
    (dest / "trust.json").write_text(
        json.dumps({str(p): True for p in trusted}, indent=2)
    )
    return dest


def direct_agent_dir(
    dest: Path,
    profile: str,
    base_url: str = DEFAULT_BASE_URL,
    *,
    provider: str = "omlx",
    model_id: str = MODEL_ID,
    context_window: int = 56000,
    request_overrides: dict | None = None,
) -> Path:
    """A minimal Pi agent directory whose model entry sends the profile's request values.

    Direct mode uses this instead of the operator's profile so that temperature,
    caps, and penalties are the ladder's, not Pi's defaults. ``provider``,
    ``base_url`` and ``model_id`` point the OpenAI-completions entry at any
    server (oMLX by default, llama.cpp or a plain mlx_lm.server);
    ``request_overrides`` applies sampling overrides for a screen.
    """
    request = effective_request(profile, request_overrides)
    max_tokens = request.pop("max_tokens")
    entry = {
        "id": model_id,
        "name": "Mellum ladder",
        "reasoning": True,
        "input": ["text"],
        "contextWindow": context_window,
        "maxTokens": max_tokens,
        "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
        "compat": {
            "supportsDeveloperRole": False,
            "supportsReasoningEffort": False,
            "maxTokensField": "max_tokens",
            "thinkingFormat": "qwen-chat-template",
        },
        "samplingParams": request,
    }
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "models.json").write_text(
        json.dumps(
            {
                "providers": {
                    provider: {
                        "baseUrl": base_url,
                        "api": "openai-completions",
                        "apiKey": "not-needed",
                        "models": [entry],
                    }
                }
            },
            indent=2,
        )
    )
    (dest / "settings.json").write_text(
        json.dumps(
            {
                "defaultProvider": provider,
                "defaultModel": model_id,
                "defaultThinkingLevel": "high",
                "compaction": {"enabled": False},
                "quietStartup": True,
            },
            indent=2,
        )
    )
    return dest
