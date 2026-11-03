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


def _version_binary(tmp_path, name, version):
    p = tmp_path / name
    p.write_text(f'#!/bin/sh\necho {version}\n')
    p.chmod(0o755)
    return p


def test_baseline_resolves_pin_and_fixed_arguments(tmp_path):
    old = _version_binary(tmp_path, 'old-pi', '1.1.0')
    pinned = _version_binary(tmp_path, 'pinned-pi', '1.4.0')
    resolved = baseline.resolve_pinned_pi(harness.CODE.parents[1], candidates=[old, pinned])
    assert resolved['path'] == str(pinned)
    assert resolved['version'] == '1.4.0'
    with pytest.raises(SystemExit, match='1.4.0|install'):
        baseline.resolve_pinned_pi(harness.CODE.parents[1], candidates=[old])
    args = harness.build_parser().parse_args(['baseline','--dry-run'])
    assert args.dry_run
    args = harness.build_parser().parse_args(['baseline','--arm','worker','--reference','saved/batch.json'])
    assert args.arm == 'worker' and args.reference == Path('saved/batch.json')


def _flight_fixture(monkeypatch):
    freeze = json.loads(baseline.FREEZE.read_text())
    raw = harness.CODE.parents[1] / 'runs/2026-11-03-runpod-qualification'
    # Complete HTTP fixture saved by qualification; not a model response oracle.
    props = {'build_info':'b11669-620d2225c','total_slots':2,
        'default_generation_settings':{'n_ctx':50176},'model_alias':freeze['model']['alias'],
        'model_ftype':'Q4_K - Medium',
        'model_path':'/workspace/mellum/cache/'+freeze['model']['file']}
    responses = {'/health':{'status':'ok'}, '/props':props,
        '/v1/models':{'data':[{'id':freeze['model']['alias'],'owned_by':'llamacpp'}]},
        '/slots':[{'id':i,'n_ctx':50176,'is_processing':False} for i in range(2)]}
    monkeypatch.setattr(baseline, 'read_json_url', lambda base, route: responses[route])
    monkeypatch.setattr(baseline, 'verify_remote', lambda config: {
        'gpu':freeze['hardware']['gpu'], 'vram_mib':32623, 'driver':'595.91.07',
        'weight_sha256':freeze['model']['sha256'],
        'runtime_sha256':freeze['backend']['runtime_sha256'],
        'cmdline':baseline.expected_server_argv(config), 'gpu_uuid':'GPU-fixture'})
    monkeypatch.setattr(baseline, 'checker_versions', lambda: {'ruff':'0.14.2','complexipy':'5.1.0','pyrefly':'0.38.0','pytest':'8.4.2'})
    monkeypatch.setattr(baseline, 'resolve_pinned_pi', lambda *a, **k: {
        'path':str(Path(sys.executable)), 'entry_path':str(Path(sys.executable).resolve()), 'version':'1.4.0'})
    return responses


@pytest.mark.parametrize('bad', ['health','omlx','model','build','slots','provenance'])
def test_preflight_rejects_wrong_backend_or_model(monkeypatch, bad):
    responses = _flight_fixture(monkeypatch)
    if bad == 'health': responses['/health'] = {'status':'loading model'}
    if bad == 'omlx': responses['/props'] = {'status':'ok'}
    if bad == 'model': responses['/v1/models']['data'][0]['id'] = 'another-model'
    if bad == 'build': responses['/props']['build_info'] = 'b99999-unknown'
    if bad == 'slots': responses['/slots'][0]['n_ctx'] = 25088
    if bad == 'provenance': monkeypatch.setattr(baseline, 'verify_remote', lambda _: {})
    with pytest.raises(SystemExit, match='backend|identity|model|context|provenance|health|slot'):
        baseline.preflight(Path(sys.executable), PROFILE)


