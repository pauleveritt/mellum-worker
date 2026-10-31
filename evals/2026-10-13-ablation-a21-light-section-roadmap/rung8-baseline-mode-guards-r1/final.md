Tests passed successfully.

Files changed:
- `app.py`: Added RedirectResponse handling for POST /complaints
- `templates/complaints.html`: Added form for submitting new complaints
- `tests/test_app.py`: Updated test_add_complaint to use follow_redirects=False

Test output:
```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-8.3.4, pluggy-1.6.0 -- /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-yfyadscz/rung8/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-yfyadscz/rung8
configfile: pyproject.toml
plugins: anyio-4.15.0
collecting ... collected 3 items

tests/test_app.py::test_home_page PASSED                                 [ 33%]
tests/test_app.py::test_add_complaint PASSED                             [ 66%]
tests/test_board.py::test_board_lists_complaints PASSED                  [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-yfyadscz/rung8/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-yfyadscz/rung8/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 3 passed, 4 warnings in 0.37s =========================
```