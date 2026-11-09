"""Select immutable assertion inputs independently of the model's brief."""
from dataclasses import replace
import hashlib
import json

EXECUTION_POLICY = 'trusted-copy-v1'
BUNDLES = {'bc5db20': 'bc5db20', '16cf9f9^': 'pre-single-source', '658bbea5': '658bbea5',
           'f7-roadmap': 'f7-roadmap'}


def select_grader(suite, name='current'):
    if name == 'current':
        if suite.grader_revision != 'current':
            from harness import load_suite
            current = load_suite(suite.root.parent, suite.name)
            return replace(suite, tests=current.tests, expected=current.expected,
                           canary=current.canary, grader_revision='current', grader_base=None)
        return replace(suite, grader_revision='current', grader_base=None)
    if name not in BUNDLES or suite.root is None:
        raise SystemExit(f'unknown grader {name!r} for {suite.name}')
    root = suite.root / 'grader-versions' / BUNDLES[name]
    if not (root / 'revision.json').is_file():
        raise SystemExit(f'unknown grader {name!r} for {suite.name}')
    return replace(suite, tests=root / 'grader',
                   expected=tuple(json.loads((root / 'expected.json').read_text())),
                   grader_revision=name, grader_base=root / 'base')


def grader_identity(suite) -> dict:
    digest = hashlib.sha256()
    paths = [(f'grader/{p.relative_to(suite.tests)}', p) for p in suite.tests.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    base = suite.grader_base or (suite.root / 'base' if suite.root else None)
    if base:
        paths += [(f'base/{name}', base / name) for name in ('pyproject.toml', 'uv.lock')
                  if (base / name).is_file()]
    if base and (base / 'tests').is_dir():
        paths += [(f'base/tests/{p.relative_to(base / "tests")}', p)
                  for p in (base / 'tests').rglob('*.py')]
    if base and (base / 'conftest.py').is_file():
        paths.append(('base/conftest.py', base / 'conftest.py'))
    for name, path in sorted(paths):
        digest.update(name.encode() + b'\0' + path.read_bytes() + b'\0')
    digest.update(json.dumps(suite.expected).encode())
    return {'revision': suite.grader_revision, 'assertion_digest': digest.hexdigest(),
            'execution_policy': EXECUTION_POLICY}