def test_manifest_freezes_shared_inputs(monkeypatch):
    _flight_fixture(monkeypatch)
    flight = baseline.preflight(Path(sys.executable), PROFILE)
    manifest = baseline.create_manifest(harness.CODE.parents[1], flight)
    material = manifest['material']
    assert material['limits'] == {'deadline':600,'stall':180,'target':6,'concurrency':1}
    assert material['pi']['version'] == '1.4.0'
    assert material['backend']['props']['build_info'] == 'b11669-620d2225c'
    assert material['effective_profile']['providers']['llamacpp']['models'][0]['samplingParams']['top_k'] == 20
    assert material['effective_profile']['providers']['llamacpp']['baseUrl'] == 'http://127.0.0.1:8002/v1'
    assert material['checkers']['pytest'] == '8.4.2'
    assert material['hashes']['extensions/mellum-recorder.ts']
    assert any('grader/' in key for key in material['hashes'])


def test_resume_rejects_changed_inputs():
    import copy
    saved = {'material':{'limits':{'deadline':600},'hashes':{'recorder':'a'}},'created_at':'yesterday'}
    current = copy.deepcopy(saved)
    current['created_at'] = 'today'
    baseline.validate_resume(saved, current)
    current['material']['hashes']['recorder'] = 'b'
    with pytest.raises(SystemExit, match='changed|mismatch'):
        baseline.validate_resume(saved, current)


def test_six_counts_failures_and_stalls():
    attempts = []
    for i, completion in enumerate(['settled','stalled','deadline','error','settled','stalled']):
        record = {'completion':completion,'passed':False,'cleanup_ok':True,'requests':2,'provider_error':None}
        state, reason = baseline.classify_attempt(record, identity_ok=True)
        attempts.append({'run_id':str(i),'state':state,'reason':reason})
    assert baseline.counted_attempts(attempts) == 6


def test_infrastructure_stops_and_requires_exclusion_reason():
    record = {'completion':'error','cleanup_ok':True,'requests':1,
              'provider_error':{'classification':'infrastructure'}}
    state, reason = baseline.classify_attempt(record, identity_ok=True)
    attempts = [{'run_id':'r','state':state,'reason':reason}]
    assert state == 'pending-review'
    with pytest.raises(SystemExit, match='reason'):
        baseline.resolve_attempt(attempts, 'r', 'excluded', '')
    baseline.resolve_attempt(attempts, 'r', 'excluded', 'Confirmed HTTP 503 before model work')
    assert baseline.counted_attempts(attempts) == 0
    assert attempts[0]['reason'] == 'Confirmed HTTP 503 before model work'


def test_resume_never_repeats_a_counted_attempt():
    attempts = [{'run_id':'r','state':'counted','reason':'model stall'}]
    with pytest.raises(SystemExit, match='counted|pending'):
        baseline.resolve_attempt(attempts, 'r', 'excluded', 'want another try')
    assert baseline.counted_attempts(attempts) == 1


def test_trace_identity_and_recorder_only_launch(tmp_path):
    pi = {'version':'1.4.0','entry_path':'/pinned/pi.js'}
    launch = {'argv':['/pi','--no-context-files','--no-skills','--no-extensions','-e',str(tmp_path/'record-pi.mjs')],
              'arm':'vanilla','extras':[],'context_files':False}
    (tmp_path/'launch.json').write_text(json.dumps(launch))
    (tmp_path/'trace.jsonl').write_text(json.dumps({'type':'instance_start','runId':tmp_path.name,
        'runtime':{'piVersion':'1.4.0','entryPath':'/pinned/pi.js'}})+'\n')
    assert baseline.verify_trace_identity(tmp_path, pi)
    launch['argv'] += ['-e','worker.ts']
    (tmp_path/'launch.json').write_text(json.dumps(launch))
    assert not baseline.verify_trace_identity(tmp_path, pi)


