"""baseline.py's own logic, without renting anything: run with
`uv run --with pytest python -m pytest scripts/baseline/tests`."""

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("baseline", HERE / "baseline.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)

PINS = baseline.pins()
A6000 = "NVIDIA RTX A6000, 49140, 595.104.02"


def test_pins_parse_without_a_shell():
    assert PINS["BASELINE_GPU_NAME"] == "NVIDIA RTX A6000"
    assert PINS["BASELINE_LADDER_RUNGS"].split() == [str(n) for n in range(1, 13)]
    assert PINS["BASELINE_VLLM_IMAGE"].startswith("vllm/vllm-openai:v0.32.0@sha256:")


def test_load_kv_strips_quotes_expands_home_and_skips_comments(tmp_path):
    f = tmp_path / "x.env"
    f.write_text('# c\nA="one two"\nB=\'q\'\nC=~/k\n\nnot a pair\n')
    assert baseline.load_kv(f) == {"A": "one two", "B": "q", "C": str(Path.home() / "k")}


def test_the_pinned_gpu_passes():
    assert baseline.gpu_problems(baseline.parse_gpus(A6000 + "\n"), PINS) == []


@pytest.mark.parametrize("rows, why", [
    (["NVIDIA GeForce RTX 5090, 32607, 595.91.07"], "pinned to"),
    (["NVIDIA RTX A6000, 46068, 595.104.02"], "pinned to"),
    ([A6000, A6000], "pinned to"),
    ([], "no GPU"),
    (["NVIDIA RTX A6000, 49140, 550.163.01"], "older than 580"),
])
def test_another_gpu_or_an_old_driver_is_refused(rows, why):
    problems = baseline.gpu_problems(baseline.parse_gpus("\n".join(rows)), PINS)
    assert any(why in p for p in problems), problems


@pytest.mark.parametrize("system, machine, key, suffix", [
    ("Darwin", "arm64", "darwin_arm64", "darwin-arm64.tar.gz"),
    ("Linux", "x86_64", "linux_x64", "linux-x64.tar.xz"),
    ("Linux", "aarch64", "linux_arm64", "linux-arm64.tar.xz"),
    ("Windows", "AMD64", "win_x64", "win-x64.zip"),
])
def test_every_platform_has_a_pinned_checksummed_node(system, machine, key, suffix):
    assert baseline.node_platform(system, machine) == (key, suffix)
    assert len(PINS[f"BASELINE_NODE_SHA256_{key}"]) == 64


def test_an_unpinned_platform_is_refused():
    with pytest.raises(SystemExit, match="no pinned Node build"):
        baseline.node_platform("FreeBSD", "x86_64")


def test_the_offer_search_asks_for_the_pinned_gpu_and_driver():
    q = baseline.offer_query(PINS, {"VAST_MAX_DPH": "0.55", "VAST_DISK_GB": "80"})
    assert "gpu_name=RTX_A6000" in q and "num_gpus=1" in q
    assert "dph_total<=0.55" in q and "driver_version>=580.0.0" in q and "verified=true" in q


def test_the_placeholder_token_is_refused_not_sent(tmp_path, monkeypatch):
    f = tmp_path / "vast.env"
    f.write_text(f'VAST_API_KEY="{baseline.PLACEHOLDER}"\n')
    monkeypatch.setenv("VAST_CONFIG", str(f))
    with pytest.raises(SystemExit, match="set VAST_API_KEY"):
        baseline.config()


def test_a_missing_config_says_how_to_make_one(tmp_path, monkeypatch):
    monkeypatch.setenv("VAST_CONFIG", str(tmp_path / "none.env"))
    with pytest.raises(SystemExit, match="copy vast.env.example"):
        baseline.config()


def test_an_unknown_command_prints_the_usage(capsys):
    assert baseline.main(["frobnicate"]) == 2
    assert "destroys on any exit" in capsys.readouterr().out


def test_the_screen_is_a_small_named_subset_of_the_baseline():
    full, screen = baseline.run_plan(PINS, screen=False), baseline.run_plan(PINS, screen=True)
    assert full == {"rungs": PINS["BASELINE_LADDER_RUNGS"].split(), "ladder_repeat": "3",
                    "suites": "all", "suite_repeat": "3", "label": "baseline", "stall": "120"}
    assert screen["label"] == "screen"
    assert set(screen["rungs"]) < set(full["rungs"])
    assert screen["ladder_repeat"] == screen["suite_repeat"] == "1"
    assert screen["suites"] == "easy"


def test_run_and_all_take_screen_and_all_takes_keep():
    assert baseline.parse_args(["run", "--screen"]) == ("run", {"screen": True, "suites_only": False})
    assert baseline.parse_args(["all"]) == ("all", {"screen": False, "keep": False})
    assert baseline.parse_args(["all", "--keep", "--screen"]) == ("all", {"screen": True, "keep": True})
    assert baseline.parse_args(["down"]) == ("down", {})
    assert baseline.parse_args(["up", "--screen"]) is None
    assert baseline.parse_args(["run", "--keep"]) is None
    assert baseline.parse_args(["run", "--fast"]) is None


def test_the_tunnel_avoids_the_ports_the_model_serves_its_apps_on(tmp_path, monkeypatch):
    """Screen 1: an app the model started bound *:8000 beside a tunnel on 8000."""
    key = tmp_path / "id"
    key.write_text("")
    (tmp_path / "id.pub").write_text("ssh-ed25519 AAAA t")
    f = tmp_path / "vast.env"
    f.write_text(f'VAST_API_KEY=k\nVAST_SSH_KEY={key}\n')
    monkeypatch.setenv("VAST_CONFIG", str(f))
    assert baseline.config()["LOCAL_PORT"] not in {"3000", "5000", "8000", "8001", "8080"}
    example = baseline.load_kv(HERE / "vast.env.example")
    assert example["LOCAL_PORT"] == baseline.config()["LOCAL_PORT"]


PAGE = '''# E9 · Example

### Run it yourself

Run both arms:

```bash
uv run python learn/code/harness.py run --suite medium --arm worker \\
  --specs joined --repeat 3 --grade --deadline 2700
uv run python learn/code/harness.py run --suite medium --arm worker \\
  --single-prompt --repeat 3 --grade --deadline 2700
```

!!! success "Key points"
'''

LOOP = '''### Run it yourself

```bash
for suite in easy medium; do
  for arm in bare worker; do
    uv run python learn/code/harness.py run --suite "$suite" --arm "$arm" --repeat 3 --grade --deadline 2700
  done
done
```

!!! success "Key points"
'''


def test_lesson_commands_are_read_from_run_it_yourself():
    cmds = baseline.lesson_commands(PAGE)
    assert [c[c.index("--suite"):c.index("--suite") + 2] for c in cmds] == [["--suite", "medium"]] * 2
    assert "--specs" in cmds[0] and "--single-prompt" in cmds[1]


def test_a_shell_loop_expands_into_one_command_per_arm():
    cmds = baseline.lesson_commands(LOOP)
    pairs = [(c[c.index("--suite") + 1], c[c.index("--arm") + 1]) for c in cmds]
    assert pairs == [("easy", "bare"), ("easy", "worker"), ("medium", "bare"), ("medium", "worker")]


def test_a_page_with_no_command_yields_none():
    assert baseline.lesson_commands("### Run it yourself\n\nNo arm to run.\n\n!!! success \"Key points\"\n") == []


def test_a_smoke_run_is_one_session_per_arm_through_the_pinned_client(tmp_path):
    cmd = baseline.lesson_commands(PAGE)[0]
    out = baseline.smoke_argv(cmd, profile=tmp_path / "p", pi=tmp_path / "pi", runs=tmp_path / "r")
    assert out[out.index("--repeat") + 1] == "1"
    assert out[out.index("--profile") + 1] == str(tmp_path / "p")
    assert out[out.index("--pi-binary") + 1] == str(tmp_path / "pi")
    assert out[out.index("--runs-dir") + 1] == str(tmp_path / "r")
    assert "--grade" in out and out[out.index("--deadline") + 1] == "2700"


def test_the_suites_carry_the_pinned_stall_limit():
    assert PINS["BASELINE_SUITE_STALL"] == "120"
    plan = baseline.run_plan(PINS, screen=False)
    assert plan["stall"] == "120"


def test_run_takes_suites_only():
    assert baseline.parse_args(["run", "--suites-only"]) == ("run", {"screen": False, "suites_only": True})
    assert baseline.parse_args(["run"]) == ("run", {"screen": False, "suites_only": False})


def test_a_lesson_smoke_run_carries_the_stall_limit(tmp_path):
    cmd = baseline.lesson_commands(PAGE)[0]
    out = baseline.smoke_argv(cmd, profile=tmp_path / "p", pi=tmp_path / "pi", runs=tmp_path / "r", stall="120")
    assert out[out.index("--stall") + 1] == "120"


def test_the_smoke_deadline_is_capped_never_raised(tmp_path):
    long_cmd = baseline.lesson_commands(PAGE)[0]                     # --deadline 2700
    out = baseline.smoke_argv(long_cmd, profile=tmp_path, pi=tmp_path, runs=tmp_path, cap="900")
    assert out[out.index("--deadline") + 1] == "900"
    short = ["uv", "run", "python", "learn/code/harness.py", "run", "--suite", "easy", "--deadline", "600"]
    out = baseline.smoke_argv(short, profile=tmp_path, pi=tmp_path, runs=tmp_path, cap="900")
    assert out[out.index("--deadline") + 1] == "600"
    bare = ["uv", "run", "python", "learn/code/harness.py", "run", "--suite", "easy"]
    out = baseline.smoke_argv(bare, profile=tmp_path, pi=tmp_path, runs=tmp_path, cap="900")
    assert "--deadline" not in out                                    # the harness default (600) is under the cap


def test_lesson_runs_are_pinned_parallel_and_capped():
    assert int(PINS["BASELINE_LESSON_PARALLEL"]) >= 1
    assert int(PINS["BASELINE_LESSON_DEADLINE_CAP"]) >= 300


def test_lesson_commands_run_in_parallel_and_keep_their_order(monkeypatch):
    import threading, time as _t
    active, peak, lock = [0], [0], threading.Lock()

    def fake(argv):
        with lock:
            active[0] += 1; peak[0] = max(peak[0], active[0])
        _t.sleep(0.05)
        with lock:
            active[0] -= 1
        return 0, argv[-1]

    results = baseline.run_all([["x", str(i)] for i in range(6)], fake, parallel=3)
    assert peak[0] == 3
    assert [r[1] for r in results] == [str(i) for i in range(6)]



def test_serve_start_and_alive_track_the_server_by_pid(tmp_path):
    # vLLM renames its own process, so a name match calls a live server dead;
    # the start command records the PID and the alive check uses only that.
    import subprocess, time
    (tmp_path / "serve.sh").write_text("#!/bin/sh\nexec sleep 30\n")
    (tmp_path / "serve.sh").chmod(0o755)
    sh = lambda cmd: subprocess.run(["bash", "-c", cmd], cwd=tmp_path, capture_output=True, text=True)
    assert sh(baseline.ALIVE).returncode != 0
    assert sh(baseline.START).returncode == 0
    time.sleep(0.5)
    pid = int((tmp_path / "vllm.pid").read_text())
    assert sh(baseline.ALIVE).returncode == 0
    assert sh(baseline.START).returncode == 0
    assert int((tmp_path / "vllm.pid").read_text()) == pid  # never a second server
    subprocess.run(["kill", str(pid)])
    time.sleep(0.5)
    assert sh(baseline.ALIVE).returncode != 0


def test_a_full_lesson_run_keeps_the_pages_n_and_deadline(tmp_path):
    cmd = baseline.lesson_commands(PAGE)[0]                          # --repeat 3 --deadline 2700
    out = baseline.smoke_argv(cmd, profile=tmp_path, pi=tmp_path, runs=tmp_path, stall="120", cap="900",
                              full=True)
    assert out.count("--repeat") == 1 and out[out.index("--repeat") + 1] == "3"
    assert out[out.index("--deadline") + 1] == "2700"
    assert out[out.index("--stall") + 1] == "120"


def test_lessons_takes_full():
    assert baseline.parse_args(["lessons", "--full"]) == ("lessons", {"full": True})
    assert baseline.parse_args(["lessons"]) == ("lessons", {"full": False})


def test_a_lesson_command_never_runs_against_a_dead_tunnel():
    reopened = []
    up = iter([False, True])
    baseline.ensure_serving("http://x/v1", reopen=lambda: reopened.append(1), serving=lambda url: next(up))
    assert reopened == [1]
    baseline.ensure_serving("http://x/v1", reopen=lambda: reopened.append(2), serving=lambda url: True)
    assert reopened == [1]


def test_ensure_serving_gives_up_when_the_reopened_tunnel_still_has_no_model():
    with pytest.raises(baseline.BaselineError, match="no model"):
        baseline.ensure_serving("http://x/v1", reopen=lambda: None, serving=lambda url: False)
