"""Historical assertions are explicit inputs, independently of brief selection."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness


def history():
    assert (harness.CODE / 'grader_history.py').is_file(), 'explicit grader selection is missing'
    return importlib.import_module('grader_history')


@pytest.mark.parametrize('name', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('revision', ['bc5db20', '16cf9f9^'])
def test_retained_bundle_matches_git_bytes(name, revision):
    selected = history().select_grader(harness.load_suite(harness.SUITES, name), revision)
    prefix = f'learn/code/suites/{name}/'
    paths = subprocess.check_output(['git', '-C', str(harness.CODE.parents[1]), 'ls-tree', '-r', '--name-only', revision, prefix], text=True).splitlines()
    assert paths, 'historical bundle source was not found'
    for path in paths:
        rel = path.removeprefix(prefix)
        if rel.startswith(('grader/', 'base/tests/')) or rel in ('expected.json', 'base/pyproject.toml', 'base/uv.lock'):
            saved = selected.tests.parent / rel
            assert saved.is_file(), f'missing historical input: {rel}'
            assert saved.read_bytes() == subprocess.check_output(['git', 'show', f'{revision}:{path}'])
    identity = history().grader_identity(selected)
    assert identity['revision'] == revision
    assert len(identity['assertion_digest']) == 64
    assert identity['execution_policy'] == 'trusted-copy-v1'


def test_unknown_bundle_cannot_fall_back_to_current():
    with pytest.raises(SystemExit, match='unknown grader'):
        history().select_grader(harness.load_suite(harness.SUITES, 'easy'), '../unknown')


def test_original_briefs_match_recorded_byte_manifest():
    history()
    manifest = json.loads((harness.CODE.parents[1] / 'docs/superpowers/research/2026-11-07-suite-oracle-audit/original-bytes.json').read_text())
    assert len(manifest) == 25
    for path, digest in manifest.items():
        assert hashlib.sha256((harness.CODE.parents[1] / path).read_bytes()).hexdigest() == digest


def test_cli_selects_grader_separately_from_specs():
    history()
    args = harness.build_parser().parse_args(['run', '--suite', 'easy', '--specs', 'original', '--grader', 'bc5db20'])
    assert (args.specs, args.grader) == ('original', 'bc5db20')
    assert harness.build_parser().parse_args(['qualify', '--suite', 'easy', '--grader', '16cf9f9^']).grader == '16cf9f9^'


def test_historical_timestamp_assertion_differs_from_current(tmp_path):
    module = history()
    suite = harness.load_suite(harness.SUITES, 'medium')
    shutil.copytree(suite.root / 'base', tmp_path, dirs_exist_ok=True)
    shutil.copytree(suite.root / 'fixtures/known-good', tmp_path, dirs_exist_ok=True)
    models = tmp_path / 'models.py'
    text = models.read_text().replace('timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))', 'timestamp: datetime = None')
    text = text.replace('\n\ncomplaints:', '\n\n    def __post_init__(self):\n        if self.timestamp is None:\n            self.timestamp = datetime.now(timezone.utc)\n\n\ncomplaints:')
    models.write_text(text)
    old = module.select_grader(suite, '16cf9f9^')
    recent = module.select_grader(suite, 'bc5db20')
    assert harness.score_workspace(tmp_path, recent)[0]
    assert not harness.score_workspace(tmp_path, old)[0]


def test_selecting_current_after_history_restores_current_inputs():
    module = history()
    current = harness.load_suite(harness.SUITES, 'medium')
    old = module.select_grader(current, '16cf9f9^')
    restored = module.select_grader(old, 'current')
    assert restored.tests == current.tests
    assert restored.expected == current.expected
    assert module.grader_identity(restored) == module.grader_identity(current)