def test_collector_resumes_without_rerunning_completed_sessions(tmp_path, monkeypatch):
    _flight_fixture(monkeypatch)
    monkeypatch.setattr(harness, 'BASELINE_RUNS', tmp_path / 'runs', raising=False)
    monkeypatch.setattr(harness, 'qualify', lambda _: (True, {'known-good':True,'known-broken':False}))
    calls = []
    def sessions(suite, **kwargs):
        calls.append(kwargs)
        run = harness.new_run(kwargs['runs_dir'], 'easy')
        record = {'completion':'stalled','cleanup_ok':True,'requests':2,'turns':2,
            'provider_error':None,'tests_passed':True,'passed':True,'checks_ran':True,
            'checks_passed':4,'checks_total':4,'code_health':'pass','output_tokens':20,'elapsed_seconds':181}
        (run/'run.json').write_text(json.dumps(record))
        (run/'trace.jsonl').write_text(json.dumps({'type':'instance_start','runId':run.name,
            'runtime':{'piVersion':'1.4.0','entryPath':str(Path(sys.executable).resolve())}})+'\n')
        (run/'launch.json').write_text(json.dumps({'argv':['pi','--no-context-files','--no-skills',
            '--no-extensions','-e',str(run/'record-pi.mjs')], 'arm':'vanilla','extras':[],'context_files':False}))
        return [(run,)]
    monkeypatch.setattr(harness, '_run_sessions', sessions)
    assert harness.collect_baseline() == 0
    batch = next((tmp_path/'runs').glob('vanilla-easy-*'))
    manifest = json.loads((batch/'batch.json').read_text())
    assert len(calls) == 6
    assert all(c['arm']=='vanilla' and c['repeat']==1 and c['grade_run'] and c['stall']==180
               and c['deadline']==600 for c in calls)
    assert baseline.counted_attempts(manifest['attempts']) == 6
    assert '4/4' in (batch/'scorecard.md').read_text()
    assert harness.collect_baseline(resume=batch) == 0
    assert len(calls) == 6


def test_incomplete_attempt_cannot_be_counted_from_a_reason_alone():
    attempts = [{'run_id':'attempt-01','state':'pending-review','reason':'runner killed'}]
    with pytest.raises(SystemExit, match='identity|record|incomplete'):
        baseline.resolve_attempt(attempts, 'attempt-01', 'counted', 'looks okay')
    assert baseline.counted_attempts(attempts) == 0


def _standin_collector(tmp_path, monkeypatch):
    _flight_fixture(monkeypatch)
    monkeypatch.setattr(harness, 'BASELINE_RUNS', tmp_path / 'runs', raising=False)
    monkeypatch.setattr(harness, 'qualify', lambda _: (True, {'known-good':True,'known-broken':False}))
    calls = []
    def sessions(suite, **kwargs):
        calls.append(kwargs)
        run = harness.new_run(kwargs['runs_dir'], 'easy')
        record = {'completion':'stalled','cleanup_ok':True,'requests':2,'turns':2,
            'provider_error':None,'tests_passed':True,'passed':True,'checks_ran':True,
            'checks_passed':4,'checks_total':4,'code_health':'pass','output_tokens':20,'elapsed_seconds':181}
        (run/'run.json').write_text(json.dumps(record))
        (run/'trace.jsonl').write_text(json.dumps({'type':'instance_start','runId':run.name,
            'runtime':{'piVersion':'1.4.0','entryPath':str(Path(sys.executable).resolve())}})+'\n')
        (run/'launch.json').write_text(json.dumps({'argv':['pi','--no-context-files','--no-skills',
            '--no-extensions','-e',str(run/'record-pi.mjs')], 'arm':'vanilla','extras':[],'context_files':False}))
        return [(run,)]
    monkeypatch.setattr(harness, '_run_sessions', sessions)
    return calls


def test_resume_rejects_modified_private_profile(tmp_path, monkeypatch):
    calls = _standin_collector(tmp_path, monkeypatch)
    assert harness.collect_baseline() == 0
    batch = next((tmp_path/'runs').glob('vanilla-easy-*'))
    p = batch/'profile/models.json'
    data = json.loads(p.read_text())
    data['providers']['llamacpp']['models'][0]['samplingParams']['temperature'] = 0
    p.write_text(json.dumps(data))
    with pytest.raises(SystemExit, match='profile|changed'):
        harness.collect_baseline(resume=batch)
    assert len(calls) == 6


def test_resume_discovers_record_written_before_manifest_update(tmp_path, monkeypatch):
    calls = _standin_collector(tmp_path, monkeypatch)
    write = baseline.write_json
    def interrupted(path, data):
        if path.name == 'batch.json' and any(a.get('path') for a in data.get('attempts', [])):
            raise KeyboardInterrupt('simulated crash before manifest commit')
        return write(path, data)
    monkeypatch.setattr(baseline, 'write_json', interrupted)
    with pytest.raises(KeyboardInterrupt):
        harness.collect_baseline()
    batch = next((tmp_path/'runs').glob('vanilla-easy-*'))
    retained = next(batch.glob('attempt-01/*/run.json')).parent.name
    monkeypatch.setattr(baseline, 'write_json', write)
    assert harness.collect_baseline(resume=batch, count=retained,
        reason='retained complete model record and runtime identity verified') == 0
    manifest = json.loads((batch/'batch.json').read_text())
    assert len(calls) == 6
    assert manifest['attempts'][0]['run_id'] == retained
    assert manifest['attempts'][0]['state'] == 'counted'


