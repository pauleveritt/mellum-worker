"""Grade disposable application copies using trusted dependencies and structured results.

This boundary prevents project configuration from deciding a hidden grade. It is
not an operating-system sandbox for arbitrary hostile application Python.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

WORKER = Path(__file__).with_name('grading_worker.py')
IGNORED = ('.git', '.venv', '__pycache__', '.pytest_cache', 'grader_tests')
CONFIG = ('pyproject.toml', 'uv.lock', 'uv.toml', '.python-version')


def grade_env(workspace=None):
    """Keep host essentials, excluding interpreter, dependency and pytest overrides."""
    return {k: v for k, v in os.environ.items()
            if not k.startswith(('PYTHON', 'PYTEST', 'UV_'))
            and k not in ('VIRTUAL_ENV', 'CONDA_PREFIX')} | {
                'PYTHONUTF8': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}


def _base(suite):
    return suite.grader_base or (suite.root / 'base' if suite.root else None)


def _application(source, destination, base):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*IGNORED))
    for name in CONFIG:
        target = destination / name
        if target.is_file() or target.is_symlink():
            target.unlink()
        if base and (base / name).is_file() and name in ('pyproject.toml', 'uv.lock'):
            shutil.copyfile(base / name, target)


def _command(trusted, base):
    env = grade_env()
    if base and (base / 'pyproject.toml').is_file():
        for name in ('pyproject.toml', 'uv.lock'):
            if (base / name).is_file():
                shutil.copyfile(base / name, trusted / name)
        digest = hashlib.sha256(b''.join((trusted / name).read_bytes()
            for name in ('pyproject.toml', 'uv.lock') if (trusted / name).is_file())).hexdigest()
        # Shared only by trusted inputs, never the submitted project's virtualenv.
        env['UV_PROJECT_ENVIRONMENT'] = str(Path(tempfile.gettempdir()) / 'mellum-grading-envs' / digest)
        argv = ['uv', '--no-config', 'run', '--project', str(trusted)]
        if (trusted / 'uv.lock').is_file():
            argv += ['--frozen']
        argv += ['--with', 'pytest', '--no-editable']
    else:
        argv = ['uv', '--no-config', 'run', '--no-project', '--with', 'pytest']
    return [*argv, 'python', '-I', str(WORKER)], env


def _run(command, env, mode, app, trusted, destination, node=None):
    argv = [*command, mode, str(app), str(trusted), str(destination)]
    if node:
        argv.append(node)
    try:
        from harness import start_child, kill_tree, sweep_group
        process = start_child(argv, cwd=trusted, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = process.communicate(timeout=120)
            output = stdout + stderr
        finally:
            if process.poll() is None:
                kill_tree(process.pid)
                process.communicate()
            sweep_group(process.pid)
    except subprocess.TimeoutExpired as exc:
        return {'exit_code': -1, 'collected': [], 'reports': {}, 'passed': [],
                'collection_errors': ['grading timed out']}, str(exc)
    if destination.is_file():
        return json.loads(destination.read_text()), output
    return {'exit_code': process.returncode or -1, 'collected': [], 'reports': {},
            'passed': [], 'collection_errors': ['runner did not produce outcomes']}, output


def _prepared_tests(suite, variant):
    """Immutable starter inputs from the brief actually prepared for the worker."""
    base = suite.root / 'base' if suite.root else _base(suite)
    files = {p.relative_to(base).as_posix(): p.read_bytes()
             for p in (base / 'tests').rglob('*.py')} if base and (base / 'tests').is_dir() else {}
    if base and (base / 'conftest.py').is_file():
        files['conftest.py'] = (base / 'conftest.py').read_bytes()
    if variant:
        from harness import load_variant
        overlay = load_variant(suite, variant)
        for path in (overlay / 'tests').rglob('*.py'):
            files[path.relative_to(overlay).as_posix()] = path.read_bytes()
        if (overlay / 'conftest.py').is_file():
            files['conftest.py'] = (overlay / 'conftest.py').read_bytes()
        if (overlay / 'delete.json').is_file():
            for name in json.loads((overlay / 'delete.json').read_text()):
                files.pop(name, None)
    return files


def _project(workspace, suite, root, command, env, trusted, variant):
    base = _base(suite)
    required = _prepared_tests(suite, variant)
    violations = [name for name, content in required.items()
                  if not (workspace / name).is_file() or (workspace / name).read_bytes() != content]
    test_root = workspace / 'tests'
    if not test_root.is_dir():
        return {'passed': not violations, 'integrity_ok': not violations,
                'integrity_violations': violations, 'collected': [], 'reports': {}}, ''
    app = root / 'project'
    _application(workspace, app, base)
    inventory_app = root / 'project-inventory'
    _application(workspace, inventory_app, base)
    inventory, inventory_log = _run(command, env, 'project-collect', inventory_app,
                                    trusted, root / 'project-inventory.json')
    result, output = _run(command, env, 'project', app, trusted, root / 'project.json')
    missing = [key for key, count in inventory.get('inventory', {}).items()
               if result.get('inventory', {}).get(key, 0) < count]
    result['unexecuted_tests'] = missing
    result.update(integrity_ok=not violations, integrity_violations=violations)
    result['passed'] = (not violations and not missing and not result.get('execution_overrides')
                        and inventory['exit_code'] == 0
                        and result['exit_code'] == 0
                        and bool(result['collected'])
                        and set(result['collected']) == set(result['passed']))
    if required:
        # Execute the immutable starter tests once more without submitted hooks.
        # Their own trusted fixtures remain supported; added project tests above
        # still run with the submitted conftests.
        required_app = root / 'required'
        _application(workspace, required_app, base)
        for path in required_app.rglob('conftest.py'):
            path.unlink()
        shutil.rmtree(required_app / 'tests', ignore_errors=True)
        for name, content in required.items():
            target = required_app / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        starter, log = _run(command, env, 'required', required_app, trusted, root / 'required.json')
        starter_ok = (starter['exit_code'] == 0 and bool(starter['collected'])
                      and set(starter['collected']) == set(starter['passed']))
        result['required_passed'] = starter_ok
        result['passed'] &= starter_ok
        output += '\n' + log
    return result, inventory_log + '\n' + output


def evaluate(workspace, suite, *, variant=None) -> dict:
    workspace = Path(workspace).resolve()
    base = _base(suite)
    with tempfile.TemporaryDirectory(prefix='mellum-grade-') as scratch:
        root = Path(scratch)
        trusted = root / 'trusted'
        trusted.mkdir()
        (trusted / 'pytest.ini').write_text('[pytest]\n')
        shutil.copytree(suite.tests, trusted / 'grader_tests', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        command, env = _command(trusted, base)
        collect_app = root / 'collect'
        _application(workspace, collect_app, base)
        collection, output = _run(command, env, 'collect', collect_app, trusted, root / 'collection.json')
        nodes = collection['collected']
        reports, passed = {}, set()
        checks_ran = collection['exit_code'] == 0 and not collection['collection_errors'] and bool(nodes)
        hidden_ok = checks_ran
        if checks_ran:
            for index, node in enumerate(nodes):
                app = root / f'check-{index}'
                _application(workspace, app, base)
                result, log = _run(command, env, 'hidden', app, trusted, root / f'check-{index}.json', node)
                output += '\n' + log
                reports.update(result['reports'])
                passed.update(result['passed'])
                hidden_ok &= result['exit_code'] == 0 and node in result['passed']
                shutil.rmtree(app)
        missing = sorted(set(suite.expected) - passed)
        hidden_ok = bool(hidden_ok and not missing)
        project, log = _project(workspace, suite, root, command, env, trusted, variant)
        output += '\n' + log
        lines = output.strip().splitlines()[-20:]
        if missing:
            lines.append('missing expected tests: ' + ', '.join(missing))
        if not project['integrity_ok']:
            lines.append('required project tests changed/missing: ' + ', '.join(project['integrity_violations']))
        if project.get('unexecuted_tests'):
            lines.append('project tests hidden by collection: ' + ', '.join(project['unexecuted_tests']))
        if project.get('execution_overrides'):
            lines.append('project test execution overridden: ' + ', '.join(project['execution_overrides']))
        return {'passed': hidden_ok and project['passed'], 'hidden_passed': hidden_ok,
                'tail': '\n'.join(lines), 'missing': missing, 'checks_ran': checks_ran,
                'hidden_reports': reports, 'project_tests': project}
