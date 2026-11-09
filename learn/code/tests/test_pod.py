"""F.6's held pod: the pin card and the setup commands, built from it so no script can drift."""
import shlex
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conformance
import pod

PINS = conformance.load_pins(conformance.POD_PINS)
PREFIX, REPO, WEIGHTS = "/opt/mellum", "/opt/mellum/repo", "/workspace/mellum/models"


def test_the_pod_card_pins_the_macs_weights_build_server_and_numerics():
    mac = conformance.load_pins()
    for section in ("weights", "server", "numerics", "tooling"):
        assert PINS[section] == mac[section], section
    assert PINS["weights"]["sha256"] == mac["weights"]["sha256"]
    assert PINS["build"]["build_info"] == mac["build"]["build_info"]
    assert conformance.pins_digest(PINS) != conformance.pins_digest(mac), "pod numbers do not pool with the Mac's"


def test_the_pod_build_covers_the_a40_and_its_l40s_fallback():
    archs = PINS["pod"]["cuda_architectures"].split(";")
    assert "86" in archs and "89" in archs


def test_the_build_is_the_pinned_commit_with_full_history_and_a_bounded_job_count():
    joined = "\n".join(pod.build_commands(PINS, prefix=PREFIX, jobs=8))
    assert "--depth" not in joined, "a shallow clone reports the wrong build number"
    assert f"checkout --detach {PINS['pod']['llama_commit']}" in joined
    assert "-DGGML_CUDA=ON" in joined and "-DGGML_NATIVE=OFF" in joined
    assert f"-DCMAKE_CUDA_ARCHITECTURES='{PINS['pod']['cuda_architectures']}'" in joined
    assert "--target llama-server llama-perplexity -j 8" in joined
    assert "build 12110, commit cd959bae9" in joined, "the build proves its identity"


def test_node_is_checked_before_it_is_unpacked():
    commands = pod.node_commands(PINS, prefix=PREFIX)
    check = next(i for i, c in enumerate(commands) if "sha256sum --check" in c)
    unpack = next(i for i, c in enumerate(commands) if "tar -xJf" in c)
    assert check < unpack and PINS["pod"]["node_sha256"] in commands[check]


def test_the_weights_are_fetched_at_a_pinned_revision_and_checked():
    commands = pod.weights_commands(PINS, dest=WEIGHTS)
    assert PINS["pod"]["weights_revision"] in commands[1] and f"{WEIGHTS}/{PINS['weights']['file']}" in commands[1]
    assert PINS["weights"]["sha256"] in commands[-1] and "sha256sum --check" in commands[-1]


def test_the_checkout_is_locked_to_root_and_the_tools_stay_readable():
    commands = pod.lock_commands(prefix=PREFIX, repo=REPO)
    assert commands.index(f"chmod -R a+rX {PREFIX}") < commands.index(f"chmod -R go-rwx {REPO}"), \
        "opening the prefix must not reopen the checkout"
    assert f"chown -R root:root {REPO}" in commands


def test_the_session_user_has_no_password_and_a_warm_cache():
    assert f"passwd --lock {pod.SESSION_USER}" in pod.user_commands()
    warm = "\n".join(pod.warm_commands(PINS, prefix=PREFIX, repo=REPO))
    assert f"su -s /bin/bash {pod.SESSION_USER}" in warm or f"runuser -u {pod.SESSION_USER}" in warm
    assert "uv sync --frozen" in warm or "sync --frozen" in warm
    assert "pytest --version" in warm, "the mediated test runs `uv run --offline`, so pytest must be cached"


def test_grading_has_a_locked_user_of_its_own():
    commands = pod.user_commands()
    assert any(f"useradd --create-home --shell /bin/bash {pod.GRADE_USER}" in c for c in commands)
    assert f"passwd --lock {pod.GRADE_USER}" in commands


def test_the_image_web_server_is_stopped_so_its_ports_are_free():
    assert any("nginx" in c for c in pod.free_ports_commands())


def test_the_server_runs_the_pinned_command_in_tmux():
    command = pod.serve_commands(PINS, prefix=PREFIX, weights=WEIGHTS, threads=8, log="/tmp/llama.log")[-1]
    argv = conformance.server_argv(PINS, binary=f"{PREFIX}/bin/llama-server",
                                   model=f"{WEIGHTS}/{PINS['weights']['file']}", port=8001, threads=8,
                                   log="/tmp/llama.log")
    assert "tmux new-session -d -s mellum-llama" in command and shlex.quote(shlex.join(argv)) in command


def test_steps_run_in_order_and_skip_what_is_done(tmp_path):
    ran = tmp_path / "ran.txt"
    steps = [("one", [f"echo one >> {ran}"]), ("two", [f"echo two >> {ran}"])]
    pod.run_steps(steps, tmp_path / "done")
    pod.run_steps(steps, tmp_path / "done")
    assert ran.read_text().split() == ["one", "two"]


def test_a_failing_step_stops_the_run_and_is_not_marked_done(tmp_path):
    with pytest.raises(SystemExit, match="bad"):
        pod.run_steps([("bad", ["false"]), ("after", [f"touch {tmp_path / 'after'}"])], tmp_path / "done")
    assert not (tmp_path / "after").exists() and not (tmp_path / "done" / "bad").exists()


@pytest.mark.parametrize(("text", "expected"), [("800000 100000\n", 8), ("765000 100000\n", 7), ("max 100000\n", 64)])
def test_the_cpu_count_is_the_cgroups_not_nprocs(text, expected):
    assert pod.cgroup_cpus(text, fallback=64) == expected


def test_a_pod_cpu_quota_under_one_still_gives_one_thread():
    assert pod.cgroup_cpus("50000 100000\n", fallback=64) == 1


def test_setup_scripts_are_executable():
    for name in ("bootstrap.sh", "push.sh"):
        assert (pod.REPO / "scripts" / "pod" / name).stat().st_mode & stat.S_IXUSR, name


def test_the_defaults_keep_runs_off_the_volume_that_refuses_chown():
    # /workspace on a Secure Cloud pod is NFS and refuses chown, so a session user cannot own a run tree there.
    parser_defaults = pod.DEFAULTS
    assert parser_defaults["prefix"] == "/opt/mellum" and not parser_defaults["repo"].startswith("/workspace")
    assert parser_defaults["weights"].startswith("/workspace/")


def test_results_are_copied_to_the_volume_without_owners_or_venvs():
    command = pod.keep_results_command(runs="/opt/mellum/runs/x", results="/workspace/mellum/results/x")
    assert "rsync -rlt " in command and "--exclude .venv" in command
    assert " -a " not in command, "the volume refuses chown, so -a would fail"