def _reference(tmp_path, monkeypatch):
    _flight_fixture(monkeypatch)
    flight = baseline.preflight(Path(sys.executable), PROFILE)
    saved = baseline.create_manifest(harness.CODE.parents[1], flight)
    saved.update(status='complete', attempts=[{'state':'counted','run_id':str(i)} for i in range(6)])
    (tmp_path/'batch.json').write_text(json.dumps(saved))
    # Use one real installed file to exercise runtime drift without a Pi install in tests.
    runtime_file = Path(sys.executable).resolve()
    (tmp_path/'native-max-tokens-verification.json').write_text(json.dumps({
        'runtime_sha256':{str(runtime_file):baseline.sha256(runtime_file)}}))
    (tmp_path/'runtime-observations.json').write_text(json.dumps({
        'pi_runtime':{'execPath':str(runtime_file), 'piVersion':'1.4.0','entryPath':str(runtime_file)}}))
    return tmp_path/'batch.json', flight


def test_worker_reference_and_source_provenance(tmp_path, monkeypatch):
    reference, flight = _reference(tmp_path, monkeypatch)
    current = baseline.create_manifest(harness.CODE.parents[1], flight, arm='worker')
    baseline.attach_reference(current, reference)
    m = current['material']
    assert m['arm'] == 'worker'
    assert m['extensions'] == ['extensions/mellum-worker.ts','extensions/mellum-recorder.ts']
    assert m['arm_env'] == {'MELLUM_MODE':'1'}
    assert 'extensions/mellum-commands.ts' in m['worker_hashes']
    assert current['reference']['sha256'] == baseline.sha256(reference)
    baseline.verify_collection_inputs(harness.CODE.parents[1], m)
    m['worker_hashes']['extensions/mellum-commands.ts'] = 'changed'
    with pytest.raises(SystemExit, match='changed|source'):
        baseline.verify_collection_inputs(harness.CODE.parents[1], m)


@pytest.mark.parametrize('bad', ['arm','status','n','suite','profile','recorder','runtime'])
def test_worker_reference_rejects_mismatches(tmp_path, monkeypatch, bad):
    reference, flight = _reference(tmp_path, monkeypatch)
    saved = json.loads(reference.read_text())
    if bad == 'arm': saved['material']['arm'] = 'worker'
    if bad == 'status': saved['status'] = 'partial'
    if bad == 'n': saved['attempts'].pop()
    if bad == 'suite': saved['material']['hashes']['learn/code/suites/easy/task/PROMPT.md'] = 'other'
    if bad == 'profile': saved['material']['profile_settings']['injected'] = True
    if bad == 'recorder': saved['material']['hashes']['extensions/mellum-recorder.ts'] = 'other'
    reference.write_text(json.dumps(saved))
    if bad == 'runtime':
        runtime = json.loads((tmp_path/'native-max-tokens-verification.json').read_text())
        runtime['runtime_sha256'][str(Path(sys.executable).resolve())] = 'other'
        (tmp_path/'native-max-tokens-verification.json').write_text(json.dumps(runtime))
    current = baseline.create_manifest(harness.CODE.parents[1], flight, arm='worker')
    with pytest.raises(SystemExit, match='reference|runtime|shared'):
        baseline.attach_reference(current, reference)


