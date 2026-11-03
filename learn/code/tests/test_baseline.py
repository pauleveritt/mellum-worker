"""Collection ownership, provenance, and accounting regressions."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import baseline
import harness
from test_harness import FIX, PROFILE, SUITES, _observed_pi


def test_live_collection_is_not_reaped(tmp_path):
    with baseline.collection_lock(tmp_path):
        with pytest.raises(SystemExit, match='active|locked'):
            with baseline.collection_lock(tmp_path):
                pass


def test_reused_pid_is_not_trusted(tmp_path):
    run = tmp_path / 'old-run'
    (run / 'workspace').mkdir(parents=True)
    (run / 'owner.json').write_text(json.dumps({
        'owner':{'pid':os.getpid(), 'start':'not-this-process'},
        'workspace':str(run / 'workspace'), 'children':[
            {'pid':os.getpid(), 'start':'not-this-process'}]}))
    with pytest.raises(SystemExit, match='identity|ownership'):
        baseline.reap_stale_runs(tmp_path)
    assert baseline.process_identity(os.getpid()) is not None


def test_sigkill_then_resume_reaps_only_owned_processes(tmp_path):
    root = tmp_path / 'runs'
    root.mkdir()
    binary = _observed_pi(tmp_path, [], sleep=300)
    command = [sys.executable, '-c',
        'import sys; from pathlib import Path; import harness, baseline; '
        'root=Path(sys.argv[1]); '
        'lock=baseline.collection_lock(root); lock.__enter__(); '
        'harness.run_suite(harness.load_suite(Path(sys.argv[2]), "add"), '
        'runs_dir=root, pi_binary=sys.argv[3], profile=Path(sys.argv[4]))',
        str(root), str(SUITES), binary, str(PROFILE)]
    unrelated = subprocess.Popen(['sleep','300'], start_new_session=True)
    runner = subprocess.Popen(command, cwd=harness.CODE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        until = time.monotonic() + 10
        owners = []
        while time.monotonic() < until:
            owners = list(root.glob('*/owner.json'))
            if owners and json.loads(owners[0].read_text()).get('children'):
                break
            if runner.poll() is not None:
                pytest.fail(runner.stderr.read().decode())
            time.sleep(.05)
        assert owners and json.loads(owners[0].read_text())['children']
        runner.kill()
        runner.wait(timeout=10)
        with baseline.collection_lock(root):
            recovered = baseline.reap_stale_runs(root)
        assert len(recovered) == 1
        assert recovered[0]['cleanup_ok'] is True
        assert harness.workspace_members(owners[0].parent / 'workspace') == []
        assert unrelated.poll() is None
        assert (owners[0].parent / 'recovery.json').is_file()
    finally:
        if runner.poll() is None:
            runner.kill()
            runner.wait()
        for workspace in root.glob('*/workspace'):
            harness.sweep_workspace(workspace)
        unrelated.terminate()
        unrelated.wait()


def test_cleanup_failure_stops_before_grading(tmp_path, monkeypatch):
    original = harness.workspace_members
    monkeypatch.setattr(harness, 'workspace_members', lambda _: [(999999999,'unreaped')])
    monkeypatch.setattr(harness, 'sweep_workspace', lambda _: [])
    def forbidden(*args, **kwargs):
        pytest.fail('grading an uncleared workspace')
    monkeypatch.setattr(harness, 'score_details', forbidden)
    monkeypatch.setattr(harness, 'grade', forbidden)
    results = harness._run_sessions(harness.load_suite(SUITES, 'add'),
        runs_dir=tmp_path, pi_binary=str(FIX / 'fake-pi.sh'), repeat=1,
        grade_run=True, deadline=5)
    record = json.loads((results[0][0] / 'run.json').read_text())
    assert record['cleanup_ok'] is False
    assert record['completion'] == 'error'
    assert record['checks_ran'] is False
    assert record['code_health'] == 'not checked'
