import importlib
import importlib.util
import json
import os
from pathlib import Path

import pytest
from ladder.rungs import CheckResult, Rung

from ladder import run_ladder


def launch_module():
    assert importlib.util.find_spec("ladder.pi_launch") is not None, (
        "launch preflight is not implemented"
    )
    return importlib.import_module("ladder.pi_launch")


def executable(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)
    return path


def fake_pi(tmp_path):
    return executable(
        tmp_path / "runtime with spaces" / "pi",
        """
if [ "$1" = "--version" ]; then
  echo version > "$0.probed"
  echo 1.1.0
else
  echo launched > "$MELLUM_TRACE_FILE.launched"
  echo '{"type":"agent_settled","aborted":false}'
fi
""",
    )


def runner_setup(monkeypatch, tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    monkeypatch.setattr(run_ladder, "prepare_workspace", lambda *a, **kw: ws)
    monkeypatch.setattr(run_ladder, "baseline_index", lambda ws: (set(), {}))
    monkeypatch.setattr(run_ladder, "git", lambda *a: "")
    return ws, Rung(
        1, "calculator", "fix it", ["true"], lambda *a: CheckResult(False, True)
    )


def test_resolve_pi_path_and_symlink(tmp_path):
    module = launch_module()
    pi = fake_pi(tmp_path)
    alias = tmp_path / "pi-link"
    alias.symlink_to(pi)
    assert module.resolve_pi(str(alias)) == {
        "executable": str(alias),
        "version": "1.1.0",
    }
    assert Path(str(alias) + ".probed").read_text().strip() == "version"


@pytest.mark.parametrize("body", ["exit 2\n", 'echo ""\n'])
def test_failed_version_probe_is_preflight_failure(tmp_path, body):
    module = launch_module()
    with pytest.raises(RuntimeError, match="Pi"):
        module.resolve_pi(str(executable(tmp_path / "bad-pi", body)))


def test_python_preflight_uses_fixture_environment(tmp_path):
    module = launch_module()
    (tmp_path / "pyproject.toml").write_text('[project]\nname="fixture"\n')
    python = tmp_path / ".venv/bin/python"
    executable(python, "echo " + "'" + json.dumps({"executable": str(python)}) + "'\n")
    env, metadata = module.workspace_preflight(
        tmp_path, "ledger", {"PATH": os.environ["PATH"], "VIRTUAL_ENV": "/ladder-env"}
    )
    assert env["VIRTUAL_ENV"] == str(tmp_path / ".venv")
    assert env["PATH"].split(os.pathsep)[0] == str(python.parent)
    assert metadata["python"]["executable"] == str(python)
    assert metadata["python"]["imports"] == ["pytest"]


def test_non_python_preflight_records_node(tmp_path):
    module = launch_module()
    env, metadata = module.workspace_preflight(
        tmp_path,
        "calculator",
        {"PATH": os.environ["PATH"], "VIRTUAL_ENV": "/ladder-env"},
    )
    assert "VIRTUAL_ENV" not in env
    assert metadata["python"] is None
    assert metadata["node"]["version"].startswith("v")
    assert Path(metadata["node"]["executable"]).is_absolute()


def test_selected_pi_used_for_version_and_launch(monkeypatch, tmp_path):
    launch_module()
    pi = fake_pi(tmp_path)
    ws, rung = runner_setup(monkeypatch, tmp_path)
    record = run_ladder.run_once(
        rung,
        "direct",
        "baseline",
        1,
        tmp_path / "out",
        5,
        {},
        False,
        pi_executable=str(pi),
    )
    assert record["launch"]["argv"][0] == str(pi)
    assert record["launch"]["pi"] == {"executable": str(pi), "version": "1.1.0"}
    assert record["launch"]["cwd"] == str(ws)
    assert Path(str(pi) + ".probed").exists()


def test_preflight_failure_never_launches_pi(monkeypatch, tmp_path):
    launch_module()
    pi = fake_pi(tmp_path)
    ws, rung = runner_setup(monkeypatch, tmp_path)
    (ws / "pyproject.toml").write_text('[project]\nname="fixture"\n')
    executable(ws / ".venv/bin/python", 'echo "import failed" >&2\nexit 1\n')
    with pytest.raises(RuntimeError, match="preflight"):
        run_ladder.run_once(
            rung,
            "direct",
            "baseline",
            1,
            tmp_path / "out",
            5,
            {},
            False,
            pi_executable=str(pi),
        )
    assert not list(tmp_path.rglob("*.launched"))


def test_multicall_executable_keeps_invocation_name(tmp_path):
    module = launch_module()
    shim = executable(
        tmp_path / "tool-shim", 'case "$0" in */pi) echo 1.1.0 ;; *) exit 2 ;; esac\n'
    )
    alias = tmp_path / "pi"
    alias.symlink_to(shim)
    assert module.resolve_pi(str(alias))["executable"] == str(alias)


def test_child_env_removes_ladder_python_from_path():
    env = run_ladder.child_env(
        {"VIRTUAL_ENV": "/ladder-env", "PATH": "/ladder-env/bin:/usr/bin"}, "/tmp/trace"
    )
    assert env["PATH"] == "/usr/bin"


def test_preflight_python_identity_survives_a_symlinked_temp_dir(tmp_path):
    """macOS: /var is a link to /private/var, and Python 3.15 reports the real path."""
    from ladder.pi_launch import same_venv_python

    real = tmp_path / "private" / "ws" / ".venv" / "bin"
    real.mkdir(parents=True)
    (real / "python").write_text("")
    (tmp_path / "link").symlink_to(tmp_path / "private")
    via_link = tmp_path / "link" / "ws" / ".venv" / "bin" / "python"
    assert same_venv_python(str(real / "python"), via_link)
    assert not same_venv_python(str(tmp_path / "elsewhere" / "python"), via_link)