def _worker_identity(run):
    pi = {'version':'1.4.0','entry_path':'/pinned/pi.js'}
    model = {'type':'model_change','provider':'llamacpp','modelId':'Mellum2.1-12B-A2.5B-Thinking'}
    (run/'sessions').mkdir()
    (run/'sessions/session.jsonl').write_text('\n'.join(map(json.dumps,[model,model,
        {'type':'message','message':{'role':'user','content':'task'}}])))
    launch = {'argv':['pi','--no-context-files','--no-skills','--no-extensions',
        '-e',str(harness.EXTENSION),'-e',str(run/'record-pi.mjs')],
        'arm':'worker','extras':[],'context_files':False,'arm_env':{'MELLUM_MODE':'1'},
        'mode_runs_file':str(run/'mellum-mode-runs.jsonl')}
    (run/'launch.json').write_text(json.dumps(launch))
    (run/'trace.jsonl').write_text(json.dumps({'type':'instance_start','runId':run.name,
        'runtime':{'piVersion':'1.4.0','entryPath':'/pinned/pi.js','execPath':'/node'}})+'\n')
    return pi, launch


@pytest.mark.parametrize('bad', [None,'order','inactive','late','env','global-record','runtime','wrong-arm'])
def test_worker_identity_requires_activation_and_exact_launch(tmp_path, bad):
    pi, launch = _worker_identity(tmp_path)
    if bad == 'order': launch['argv'][-3], launch['argv'][-1] = launch['argv'][-1],launch['argv'][-3]
    if bad == 'env': launch['arm_env'] = {}
    if bad == 'global-record': launch['mode_runs_file'] = '/home/records.jsonl'
    if bad == 'inactive':
        p = tmp_path/'sessions/session.jsonl'; p.write_text('\n'.join(p.read_text().splitlines()[1:]))
    if bad == 'late':
        p = tmp_path/'sessions/session.jsonl'; rows=p.read_text().splitlines(); p.write_text('\n'.join([rows[0],rows[2],rows[1]]))
    (tmp_path/'launch.json').write_text(json.dumps(launch))
    assert baseline.verify_trace_identity(tmp_path, pi, arm='vanilla' if bad=='wrong-arm' else 'worker',
        exec_path='/wrong-node' if bad=='runtime' else '/node') is (bad is None)


def test_worker_runner_keeps_mode_records_private(tmp_path):
    binary = tmp_path/'env-pi'
    binary.write_text('#!/bin/sh\nprintf "%s" "$MELLUM_MODE_RUNS" > mode-destination\n')
    binary.chmod(0o755)
    result = harness.run_suite(harness.load_suite(SUITES,'add'), runs_dir=tmp_path/'runs',
        pi_binary=str(binary), profile=PROFILE, arm='worker')
    run = result
    launch = json.loads((run/'launch.json').read_text())
    assert launch['arm_env'] == {'MELLUM_MODE':'1'}
    assert (run/'workspace/mode-destination').read_text() == str(run/'mellum-mode-runs.jsonl')


def test_worker_collector_requires_reference_before_launch(tmp_path, monkeypatch):
    calls = _standin_collector(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match='reference'):
        harness.collect_baseline(arm='worker')
    assert not calls


def test_worker_source_drift_during_last_attempt_cannot_complete_batch(tmp_path, monkeypatch):
    reference_dir = tmp_path/'reference'; reference_dir.mkdir()
    reference, _ = _reference(reference_dir, monkeypatch)
    calls = _standin_collector(tmp_path, monkeypatch)
    sessions = harness._run_sessions
    def worker_sessions(suite, **kwargs):
        results = sessions(suite, **kwargs)
        run = results[0][0]
        _worker_identity(run)
        trace = json.loads((run/'trace.jsonl').read_text())
        trace['runtime'].update(entryPath=str(Path(sys.executable).resolve()),
                                execPath=str(Path(sys.executable).resolve()))
        (run/'trace.jsonl').write_text(json.dumps(trace)+'\n')
        return results
    monkeypatch.setattr(harness, '_run_sessions', worker_sessions)
    digest = baseline.sha256
    def drift(path):
        if len(calls) == 6 and path == harness.EXTENSION:
            return 'modified-during-final-session'
        return digest(path)
    monkeypatch.setattr(baseline, 'sha256', drift)
    with pytest.raises(SystemExit, match='source|changed'):
        harness.collect_baseline(arm='worker', reference=reference)
    batch = next((tmp_path/'runs').glob('worker-easy-*'))
    saved = json.loads((batch/'batch.json').read_text())
    assert saved.get('status') != 'complete'
    assert baseline.counted_attempts(saved['attempts']) == 5
