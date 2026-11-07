"""The ladder's request-level sampling profiles.

The three profiles are the spec's section 5.1, reduced to what a scriptable
OpenAI-completions server needs: the sampling and cap values the runner sends
with every request. The server gives a request's values precedence over any
model-side default, so the runner must send these itself (through a temporary
Pi ``models.json``) for a profile to be in effect. Greedy by design: the ladder
measures settings, not sampling variance.
"""

from __future__ import annotations

# Request-level values the runner sends with every call. Greedy by design: the
# ladder measures settings, not sampling variance.
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


class ProfileMismatch(RuntimeError):
    """The request Pi sent carried values that differ from the profile's."""


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
