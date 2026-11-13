"""Turn recorded Pi events into a Score. Pure functions, replayable offline.

Events are the JSON lines written by ``extensions/mellum-recorder.ts``:
``provider_request`` (the wire payload), ``tool_call`` (toolName, input),
and ``tool_result`` (toolName, isError, content). Every column maps to a
pathology recorded in ``../local-ai-pi`` or ``../satyrn-evals``.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

_QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
_HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?(?:\n\2\s*$|\Z)", re.DOTALL | re.MULTILINE
)
_NULL_SINK = re.compile(r"\d?>>?\s*/dev/null|\d>&\d|&>\s*/dev/null|\btee\s+/dev/null")
_REDIRECT_TO_PATH = re.compile(r"(?<![<>|&=\-])>{1,2}\s*(?!&)[\w./~$-]")
_WRITING_COMMAND = re.compile(
    r"(?:^|[;&|]\s*)(?:tee\s+(?!-)|sed\s+-[a-zA-Z]*i|perl\s+-[a-zA-Z]*i|mv\s|cp\s)"
)


LOOP_WINDOW = 20
LOOP_THRESHOLD = 5
# Tools after which an earlier call's result may legitimately differ (mirrors mellum-guards.ts).
MUTATING_TOOLS = {"edit", "write", "bash"}


def bash_mutates(command: str) -> bool:
    """True when a bash command writes a file: a redirect to a path, tee, an
    in-place editor, mv/cp, or a heredoc fed to a redirect.

    Quoted strings and heredoc bodies are removed before matching so that
    `python -c "print(1 > 0)"` and `grep -v '>'` do not count, and null sinks
    such as `2>&1`, `>/dev/null`, `tee /dev/null` are stripped.
    """
    text = _HEREDOC.sub(lambda m: m.group(0).split("\n", 1)[0], command)
    text = _QUOTED.sub("", text)
    text = _NULL_SINK.sub("", text)
    return bool(_REDIRECT_TO_PATH.search(text) or _WRITING_COMMAND.search(text))


def call_key(name: str, payload: object) -> str:
    """Stable identity for a tool call: same tool and same arguments, any key order."""
    return name + "\0" + json.dumps(payload, sort_keys=True, default=str)


@dataclass
class Score:
    requests: int = 0
    largest_prompt_chars: int = 0
    tool_calls_by_name: dict[str, int] = field(default_factory=dict)
    tool_errors: int = 0
    edit_anchor_failures: int = 0
    noop_edits: int = 0
    write_existing: list[dict] = field(default_factory=list)
    bash_file_mutations: int = 0
    max_identical_streak: int = 0
    write_shrink: int = 0
    nudges: int = 0
    # Repeats of one call within the loop breaker's 20-call window: the metric
    # the guard uses, as opposed to max_identical_streak (adjacent only).
    max_identical_in_window: int = 0
    # Calls the ported loop breaker would have blocked, replayed with its exact
    # semantics: a call is refused when five matches already sit in the window
    # of admitted calls, and a refused call does not enter the window.
    loop_breaker_would_block: int = 0
    # Sampling and cap values the client actually sent on the first request.
    # oMLX gives these precedence over the model profile, so they, not the
    # profile, are the effective settings.
    effective_params: dict = field(default_factory=dict)

    def as_row(self) -> dict:
        row = asdict(self)
        row["write_existing"] = len(self.write_existing)
        return row


def _path(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("path", "filePath", "file_path"):
        if key in payload:
            return str(payload[key])
    return None


def score(
    events: list[dict], baseline_paths: set[str], baseline_lines: dict[str, int]
) -> Score:
    result = Score()
    streak = 0
    last_key = None
    window: list[str] = []
    admitted: list[str] = []
    for event in events:
        kind = event.get("type")
        if kind == "provider_request":
            result.requests += 1
            payload = event.get("payload", {})
            if not result.effective_params:
                result.effective_params = {
                    k: payload[k]
                    for k in (
                        "temperature",
                        "top_p",
                        "top_k",
                        "min_p",
                        "seed",
                        "max_tokens",
                        "presence_penalty",
                        "thinking_budget",
                    )
                    if k in payload
                }
            size = len(json.dumps(payload))
            result.largest_prompt_chars = max(result.largest_prompt_chars, size)
            nudges = sum(
                "[mellum-guard]" in str(m.get("content", ""))
                for m in (payload.get("messages") or [])
                if isinstance(m, dict)
            )
            result.nudges = max(result.nudges, nudges)
        elif kind == "tool_call":
            name = event["toolName"]
            payload = event.get("input", {})
            result.tool_calls_by_name[name] = result.tool_calls_by_name.get(name, 0) + 1
            key = call_key(name, payload)
            streak = streak + 1 if key == last_key else 1
            last_key = key
            result.max_identical_streak = max(result.max_identical_streak, streak)
            if name in MUTATING_TOOLS:
                # The shipped breaker forgets repeats after a call that may
                # change their result; the replay must do the same.
                window.clear()
                admitted.clear()
            else:
                window.append(key)
                del window[:-LOOP_WINDOW]
                result.max_identical_in_window = max(
                    result.max_identical_in_window, window.count(key)
                )
                if admitted.count(key) >= LOOP_THRESHOLD:
                    result.loop_breaker_would_block += 1
                else:
                    admitted.append(key)
                del admitted[:-LOOP_WINDOW]
            if name == "write":
                path = _path(payload)
                if path and path in baseline_paths:
                    content = str(payload.get("content", ""))
                    before = baseline_lines.get(path, 0)
                    after = len(content.splitlines())
                    result.write_existing.append(
                        {"path": path, "lines_before": before, "lines_after": after}
                    )
                    if after < before:
                        result.write_shrink += 1
            if name == "bash" and bash_mutates(str(payload.get("command", ""))):
                result.bash_file_mutations += 1
        elif kind == "tool_result":
            content = str(event.get("content", ""))
            if event.get("isError"):
                result.tool_errors += 1
            if event["toolName"] == "edit":
                if (
                    "not found" in content
                    or "oldString" in content
                    or "Could not find" in content
                ):
                    result.edit_anchor_failures += 1
                if "No changes made" in content:
                    result.noop_edits += 1
    return result
