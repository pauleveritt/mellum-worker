"""Trusted pytest entry point. Invoked by grading.py, never from a submission."""
import json
import os
from pathlib import Path
import sys

import pytest


class Outcomes:
    def __init__(self, mode, app):
        self.mode, self.app = mode, app
        self.collected = []
        self.reports = {}
        self.collection_errors = []
        self.inventory = {}
        self.execution_overrides = []

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collection_finish(self, session):
        # Inspect the final items after submitted collection hooks have finished.
        yield
        self.collected = [item.nodeid for item in session.items]
        for item in session.items:
            name = getattr(item, 'originalname', None) or item.name
            key = item.parent.nodeid + '::' + name
            self.inventory[key] = self.inventory.get(key, 0) + 1
            if self.mode == 'project' and getattr(item.runtest, '__func__', None) is not type(item).runtest:
                self.execution_overrides.append(item.nodeid)
        if self.mode == 'project':
            # Fixture definitions and generated parameters have been registered.
            # Submitted execution/report hooks do not become part of the examiner.
            manager = session.config.pluginmanager
            for plugin in list(manager.get_plugins()):
                filename = getattr(plugin, '__file__', None)
                if filename and Path(filename).resolve().is_relative_to(self.app):
                    manager.unregister(plugin)

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append(str(report.longrepr))

    def pytest_runtest_logreport(self, report):
        self.reports.setdefault(report.nodeid, {})[report.when] = report.outcome


def main():
    mode, app, trusted, destination, *selected = sys.argv[1:]
    app, trusted = Path(app).resolve(), Path(trusted).resolve()
    os.chdir(app)
    # Python starts isolated; pytest itself is already imported from the trusted env.
    sys.path.insert(0, str(app))
    os.environ['UV_PROJECT_ENVIRONMENT'] = sys.prefix
    os.environ['UV_NO_SYNC'] = '1'
    os.environ['PATH'] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')
    hidden = mode not in ('project', 'project-collect', 'required')
    args = ['-q', '-rA', '-p', 'no:cacheprovider', '-c', str(trusted / 'pytest.ini'),
            '--rootdir', str(trusted if hidden else app)]
    if hidden:
        args += ['--noconftest', '--confcutdir', str(trusted), '--import-mode=importlib']
    if mode == 'collect':
        args += ['--collect-only', str(trusted / 'grader_tests')]
    elif hidden:
        args += [str(trusted / selected[0])]
    else:
        args += ['--confcutdir', str(app), 'tests']
        if mode == 'project-collect':
            args += ['--collect-only', '--noconftest']
    plugin = Outcomes(mode, app)
    code = int(pytest.main(args, plugins=[plugin]))
    passed = [node for node, stages in plugin.reports.items()
              if stages.get('call') == 'passed' and all(v == 'passed' for v in stages.values())]
    Path(destination).write_text(json.dumps({
        'exit_code': code, 'collected': plugin.collected, 'reports': plugin.reports,
        'passed': passed, 'collection_errors': plugin.collection_errors,
        'inventory': plugin.inventory,
        'execution_overrides': plugin.execution_overrides,
    }))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
