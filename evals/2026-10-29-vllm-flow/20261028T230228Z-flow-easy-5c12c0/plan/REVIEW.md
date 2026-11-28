=== YOUR APP FAILED THESE ACCEPTANCE CHECKS ===
These are behaviours your application got wrong. Fix the application code (app.py, models.py, templates/) so they pass. Do NOT edit, weaken or delete any test — the harness restores the frozen tests before grading, so changing a test is discarded and wasted effort.

            object = object.f_code
        if iscode(object):
            return object.co_filename
>       raise TypeError('module, class, method, function, traceback, frame, or '
                        'code object was expected, got {}'.format(
                        type(object).__name__))
E       TypeError: module, class, method, function, traceback, frame, or code object was expected, got FastAPI

../../../../../../.local/share/uv/python/cpython-3.13.16-macos-aarch64-none/lib/python3.13/inspect.py:954: TypeError
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/starlette/testclient.py:37
  /Users/codeinfinity/projects/mellum-worker/runs/flow-vllm-20261028T230228Z/20261028T230228Z-flow-easy-5c12c0/workspace/.venv/lib/python3.13/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

test_home_page_returns_200_and_tagline
test_home_page_layout_contains_expected_elements
  /Users/codeinfinity/projects/mellum-worker/runs/flow-vllm-20261028T230228Z/20261028T230228Z-flow-easy-5c12c0/workspace/.venv/lib/python3.13/site-packages/starlette/templating.py:161: DeprecationWarning: The `name` is not the first parameter anymore. The first parameter should be the `Request` instance.
  Replace `TemplateResponse(name, {"request": request})` by `TemplateResponse(request, name)`.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED test_app_uvicorn_run_reload_flag - TypeErr...
1 failed, 2 passed, 3 warnings in 0.41s
