# py-features: does the model know its Python?

Each task is a small project pinned to one Python version (`.python-version` and `requires-python`). The
prompt describes behaviour and never names the version or the feature, so the model has to find out which
Python the project uses and choose the idiom that fits it. Every task is a harness suite; run one with
`harness.py run --suites-dir suites/py-features --suite <task>`.

## Three kinds of task

| Kind | Project pinned to | Passes only if the model... |
|---|---|---|
| `new-api` | the feature's version | uses the new feature (a workaround fails the hidden tests) |
| `trap` | the version before the feature | does NOT use it (the new feature crashes there) |
| `fix` | the version that broke the code | diagnoses and fixes what that version changed |

A trap's name says both versions: `py3.14-sentinel-of-3.15` is pinned to 3.14 and tempts a 3.15 feature.

## Every task is proved before any model run

`uv run --no-project python py_features.py check` runs each task's fixtures through its hidden tests:

- `fixtures/reference/` passes on the pinned Python;
- `fixtures/workaround/` (the plausible wrong answer) and the untouched `base/` fail there;
- for `new-api`, the reference also fails on the Python before, so the task really needs the feature.

A task that fails any direction measures nothing, and `check` exits non-zero.

## Adding a new Python release

Nothing in the tooling names a version: the version before is worked out from `task.json` (3.17 -> 3.16).
For a release such as 3.16:

```bash
uv python install 3.16
uv run --no-project python py_features.py new <name> --python 3.16 --kind new-api --pep "PEP ..."
uv run --no-project python py_features.py new <name> --python 3.16 --kind trap --pep "PEP ..."
```

Then fill in the scaffold: `base/` (the starting project), `prompts/01.md` (behaviour only, no version or
feature name), `grader/test_*.py` (hidden tests), `fixtures/reference/`, `fixtures/workaround/`, and
`expected.json` (every hidden test id, as `grader_tests/<file>::<test>`). Run `check` until it passes.
A major release (4.0) has no rule for "the version before": set `"predecessor"` in its `task.json`.

Take features from the official "What's New in Python 3.x" page and confirm each on the real interpreter
before writing a task: memory of a release that is not out yet is not evidence.

## Tasks

| Task | Kind | Feature |
|---|---|---|
| py3.14-tstring-sql | new-api | template strings, `string.templatelib` (PEP 750) |
| py3.14-annotations-forward | new-api | deferred annotations, `annotationlib` (PEP 649/749) |
| py3.14-zstd-archive | new-api | `compression.zstd` (PEP 784) |
| py3.14-finally-fix | fix | `return` in `finally` is a SyntaxError (PEP 765) |
| py3.15-sentinel-default | new-api | built-in `sentinel()` (PEP 661) |
| py3.15-frozendict-config | new-api | built-in `frozendict` (PEP 814) |
| py3.15-lazy-import | new-api | `lazy import` (PEP 810) |
| py3.15-typeddict-closed | new-api | closed and `extra_items` TypedDicts (PEP 728) |
| py3.14-sentinel-of-3.15 | trap | built-in `sentinel()` is not available yet |
| py3.14-frozen-config-of-3.15 | trap | built-in `frozendict` is not available yet |
