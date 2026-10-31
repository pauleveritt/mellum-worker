=== YOUR APP FAILED THESE ACCEPTANCE CHECKS ===
These are behaviours your application got wrong. Fix the application code (app.py, models.py, templates/) so they pass. Do NOT edit, weaken or delete any test — the harness restores the frozen tests before grading, so changing a test is discarded and wasted effort.

=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/starlette/testclient.py:37
  /Users/codeinfinity/projects/mellum-worker/runs/flow-vllm-20261028T230228Z/20261029T015328Z-flow-hard-fb7c8e/workspace/.venv/lib/python3.13/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

tests/test_app.py: 6 warnings
the acceptance test: 2 warnings
the acceptance test: 1 warning
the acceptance test: 2 warnings
the acceptance test: 6 warnings
  /Users/codeinfinity/projects/mellum-worker/runs/flow-vllm-20261028T230228Z/20261029T015328Z-flow-hard-fb7c8e/workspace/.venv/lib/python3.13/site-packages/starlette/templating.py:161: DeprecationWarning: The `name` is not the first parameter anymore. The first parameter should be the `Request` instance.
  Replace `TemplateResponse(name, {"request": request})` by `TemplateResponse(request, name)`.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED test_archive_complaint_when_resolved - Ass...
FAILED test_audit_trail_records_actions - assert ...
FAILED test_migration_index_exists - AssertionErr...
FAILED test_backfill_resolved_at_migration - Asse...
FAILED test_create_open_tickets_view - AssertionE...
FAILED test_visits_endpoint_aggregates_correctly
FAILED test_add_tickets_note_migration_exists_and_adds_column
7 failed, 21 passed, 18 warnings in 0.47s
