Files changed:
- models.py
- app.py
- templates/complaints.html

 Test output:
============================= test session starts ==============================
 platform darwin -- Python 3.14.2, pytest-8.3.4, pluggy-1.6.0 -- /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-atc5hurp/rung9/.venv/bin/python
 cachedir: .pytest_cache
 rootdir: /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-atc5hurp/rung9
 configfile: pyproject.toml
 plugins: anyio-4.15.0
 collecting ... collected 4 items

 tests/test_add.py::test_post_redirects_to_board PASSED                   [ 25%]
 tests/test_add.py::test_new_complaint_is_listed PASSED                   [ 50%]
 tests/test_app.py::test_home_page PASSED                                 [ 75%]
 tests/test_board.py::test_board_lists_complaints PASSED                  [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-atc5hurp/rung9/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/ng/s__btvhd6q703hr6m9rl931h0000gn/T/ladder-atc5hurp/rung9/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 4 passed, 4 warnings in 0.24s =========================
</tool_call>