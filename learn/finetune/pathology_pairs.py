"""DPO pairs for the failure shapes the screens showed (pure functions, apart from ruff).

Each pair shares the context before one recorded act and keeps the thinking the model wrote for it; only
the tool call differs, so score it with `scored_span(calls_only=True)`. The chosen call is the model's own
call with the one fault removed, so the pair teaches the fix and nothing else:

- a search or listing aimed outside the workspace (`find /`, `ls ~`) becomes the same command aimed at `.`;
- the last write of a source file that leaves an import unused becomes the same write without it (ruff's
  own F401 fix, the check the quality gate runs);
- a phase that broke an earlier phase's checks counts as a failed phase (`with_regressions`), using the
  grades `regrade_phases.py --regressions` records.

Every rule is general developer hygiene: nothing names a suite, route or expected value.
"""
import re
import subprocess
from pathlib import PurePosixPath

from phase_pairs import _calls, _call_turn, render_segment

RUFF = ["uvx", "ruff@0.14.0"]
SEARCH = {"find", "ls", "grep", "rg", "tree", "du", "fd"}
ROOTS = re.compile(r"(?<=\s)(/|~/?|\$HOME/?|/Users/?|/home/?)(?=\s|$)")


def scope_command(command, workspace):
    """The same search aimed at the workspace, or None if the command doesn't search outside it."""
    words = command.strip().split()
    if not words or words[0] not in SEARCH:
        return None
    scoped = ROOTS.sub(".", command)
    return scoped if scoped != command else None


def _alt(call, arguments):
    return {**call, "arguments": arguments}


def outside_search_pairs(seg, workspace):
    """(act index, chosen calls) for each act in this phase whose bash call searches outside the workspace."""
    acts, out = seg["acts"], []
    for k in range(len(acts) - seg["n_phase"], len(acts)):
        calls, changed = [], False
        for c in _calls(acts[k]):
            cmd = (c.get("arguments") or {}).get("command") if c.get("name") == "bash" else None
            scoped = scope_command(cmd, workspace) if isinstance(cmd, str) else None
            changed |= scoped is not None
            calls.append(_alt(c, {**c["arguments"], "command": scoped}) if scoped else c)
        if changed:
            out.append((k, calls))
    return out


def strip_unused_imports(source, filename):
    """`source` with its unused imports removed by ruff, or None if it has none."""
    done = subprocess.run([*RUFF, "check", "--isolated", "--select", "F401", "--fix-only", "--exit-zero",
                           "--stdin-filename", PurePosixPath(filename).name, "-"],
                          input=source, capture_output=True, text=True, check=True)
    return done.stdout if done.stdout != source else None


def _gated(path):
    """Is this a source file the quality gate checks? (It skips tests.)"""
    p = PurePosixPath(path)
    return p.suffix == ".py" and "tests" not in p.parts and not p.name.startswith("test_")


def unused_import_pairs(seg):
    """(act index, chosen calls) for the last write of each gated file in this phase that leaves an import unused.

    Only the file's last write or edit in the phase counts: an import a later call puts to use was not a fault."""
    acts, last = seg["acts"], {}
    start = len(acts) - seg["n_phase"]
    for k in range(start, len(acts)):
        for c in _calls(acts[k]):
            if c.get("name") in ("write", "edit"):
                last[(c.get("arguments") or {}).get("path")] = (k, c)
    out = {}
    for path, (k, c) in last.items():
        if c.get("name") != "write" or not isinstance(path, str) or not _gated(path):
            continue
        fixed = strip_unused_imports(c["arguments"].get("content") or "", path)
        if fixed is None:
            continue
        calls = out.get(k) or list(_calls(acts[k]))
        out[k] = [_alt(x, {**x["arguments"], "content": fixed}) if x is c else x for x in calls]
    return sorted(out.items())


def render_alt(seg, bad, chosen_calls, cap=lambda text: text):
    """(chosen, rejected) message lists sharing the context before act `bad`; chosen makes `chosen_calls`."""
    rendered = render_segment(seg, cap)
    if rendered is None:
        return None
    msgs, acts = rendered[0], seg["acts"]
    ast = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    j = bad - (len(acts) - len(ast))
    if j < 0 or j >= len(ast):
        return None
    prefix = msgs[:ast[j]]
    fake = {"content": [{"type": "toolCall", **c} for c in chosen_calls]}
    return prefix + [_call_turn(acts[bad], fake)], prefix + [_call_turn(acts[bad], acts[bad])]


def with_regressions(outcome, record):
    """`outcome` with every phase that broke an earlier phase's checks marked failed."""
    if not record or not record.get("verified"):
        return outcome
    broke = {int(p) for p, earlier in (record.get("regressed") or {}).items() if earlier}
    return {p: ok and p not in broke for p, ok in outcome.items()}

