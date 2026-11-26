"""pathology_pairs: DPO pairs for the failure shapes the screens showed.

- a search or listing aimed outside the workspace (`find / -name tests` stalled a run for 7 minutes);
- a file written with an import it never uses (ruff F401 fails the quality gate);
- a later phase breaking an earlier phase's checks (the home page lost its doctype and tagline).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathology_pairs import (  # noqa: E402
    outside_search_pairs, render_alt, scope_command, strip_unused_imports, unused_import_pairs, with_regressions)
from phase_pairs import segment_trace  # noqa: E402

WS = "/runs/x/workspace"


def req(messages):
    return {"type": "provider_request", "payload": {"messages": messages, "tools": [{"t": 1}]}}


def act(name, args, think="why"):
    return {"type": "message_end", "message": {"role": "assistant", "content": [
        {"type": "thinking", "thinking": think},
        {"type": "text", "text": ""},
        {"type": "toolCall", "name": name, "id": "c1", "arguments": args}]}}


def hist(name):
    return {"role": "assistant", "content": None, "tool_calls": [{"function": {"name": name, "arguments": "{}"}}]}


SYS = {"role": "system", "content": "s"}
U1 = {"role": "user", "content": "Phase 1"}
TOOL = {"role": "tool", "content": "out"}


def one_phase(*acts):
    """A one-phase trace: each act gets its own request whose context holds the earlier acts."""
    rows, ctx = [{"type": "instance_start"}], [SYS, U1]
    for a in acts:
        rows += [req(list(ctx)), a]
        ctx += [hist(a["message"]["content"][2]["name"]), TOOL]
    return segment_trace(rows)[0]


# --- outside-workspace searches -------------------------------------------------------------

def test_scope_command_points_a_root_search_at_the_workspace():
    assert scope_command('find / -name "tests" 2>/dev/null', WS) == 'find . -name "tests" 2>/dev/null'
    assert scope_command("ls ~", WS) == "ls ."
    assert scope_command("grep -rn TODO $HOME", WS) == "grep -rn TODO ."
    assert scope_command("find /Users -name app.py", WS) == "find . -name app.py"


def test_scope_command_leaves_workspace_and_ordinary_commands_alone():
    assert scope_command(f"find {WS} -name app.py", WS) is None
    assert scope_command("find . -name app.py", WS) is None
    assert scope_command("uv run pytest -q", WS) is None
    assert scope_command("ls tests", WS) is None
    assert scope_command("cat /etc/hosts", WS) is None  # reading one named file is not a search


def test_outside_search_pairs_swap_only_the_offending_call():
    seg = one_phase(act("read", {"path": "app.py"}), act("bash", {"command": "find / -name tests 2>/dev/null"}),
                    act("bash", {"command": "uv run pytest"}))
    pairs = outside_search_pairs(seg, WS)
    assert len(pairs) == 1
    bad, calls = pairs[0]
    assert bad == 1 and calls[0]["arguments"] == {"command": "find . -name tests 2>/dev/null"}
    assert calls[0]["name"] == "bash"


def test_render_alt_shares_the_prefix_and_keeps_the_thinking():
    seg = one_phase(act("read", {"path": "app.py"}), act("bash", {"command": "find / -name tests"}, think="look"))
    bad, calls = outside_search_pairs(seg, WS)[0]
    chosen, rejected = render_alt(seg, bad, calls)
    assert chosen[:-1] == rejected[:-1]
    assert chosen[-1]["reasoning_content"] == rejected[-1]["reasoning_content"] == "look"
    assert '"find . -name tests"' in chosen[-1]["tool_calls"][0]["function"]["arguments"]
    assert '"find / -name tests"' in rejected[-1]["tool_calls"][0]["function"]["arguments"]


# --- unused imports ---------------------------------------------------------------------------

UNUSED = "from fastapi import FastAPI\nfrom fastapi.responses import HTMLResponse\n\napp = FastAPI()\n"


def test_strip_unused_imports_uses_ruff_and_keeps_the_rest():
    assert strip_unused_imports(UNUSED, "app.py") == "from fastapi import FastAPI\n\napp = FastAPI()\n"
    assert strip_unused_imports("import os\n\nprint(os.sep)\n", "app.py") is None  # nothing to fix


def test_unused_import_pairs_take_the_last_write_of_a_file_only():
    seg = one_phase(act("write", {"path": "app.py", "content": UNUSED}),
                    act("write", {"path": "tests/test_app.py", "content": "import os\n"}),
                    act("write", {"path": "models.py", "content": "import os\n"}),
                    act("write", {"path": "models.py", "content": "import os\n\nX = os.sep\n"}))
    pairs = unused_import_pairs(seg)
    assert [bad for bad, _ in pairs] == [0]  # tests are outside the gate; models.py was fixed by a later write
    assert pairs[0][1][0]["arguments"]["content"] == "from fastapi import FastAPI\n\napp = FastAPI()\n"


def test_unused_import_pairs_skip_a_file_a_later_edit_touches():
    seg = one_phase(act("write", {"path": "app.py", "content": UNUSED}),
                    act("edit", {"path": "app.py", "oldText": "app = FastAPI()", "newText": "app = FastAPI()\n"}))
    assert unused_import_pairs(seg) == []


# --- earlier-phase regressions ----------------------------------------------------------------

def test_with_regressions_fails_a_phase_that_broke_an_earlier_one():
    outcome = {2: True, 3: True, 4: False}
    assert with_regressions(outcome, {"verified": True, "regressed": {"3": [1]}}) == {2: True, 3: False, 4: False}


def test_with_regressions_ignores_unverified_or_missing_records():
    outcome = {2: True, 3: True}
    assert with_regressions(outcome, None) == outcome
    assert with_regressions(outcome, {"verified": False, "regressed": {"3": [1]}}) == outcome


def test_find_regressions_names_the_earlier_phases_each_phase_broke():
    from regrade_phases import find_regressions
    own = {1: True, 2: True, 3: True, 4: False}
    broken = {(3, 1), (4, 1), (4, 2)}  # (phase m's end state, earlier phase k) pairs that fail
    got = find_regressions(own, lambda m, k: (m, k) not in broken)
    assert got == {2: [], 3: [1], 4: [1, 2]}  # phase 1 broke nothing; a phase that never passed can't regress


# --- idioms the model doesn't know (training tasks only) ------------------------------------

REF = {"contacts.py": 'UNSET = sentinel("UNSET")\n'}


def test_idiom_pairs_swap_the_last_write_of_a_reference_file_for_the_reference():
    from pathology_pairs import idiom_pairs
    seg = one_phase(act("write", {"path": "contacts.py", "content": "UNSET = object()\n"}),
                    act("write", {"path": "tests/test_contacts.py", "content": "x"}),
                    act("write", {"path": f"{WS}/contacts.py", "content": "class U: pass\nUNSET = U()\n"}))
    pairs = idiom_pairs(seg, REF, WS)
    assert [bad for bad, _ in pairs] == [2]  # only the last write of the file counts
    assert pairs[0][1][0]["arguments"] == {"path": f"{WS}/contacts.py", "content": REF["contacts.py"]}


def test_idiom_pairs_skip_a_write_that_already_matches():
    from pathology_pairs import idiom_pairs
    same = one_phase(act("write", {"path": "contacts.py", "content": REF["contacts.py"]}))
    assert idiom_pairs(same, REF, WS) == []


def edit(path, *pairs):
    return act("edit", {"path": path, "edits": [{"oldText": o, "newText": n} for o, n in pairs]})


START = {"contacts.py": '"""Contact records."""\n'}


def test_idiom_pairs_turn_a_last_edit_into_the_same_edit_reaching_the_reference():
    """The task file already exists, so most runs edit it: replay the file from the task's starting copy, then the
    chosen call is an edit from what the file held at that point to the reference."""
    from pathology_pairs import idiom_pairs
    seg = with_results(
        (edit("contacts.py", ('"""Contact records."""', '"""Contact records."""\n\nUNSET = object()')),
         res("ok", error=False)),
        (edit("contacts.py", ("UNSET = nothing", "x")), res("Could not find the exact text", error=True)),  # failed
        (edit(f"{WS}/contacts.py", ("object()", "type('U', (), {})()")), res("ok", error=False)))
    pairs = idiom_pairs(seg, REF, WS, START)
    assert [bad for bad, _ in pairs] == [2]
    before = '"""Contact records."""\n\nUNSET = object()\n'  # the edit before it applied; the failed one didn't
    assert pairs[0][1][0]["arguments"] == {"path": f"{WS}/contacts.py",
                                           "edits": [{"oldText": before, "newText": REF["contacts.py"]}]}


def test_idiom_pairs_skip_an_edit_whose_file_state_cannot_be_replayed():
    from pathology_pairs import idiom_pairs
    seg = with_results((edit("contacts.py", ("text the start never had", "x")), res("ok", error=False)))
    assert idiom_pairs(seg, REF, WS, START) == []  # the recorded edit worked, so our replay is wrong: no pair
    assert idiom_pairs(seg, REF, WS) == []  # no starting copy: no edit pair


# --- malformed shell commands (quoting, python -c, flags this shell lacks) -----------------

def res(text, error=True):
    return {"type": "tool_result", "toolName": "bash", "isError": error, "content": [{"type": "text", "text": text}]}


def with_results(*pairs):
    """A one-phase trace where each (act, result) pair is followed by its tool result."""
    rows, ctx = [{"type": "instance_start"}], [SYS, U1]
    for a, r in pairs:
        rows += [req(list(ctx)), a] + ([r] if r else [])
        ctx += [hist(a["message"]["content"][2]["name"]), TOOL]
    return segment_trace(rows)[0]


QUOTE = "/bin/bash: -c: line 0: unexpected EOF while looking for matching `\"'\n"
PYSYN = '  File "<string>", line 1\n    try: import x; except: pass\n         ^\nSyntaxError: invalid syntax\n'
FLAG = "cat: illegal option -- A\nusage: cat [-belnstuv] [file ...]\n"


def test_shell_shape_names_the_command_faults_only():
    from pathology_pairs import shell_shape
    assert shell_shape(QUOTE) == "quote"
    assert shell_shape(PYSYN) == "pysyntax"
    assert shell_shape(FLAG) == "flag"
    assert shell_shape("FAILED tests/test_app.py::test_home - assert 404 == 200\n1 failed") is None  # red test: TDD
    assert shell_shape("ls: tests: No such file or directory\n") is None  # probing for a file is fine
    assert shell_shape('Traceback\n  File "app.py", line 3\nSyntaxError: x') is None  # the code is wrong, not the command


def test_shell_pairs_take_the_clean_bash_retry_as_chosen():
    from pathology_pairs import shell_pairs
    seg = with_results(
        (act("bash", {"command": 'python -c "try: import x; except: pass"'}), res(PYSYN)),
        (act("bash", {"command": "python -c 'import x'"}), res("ok", error=False)),
        (act("bash", {"command": "cat -A app.py"}), res(FLAG)),
        (act("write", {"path": "a.py", "content": "x"}), res("ok", error=False)),  # not a bash retry
        (act("bash", {"command": "uv run pytest"}), res("1 failed")),
        (act("bash", {"command": "uv run pytest"}), res("1 passed", error=False)))
    assert shell_pairs(seg) == [(0, 1)]  # flag fault has no bash retry; a red test run is not a fault
