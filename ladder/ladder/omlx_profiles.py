"""Switch the oMLX per-model profile through the admin API, with verified restore.

The two profiles are the spec's section 5.1. ``profile()`` snapshots the live
settings and the settings file, applies a profile, verifies the live values,
and restores the snapshot on exit even when the body raises.
"""

from __future__ import annotations

import json
import shutil
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

PROFILES: dict[str, dict] = {
    "baseline": {
        "max_context_window": 56000,
        "max_tokens": 4096,
        "thinking_budget_enabled": False,
        "thinking_budget_tokens": None,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
        "max_tool_result_tokens": None,
        "chat_template_kwargs": None,
        "forced_ct_kwargs": None,
    },
    "tuned": {
        "max_context_window": 56000,
        "max_tokens": 16384,
        "thinking_budget_enabled": True,
        "thinking_budget_tokens": 4096,
        "presence_penalty": 0.5,
        "repetition_penalty": 1.0,
        "max_tool_result_tokens": 4000,
        "chat_template_kwargs": {"enable_thinking": True},
        "forced_ct_kwargs": ["enable_thinking"],
    },
}
# Variant to isolate the presence penalty: everything in tuned except the penalty.
PROFILES["tuned-nopenalty"] = {**PROFILES["tuned"], "presence_penalty": 0.0}

# Request-level values. oMLX gives a request's sampling and cap values precedence
# over the model profile, so the runner must send these itself (through a
# temporary Pi models.json) for a profile to be in effect. Greedy by design:
# the ladder measures settings, not sampling variance. These keys are never PUT
# to the server.
_GREEDY = {"temperature": 0, "top_p": 1, "top_k": 0, "min_p": 0, "seed": 42}
REQUEST_PARAMS: dict[str, dict] = {
    "baseline": {**_GREEDY, "max_tokens": 4096, "presence_penalty": 0},
    "tuned": {**_GREEDY, "max_tokens": 16384, "presence_penalty": 0.5},
    "tuned-nopenalty": {**_GREEDY, "max_tokens": 16384, "presence_penalty": 0},
}


# Request params a caller may override from the command line. Sampling only:
# the ladder is greedy by design, so these exist for sampling screens, never to
# change a measured default. Server-only and structural keys are not overridable.
OVERRIDABLE_REQUEST_PARAMS = ("temperature", "top_p", "top_k", "min_p", "seed", "max_tokens")


def effective_request(name: str, overrides: dict | None = None) -> dict:
    """The profile's request block with any caller sampling overrides applied.

    Raises KeyError when an override names a param that is not sampling, so a
    typo or a server-only key can never masquerade as a request override.
    """
    merged = dict(REQUEST_PARAMS[name])
    for key, value in (overrides or {}).items():
        if key not in OVERRIDABLE_REQUEST_PARAMS:
            raise KeyError(f"not an overridable request param: {key}")
        merged[key] = value
    return merged


def check_effective_params(
    sent: dict, name: str, overrides: dict | None = None
) -> None:
    """Raise ProfileMismatch when the first request's values differ from the (optionally overridden) profile request block."""
    wanted = effective_request(name, overrides)
    bad = {k: (v, sent.get(k)) for k, v in wanted.items() if k in sent and sent[k] != v}
    missing = [k for k in wanted if k not in sent]
    if bad or missing:
        raise ProfileMismatch(
            f"{name}: request carried {bad or ''} missing {missing or ''}"
        )


class ProfileMismatch(RuntimeError):
    """The server accepted a settings update but the live values differ."""


class RestoreFailed(RuntimeError):
    """The original profile could not be put back; the message names the backup file."""


class SettingsClient(Protocol):
    def get_settings(self, model_id: str) -> dict: ...
    def put_settings(self, model_id: str, patch: dict) -> dict: ...


class AdminClient:
    """Minimal client for oMLX's admin API (auth is skipped on this server)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8001") -> None:
        self.base = base_url.rstrip("/")

    def _json(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read() or b"{}")

    def get_settings(self, model_id: str) -> dict:
        for model in self._json("GET", "/admin/api/models").get("models", []):
            if model.get("id") == model_id:
                return model["settings"]
        raise KeyError(model_id)

    def put_settings(self, model_id: str, patch: dict) -> dict:
        return self._json("PUT", f"/admin/api/models/{model_id}/settings", patch)


def apply_profile(client: SettingsClient, model_id: str, name: str) -> dict:
    patch = PROFILES[name]
    client.put_settings(model_id, patch)
    live = client.get_settings(model_id)
    mismatched = {k: (v, live.get(k)) for k, v in patch.items() if live.get(k) != v}
    if mismatched:
        raise ProfileMismatch(f"{name}: {mismatched}")
    return live


@contextmanager
def profile(
    client: SettingsClient, model_id: str, name: str, settings_path: Path
) -> Iterator[dict]:
    settings_path = Path(settings_path)
    snapshot = client.get_settings(model_id)
    backup = settings_path.with_name(
        f"{settings_path.name}.bak-ladder-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    )
    if settings_path.exists():
        shutil.copy2(settings_path, backup)
    try:
        yield apply_profile(client, model_id, name)
    finally:
        wanted = {key: snapshot[key] for key in PROFILES[name] if key in snapshot}
        try:
            client.put_settings(model_id, wanted)
            live = client.get_settings(model_id)
        except Exception as error:
            raise RestoreFailed(
                f"restore of {model_id} failed ({error!r}); original settings are in {backup}"
            ) from error
        stuck = {
            key: (value, live.get(key))
            for key, value in wanted.items()
            if live.get(key) != value
        }
        if stuck:
            raise RestoreFailed(
                f"restore of {model_id} did not take: {stuck}; original settings are in {backup}"
            )
