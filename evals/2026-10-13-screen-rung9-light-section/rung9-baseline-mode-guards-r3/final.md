Files changed:
- models.py: Added `status: str = "Open"` field to Complaint class
- app.py: Added `/complaints/{id}/resolve` and `/complaints/{id}/reopen` routes that update status to "Resolved"/"Open" and redirect with 303
- templates/complaints.html: Added status badge and conditional Resolve/Reopen buttons based on status; fixed status check to use "Open"
- tests/test_resolve_reopen.py: Added tests for resolve and reopen functionality

Test output:
```
......                                                                   [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/starlette/testclient.py:37
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-9moewau7/rung9/.venv/lib/python3.14/site-packages/starlette/testclient.py:37: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
.venv/lib/python3.14/site-packages/fastapi/routing.py:233
  /private/var/folders/m4/jc_jynrj6z10mk0t80pkj8l80000gn/T/ladder-9moewau7/rung9/.venv/lib/python3.14/site-packages/fastapi/routing.py:233: DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for removal in Python 3.16; use inspect.iscoroutinefunction() instead
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
6 passed, 6 warnings in 0.78s
```